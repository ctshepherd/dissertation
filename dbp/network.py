"""Network module.

Network module, mainly contains the TXNetwork class, which handles all network traffic for the DBP.
"""

from twisted.protocols.basic import NetstringReceiver
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from ast import literal_eval


class TXTaken(Exception):
    """Raised when we try to reserve a TX but it was taken by someone else."""


class TXFailed(Exception):
    """Raised when we have exceeded number of attempts to try to reserve a TX."""


class TXDistributeProtocol(NetstringReceiver):

    VERSION = 1

    def sendCommand(self, command, content=None):
        if content is None:
            self.sendString(command)
        else:
            self.sendString("%s:%s" % (command, content))

    def connectionMade(self):
        self.version_check = True
        self.factory.client = self
        self.sendCommand("VERSION", self.VERSION)

    def stringReceived(self, s):
        if ':' in s:
            command, content = s.split(':', 1)
        else:
            command = s
            content = ""
        if command == "VERSION":
            self.check_version(content)
        elif command == "SEND":
            self.receive_tx(content)
        elif command == "QUIT":
            self.transport.loseConnection()

    def check_version(self, s):
        if not self.version_check:
            return
        ver = int(s)
        if ver != self.VERSION:
            self.quit()
        self.version_check = False

    def receive_tx(self, content):
        tx_id, tx_op = content.split("|")
        tx_id = int(tx_id)
        # XXX: This should be changed to some kinda serialize/deserialize
        # method in dbp.db
        tx_op = literal_eval(tx_op)
        tx_op = tx_op[0] + "=" + tx_op[1]
        self.factory.tx_received((tx_id, tx_op))

    # def request_tx(self, tx_id):
    #     self.sendCommand("REQ", "%s" % tx_id)

    def distribute(self, (tx_id, tx_op)):
        self.sendCommand("SEND", "%s|%s" % (tx_id, tx_op))

    def quit(self):
        self.sendCommand("QUIT")
        self.transport.loseConnection()


class TXDistributeFactory(ClientFactory):

    protocol = TXDistributeProtocol

    def __init__(self, notifier, restart=True):
        self.notify = notifier
        self.restart = restart
        self.client = None

    def tx_received(self, tx):
        self.notify._passup_tx(tx)

    def distribute(self, tx):
        if self.client is None:
            raise Exception("no client!")
        self.client.distribute(tx)

    def clientConnectionLost(self, connector, reason):
        # restart connection?
        if self.restart:
            pass

    clientConnectionFailed = clientConnectionLost


class TXNetwork(object):
    """Network object.

    Distributes TXs across the network.
    """
    def __init__(self, parent):
        factory = TXDistributeFactory(parent)
        self.sock = reactor.connectTCP("127.0.0.1", 10001, factory)

    def distribute(self, tx_id, op):
        self.sock.factory.distribute((tx_id, op))
