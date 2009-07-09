import warnings
warnings.simplefilter("ignore", DeprecationWarning)
from config import Config
from optparse import OptionParser
from context import ContextHolder, RunError
from datetime import datetime
import sys
import re
import socket
import utils

#ToDo:
# * Make MAX_PY_PROP_LEVEL a command line switch as well?
# * Make a argument to echo or not echo the commands
# * Make a arg to be silent? or turn-off stdout from remote
# * Does EXPECT_TO_FAIL really work?
#Increment version number when signficant changes occur
VERSION = 1.0

hostname = socket.gethostname()
MAX_PY_PROP_LEVEL = 3
contextHolder = ContextHolder()

class Usage(Exception):
    pass

class ParseError(Exception):
    pass

def condSelect(condition, dictSelectOptions):
    """
    This is called by the configuration files to selection one of a
    dictionaries keys based on the condition passed in.
    """
    return dictSelectOptions[condition]

def boolSelect(boolVal, trueOption, falseOption):
    """
    This is called by the configuration files to select one of the two
    options based on the value of boolVal
    """
    if type(boolVal) is bool:
        if boolVal:
            return trueOption
        else:
            return falseOption

    if type(boolVal) is str:
        if boolVal.startswith('T') or boolVal.startswith('t'):
            return trueOption
        elif boolVal == '1':
            return trueOption
        else:
            return falseOption

    #don't know what to do with boolVal
    raise ParseError('Not sure what how to treat "' + str(boolVal) + '" as a boolean')

def parseScriptFile(fname, miniScripts):
    script = open(fname,'r')
    contents = script.read()
    script.close()
    
    p = re.compile(r'^#.*?$',re.MULTILINE)
    contents = p.sub('',contents)
    
    p = re.compile(r'(^\[.+?\].+?)',re.MULTILINE | re.DOTALL)
    sections = p.split(contents)
    
    name,body = None,None
    gettingName = True
    for section in sections:
        if section.startswith('\n'):
            continue
        if gettingName:
            m = re.search('\[(.+?)\].*',section)
            if m is None:
                raise ParseError("Error breaking up script file into sections, make sure there is no space between section headers and code")
            name = m.groups()[0]
            gettingName = False
        else:
            body = section
            miniScripts[name] = body
            gettingName = True
    return miniScripts

def parsePropertyFile(fname, cfg):
    try:
        cfg.load(file(fname))
        for name in cfg.keys():
            cfg[name] #make sure all keys resolve
    except Exception, e:
        utils.printf("%s: %s" % (fname, e))
        raise ParseError("Fix your input files")

    return cfg

def evaluatePythonProperties(props_toeval, props):
    for level in range(1,MAX_PY_PROP_LEVEL+1):
        python_prefix = '!py:'
        if level > 1:
            python_prefix = '!py' + str(level) + ':'
        for name in props_toeval.keys():
            if(type(props_toeval[name]) == str):
                if props_toeval[name].startswith(python_prefix):
                    toEvalStripped = props_toeval[name][len(python_prefix):].lstrip() #splice out first four caracters and whitespace
                    toEval = "props_toeval[name] = " + toEvalStripped
                    try:
                        eval(compile(toEval,"python property expression","single"))
                    except Exception, e:
                        utils.printf("Error compiling property %s: %s" % (name,toEvalStripped))
                        raise e
                
def evaluatePythonBoolean(cond,props):
    toEval = "retVal = bool(" + cond.lstrip() + ")" #strip whitespace and save value
    eval(compile(toEval,"python conditional expression","single"))
    if not 'retVal' in locals():
        raise ParseError("Failed to evaluate condition '%s'"%cond)
    return locals()['retVal']

