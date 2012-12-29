from dbp.util import dbprint
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class EchoClientDatagramProtocol(DatagramProtocol):
    def startProtocol(self):
        # add ourselves to network
        pass

    def sendDatagram(self, msg, addr):
        self.transport.write(msg, addr)

    def datagramReceived(self, datagram, host):
        dbprint('Datagram received: %s (%s)' % (repr(datagram), host), level=1)
        self.parent.receive(datagram, host)
