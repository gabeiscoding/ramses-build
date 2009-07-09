
def findVarsInString(code,varDict):
    """
    returns a dict that is a subset of varDict and contains the
    variables that are being used in code. The format of the variables
    are $var or ${var}
    """
    badVarChars = [' ', '\n',';','"',"'","/"] #end a $var search
    inVar = False
    withSquig = False
    varName = ''
    newVarDict = {}
    for i in range(len(code)):
        if code[i] == '$':
            #check if the $ is escaped (and not a preceeding excapped \)
            if(i > 0):
                if code[i-1] == "\\":
                    if(i > 1) and code[i-2] == "\\":
                        pass #Just an excapped \, nothing to freak about
                    else:
                        continue # one \ means escapped $
            
            #check if the var is "private"
            if(i+1 < len(code)):
                if code[i+1] == '_':
                    continue
            
            if inVar:
                newVarDict[varName] = varDict[varName]
            inVar = True
            withSquig = False
            if(i+1 < len(code)):
                if code[i+1] == '{':
                    withSquig = True
            varName = ''
            continue

        #termination of var if no {}
        if code[i] in badVarChars and inVar and not withSquig:
            newVarDict[varName] = varDict[varName]
            inVar = False

        #termination of varw with {}
        if code[i] == '}' and inVar and withSquig:
            newVarDict[varName] = varDict[varName]
            inVar = False

        if inVar and not (withSquig and code[i] == '{'):
            varName += code[i]

    #termination of var with EOS
    if inVar and not withSquig: 
        newVarDict[varName] = varDict[varName]
        
    return newVarDict

def _defaultPrinter(text,type,returns):
    if returns:
        print text
    else:
        print text,

printer = _defaultPrinter

def printf(text,type=1,returns=True):
    """
    calls the printer for displaying output of runs.
    type:
    1: program information messages
    2: stdout from script running
    3: stderr from script running
    """
    global printer
    printer(text,type,returns)

def toMinutes(seconds):
     if seconds > 60:
         min = int(seconds)/60
         sec = int(seconds)%60
         return "%d minutes, %d seconds"%(min,sec)
     else:
         sec = int(seconds)
         return "%d seconds"%sec
     
