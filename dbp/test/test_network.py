from dbp.network import TXDistributeProtocol
from dbp.test import TestCase
from twisted.internet.protocol import Factory
from twisted.test.proto_helpers import StringTransportWithDisconnection


def ns(s):
    return "%d:%s," % (len(s), s)


class MockFactory(Factory):
    def __init__(self):
        self.txs = []

    def tx_received(self, tx):
        self.txs.append(tx)


class TestTXDistributeProtocol(TestCase):

    def setUp(self):
        self.p = TXDistributeProtocol()
        self.transport = StringTransportWithDisconnection()
        self.p.factory = MockFactory()
        self.p.makeConnection(self.transport)
        self.transport.protocol = self.p

    def test_sends_valid_version(self):
        self.assertEquals(ns("VERSION:1"), self.transport.value())

    def test_valid_version(self):
        self.transport.clear()
        self.p.stringReceived("VERSION:1")
        self.assertEquals("", self.transport.value())
        self.assertTrue(self.transport.connected)

    def test_invalid_version(self):
        self.transport.clear()
        self.p.stringReceived("VERSION:100")
        self.assertEquals(ns("QUIT"), self.transport.value())
        self.assertFalse(self.transport.connected)

    def test_quit(self):
        self.p.stringReceived("QUIT")
        self.assertFalse(self.transport.connected)

    def test_send(self):
        self.p.stringReceived("SEND:1|('a', 'b')")
        self.assertEqual(self.p.factory.txs, [(1, 'a=b')])

    def test_distribute(self):
        self.transport.clear()
        self.p.distribute((1, ('a', 'b')))
        self.assertEqual(self.transport.value(), ns("SEND:1|('a', 'b')"))
