import struct, sys, getpass, os, string, thread, threading
import time

from sshclient import *
from twisted.python import threadable
from twisted.internet import threads
threadable.init( with_threads=1)

import utils


class RunError(Exception):
    pass

class SshRunner:
    def __init__(self,systemDict,props, dry_run = False):
        self.props = props
        self.dry_run = dry_run
        self.host = systemDict["hostname"]
        self.baseDir = systemDict['base_dir']
        self.loginName = systemDict['login_name']
        self.passwd = systemDict.get('password',None)
        self.rcScript = systemDict.get('rc',None)
        self.port = int(systemDict.get('port',22))
        self.sys_exports = systemDict.get('exports',[])
        self.connHealthy = True

        self.ssh_done = threading.Event()

        #Our factory builds a SimpleTransport which gets passed this
        #instance, sets self.ssh_done and self.ssh to itself. A little
        #wierd, but Conch is weird like that.
        factory = SimpleFactory(self.loginName, self.passwd, self.host, self)
        d = threads.deferToThread(reactor.connectTCP, self.host, self.port, factory)
        d.addCallback(self._cbDeferred)
        d.addErrback(self._cbErr)

        self.ssh_done.wait() #wait till the ssh connection initializes
        self.ssh_done.clear()

        if not self.connHealthy or not self.ssh.healthy:
            raise RunError("SSH connection failed.")

        utils.printf('Successfully connected to %s'%self.host)
        if self.rcScript:
            out,err,status = self.execCmd(self.rcScript)


    def _cbDeferred(self,d):
        pass

    def _cbErr(self, error):
        #print dir(error)
        utils.printf("Host %s: %s"%(self.host, error.getErrorMessage()))
        self.connHealthy = False
        self.ssh_done.set()
        
    def _cbDisplayStdout(self,data):
        utils.printf(data,2,False)

    def _cbDisplayStderr(self,data):
        utils.printf(data,3,False)

    def assertExists(self,entity_to_check):
        commandSetup = self._getCmdSetup(entity_to_check)
        out,err,status = self.execCmd(commandSetup + "ls " + entity_to_check,displayOutput=False)
        if status != 0:
            utils.printf(err,3,False)
            return False
        #OSX returns 0 even on a ls error, so check for the error message as well
        if len(err) > 3 and err.startswith('ls:'):
            utils.printf(err,3,False)
            return False
        print 'SUCESSFULL ASSERT'
        return True

    def processPreAsserts(self,preAsserts):
        if len(preAsserts) > 0:
            utils.printf("Checking pre-assertions that files exist...")
        wasSuccessfull = True
        for entity in preAsserts:
            wasSuccessfull &= self.assertExists(entity)
            
        if wasSuccessfull:
            utils.printf("Check passed")                        
        return wasSuccessfull

    def run(self,scriptCode):
        """
        Each script line gets its own ssh channel, thus it needs to be
        given the right enviornment. So the code is analyzed to see
        which environment variables need to be set. Also, the base
        directory is entered before executing the command.
        """
        checkStatus = True
        for line in scriptCode.splitlines():
            if line.lstrip() == '':
                continue
            line = line.lstrip()
            
            if line.startswith('PRINT'):
                utils.printf(line[5:].lstrip())
                
            elif line.startswith('ASSERT_EXISTS'):
                #this makes sure that a file or directory exists on the system
                entity_to_check = line[13:].lstrip()
                if not self.dry_run and not self.assertExists(entity_to_check):
                    return False
                
                #Otherwise the assert passed, so continue
                utils.printf("ASSERTION PASSED: " + entity_to_check)
                
            elif line.startswith('PRE_ASSERT_EXISTS'):
                #preasserts should be done before running of script blocks
                pass
            elif line.startswith('EXPECT_TO_FAIL'):
                #This section is not guranteed to get a valid status returned, thus we need to disable checking
                checkStatus = False
            else:
                #regular shell command, setup and run
                commandSetup = self._getCmdSetup(line)
                #unescape any excaped $ characters
                #line = line.replace("!$","$")
                
                echoText = ''
                if True: #may want this off sometime
                    echoText = 'echo "' + line.replace('"','\\"') + '"\n'
                cmd = commandSetup + echoText + line
                if self.dry_run:
                    cmd = commandSetup + echoText
                out,err,status = self.execCmd(cmd)

                #bail out if we failed
                if checkStatus and status != 0:
                    return False
                       
        return True
    
    def execCmd(self,command,displayOutput=True):
        if displayOutput:
            reactor.callFromThread(self.ssh.conn.runCommand,command,self._cbDisplayStdout,self._cbDisplayStderr)
        else:
            reactor.callFromThread(self.ssh.conn.runCommand,command)
        
        self.ssh_done.wait() #wait till the ssh connection initializes
        self.ssh_done.clear()
        (out,err,exit_status) = self.ssh.results
        #utils.printf("status: %s" % exit_status)
        return self.ssh.results

    def _getCmdSetup(self,code):
        varDict = utils.findVarsInString(code,self.props)
        exportCommands = []
        for export in self.sys_exports:
            exportCommands.append('export ' + export)
        for name in varDict.keys():
            if(type(varDict[name]) == str or type(varDict[name]) == int):
                exportCommands.append('export ' + name + '="' + str(varDict[name]) + '"')

        exportCommands = string.join(exportCommands,"\n")
        dirChange = "\ncd " + self.baseDir + "\n"
        
        return exportCommands + dirChange

class LocalRunner:
    #ToDo: this could start up a bash process in a separate thread and
    #communicate to stdin/stdout/stderr through pipes.
    pass

class ContextHolder:
    def __init__(self):
        self.runners = {}
        
        self.reactor_facade = ReactorFacade()
        self.startedReactor = False
       
    def getSystemRunner(self, systemDict,props, dry_run = False):
        if not self.startedReactor:
            #start the twisted event loop that handles all SSH network traffic
            self.reactor_facade.start()
            self.startedReactor = True
            
        #In the future, do logic to see if current host is desired and
        #return a LocalRunner
        runner = None
        if systemDict["hostname"] in self.runners:
            runner = self.runners[systemDict["hostname"]]
        else:
            runner = SshRunner(systemDict,props, dry_run)
            self.runners[systemDict["hostname"]] = runner
        return runner

                                  
