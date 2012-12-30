from dbp.network import TXDistributeProtocol
from twisted.internet.protocol import ServerFactory


class TXDistributeServerProtocol(TXDistributeProtocol):
    def connectionMade(self):
        TXDistributeProtocol.connectionMade(self)
        self.factory.servers.append(self)


class TXDistributeServerFactory(ServerFactory):
    protocol = TXDistributeServerProtocol

    def __init__(self):
        self.servers = []

    def tx_received(self, tx):
        print "Received TX: %r" % (tx,)
        tx_id, tx_op = tx
        tx_op = tx_op.split('=')
        tx = (tx_id, tx_op)
        for s in self.servers:
            s.distribute(tx)


def main():
    from twisted.internet import reactor
    reactor.listenTCP(10001, TXDistributeServerFactory())
    reactor.run()

if __name__ == '__main__':
    main()
