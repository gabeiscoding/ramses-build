import struct, sys, getpass, os, string, thread, threading
from twisted.conch.ssh import transport, userauth, connection, common, keys, channel, session
from twisted.internet import defer, protocol, reactor
from twisted.python import log

def getRSAKeys():
    print "Generating RSA keypair..."
    from Crypto.PublicKey import RSA
    KEY_LENGTH = 1024
    rsaKey = RSA.generate(KEY_LENGTH, common.entropy.get_bytes)
    publicKeyString = keys.makePublicKeyString(rsaKey)
    privateKeyString = keys.makePrivateKeyString(rsaKey)
    return publicKeyString, privateKeyString

class ReactorFacade:

	def __init__( self ):
		self.reactorThread = threading.Thread(
			target=reactor.run,
			name="ReactorThread",
			kwargs={'installSignalHandlers':0},
			)

	def start(self):
		# assume not yet started
		self.reactorThread.start()
		print "Ssh engine started"

	def stop(self):
		# assume already running
		reactor.callFromThread(reactor.stop)
		print "Ssh engine stopped"
		self.reactorThread.join()

class SimpleTransport(transport.SSHClientTransport):
    def __init__(self, user, passwd, host, context):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.healthy = True
        self.context = context
        context.ssh = self

    def verifyHostKey(self, hostKey, fingerprint):
        #print 'host key fingerprint: %s' % fingerprint
        return defer.succeed(1)

    def connectionSecure(self):
        self.conn = SimpleConnection()
        self.requestService(
            SimpleUserAuth(self.user,self.passwd,self.conn))

    def connectionLost(self, reason):
        if hasattr(self,'context'):
            self.healthy = False
            self.context.ssh_done.set()
        transport.SSHClientTransport.connectionLost(self,reason)

class SimpleFactory(protocol.ClientFactory):
    def __init__(self, user, passwd, host, context):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.context = context
        #Might expand key based authentication in the future
        #pubKeyString, privKeyString = getRSAKeys()
        #self.publicKeys = { 'ssh-rsa': keys.getPublicKeyString(data=pubKeyString)}
        #self.privateKeys = { 'ssh-rsa' : keys.getPrivateKeyObject(data=privKeyString)}

    def buildProtocol(self, addr):
        protocol = SimpleTransport(self.user, self.passwd, self.host, self.context)
        return protocol        

class SimpleUserAuth(userauth.SSHUserAuthClient):

    def __init__(self, user, passwd, instance):
        self.user = user
        self.passwd = passwd
        userauth.SSHUserAuthClient.__init__(self, user, instance)
        self.instance = instance

    def getPassword(self):
        if self.passwd:
            return defer.succeed(self.passwd)
        else:            
            return defer.succeed(getpass.getpass("%s@%s's password: " % (self.user,self.transport.host)))

    def getGenericAnswers(self, name, instruction, questions):
        print name
        print instruction
        answers = []
        for prompt, echo in questions:
            if echo:
                answer = raw_input(prompt)
            else:
                answer = getpass.getpass(prompt)
            answers.append(answer)
        return defer.succeed(answers)
            
    def getPublicKey(self):
        path = os.path.expanduser('~/.ssh/id_dsa') 
        # this works with rsa too
        # just change the name here and in getPrivateKey
        if not os.path.exists(path) or self.lastPublicKey:
            # the file doesn't exist, or we've tried a public key
            return
        return keys.getPublicKeyString(path+'.pub')
        

    def getPrivateKey(self):
        path = os.path.expanduser('~/.ssh/id_dsa')
        return defer.succeed(keys.getPrivateKeyObject(path))

class SimpleConnection(connection.SSHConnection):
    def serviceStarted(self):
        self.transport.context.ssh_done.set() #Say we are done initialzing the connection

    def runCommand(self, command, cbDisplayOut=None, cbDisplayErr=None):
        self.transport.results = (None,None)
        channel = CommandChannel(2**16, 2**15, self)
        channel.command = command
        channel.cbDisplayOut = cbDisplayOut
        channel.cbDisplayErr = cbDisplayErr
        channel.transport = self.transport
        self.openChannel(channel)

class CommandChannel(channel.SSHChannel):
    name = 'session'

    def openFailed(self, reason):
        error = 'Failed to open command channel, %s'%reason
        if self.cbDisplayErr:
            self.cbDisplayErr(error)
        else:
            print error
        self.transport.context.ssh_done.set() #we are done with the command

    def channelOpen(self, ignoredData):
        self.out = ''
        self.err = ''
        self.conn.sendRequest(self, 'exec', common.NS(self.command), wantReply = 1)

    def dataReceived(self, data):
        self.out += data
        if self.cbDisplayOut:
            self.cbDisplayOut(data)

    def extReceived(self, dataType, data):
        """
        This is usually where stderr comes in, thus you could change
        the callback if you wanted to display stderr differently
        """
        self.err += data
        if self.cbDisplayErr:
            self.cbDisplayErr(data)

    def request_exit_status(self, data):
        status = struct.unpack('>L', data)[0]
        self.exit_status = status
        self.loseConnection()
        
    def closed(self):
        self.transport.results = (self.out,self.err,self.exit_status)
        self.transport.context.ssh_done.set() #we are done with the command

#Uncomment this if you want very verbose output
#log.startLogging(sys.stdout)