def runBuild(build, options):
    dry_run = bool(options.dry_run)
    build.miniScripts = {}
    for script in build.scripts:
        build.miniScripts = parseScriptFile(script, build.miniScripts)
    #verify that all steps exist in our parsed task
    for step in build.steps:
        if step.name not in build.miniScripts:
            raise ParseError("The %s step was not found in any of the script files provided"
                             %step.name)

    #parse property files
    build.props = Config()
    for propFile in build.properties:
        build.props = parsePropertyFile(propFile, build.props)

    run_with_each = [{}] #List of one empty dict default
    if 'run_with_each' in build:
        run_with_each = build.run_with_each

    for run in run_with_each:
        #Extra properties to add for each build
        for key in run.keys():
            build.props[key] = run[key]
        evaluatePythonProperties(build.props, build.props)
        evaluatePythonProperties(build, build.props)

        preAsserts = []

        #run through steps and verify that properties used in the scripts are valid.
        for step in build.steps:
            #check syntax of conditions
            taskWillBeDone = True
            if 'conditions' in step:
                for cond in step['conditions']:
                    taskWillBeDone &= evaluatePythonBoolean(cond,build.props)

            #check syntax of host specification
            if 'host' in step:
                if step['host'].startswith('props.'):
                    host_prop = step['host'][6:]
                    if not host_prop in build.props:
                        raise ParseError("Step %s specifies a host of %s, but it was not found in the properites"%
                                     (step.name,host_prop))
                else:
                    if not 'hosts' in build.props:
                        raise ParseError("Step %s specifies a host, but there is no hosts dictionary property"%step.name)
                    if not step['host'] in build.props['hosts']:
                        raise ParseError("Step %s specifies a host of %s, but it was not found in the hosts dict"%
                                         (step.name,step.host))

            #check syntax of miniScript and variables
            try:
                utils.findVarsInString(build.miniScripts[step.name], build.props)
            except AttributeError, key:
                utils.printf('The script code in [%s] used a undefined property "%s"'%(step.name,key))
                valid_props = [name for name in build.props.keys() if type(name) is str or type(name) is int]
                valid_props.sort()
                utils.printf('\nValid property names follow: %s'%repr(valid_props))
                return

            #if there are any PRE_ASSERT_EXISTS in the miniScript, grab them for queinging
            if taskWillBeDone:
                for line in build.miniScripts[step.name].splitlines():
                    if line.lstrip().startswith('PRE_ASSERT_EXISTS'):
                        preAsserts.append(line.lstrip()[17:].lstrip())

        #Now run the steps
        global contexHolder
        defaultRunner = contextHolder.getSystemRunner(build.default_host,build.props, dry_run)

        if not defaultRunner.processPreAsserts(preAsserts):
            utils.printf('\nPreasserts failed, exiting build process...')
            return

        for step in build.steps:
            #perform condition check
            if 'conditions' in step:
                doTask = True
                for cond in step['conditions']:
                    doTask &= evaluatePythonBoolean(cond,build.props)
                if not doTask:
                    continue
            runner = defaultRunner
            runHostname = build.default_host.hostname

            if 'host' in step: #running on host other than default_host
                host_dict = None
                if step['host'].startswith('props.'):
                    host_prop = step['host'][6:]
                    host_dict = build.props[host_prop]
                else:
                    host_dict = build.props['hosts'][step['host']]
                runner = contextHolder.getSystemRunner(host_dict, build.props, dry_run)
                runHostname = host_dict.hostname

            utils.printf('\n[%s] on %s'%(step.name, runHostname))
            success = runner.run(build.miniScripts[step.name])
            if not success:
                utils.printf('\nPrevious task failed, exiting build process...')
                return
        
    utils.printf("Build finished successfully")
    
def parseBuildFile(fname):
    try:
        cfg = Config(fname)
        for name in cfg.keys():
            cfg[name] #make sure all keys resolve
        #validate that script files exist
        for scriptFile in cfg.scripts:
            f = open(scriptFile,'r')
            f.close()
        #validate that properity files exist
        for propFile in cfg.properties:
            f = open(propFile,'r')
            f.close()
    except Exception, e:
        print "%s: %s" % (fname, e)
        raise ParseError("Fix your input files")

    return cfg

def main(args=None):
    rv = 0
    if args is None:
        args = sys.argv[1:]
    parser = OptionParser(usage="usage: %prog [-d --dry-run] DES-FILE", version="%prog "+str(VERSION))
    parser.add_option("-d", "--dry-run", dest="dry_run", action="store_const", const=True, help="Do not execute any commands, just display the commands that would be executed")

    (options, args) = parser.parse_args(args)
    try:
        if len(args) == 0:
            raise Usage("No .des file specified")
        from time import time
        t1 = time()
        stepsData = parseBuildFile(args[0])
        runBuild(stepsData, options)
        t2 = time()
        print "Build time:",utils.toMinutes(t2-t1)
    except Usage, e:
        parser.print_help()
        print "\n%s: %s" % (parser.get_prog_name(), e)
        rv = 1
    except ParseError, e:
        print "%s: Parase Error: %s" % (parser.get_prog_name(), e)
        rv = 1
    except RunError, e:
        print "%s: Run Error: %s" % (parser.get_prog_name(), e)
        rv = 3
    except Exception, e:
        print "\n%s: error: %s" % (parser.get_prog_name(), e)
        typ, val, tb = sys.exc_info()
        import traceback
        traceback.print_tb(tb)
        rv = 2
    global contextHolder

    if contextHolder and contextHolder.startedReactor:
        contextHolder.reactor_facade.stop()

    return rv
        

if __name__ == "__main__":
    sys.exit(main())
