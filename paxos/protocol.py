from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class EchoUDP(DatagramProtocol):
    def datagramReceived(self, datagram, address):
        self.transport.write(datagram, address)


class EchoClientDatagramProtocol(DatagramProtocol):
    def startProtocol(self):
        # add ourselves to network
        pass

    def sendDatagram(self, msg, addr):
        self.transport.write(msg, addr)

    def datagramReceived(self, datagram, host):
        print 'Datagram received: %s (%s)' % (repr(datagram), host)
        self.parent.receive(datagram, host)


def main():
    protocol = EchoClientDatagramProtocol()
    t = reactor.listenUDP(0, protocol)
    reactor.run()
