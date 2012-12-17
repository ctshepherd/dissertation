from twisted.trial import unittest
from twisted.test.proto_helpers import StringTransport as TStringTransport
from paxos.protocol import EchoClientDatagramProtocol


class MockAgent(object):
    def __init__(self):
        self.msgs = []

    def receive(self, msg, host):
        self.msgs.append(msg)


class StringTransport(TStringTransport):
    def write(self, data, host=None):
        """Wrapper around TStringTransport.write"""
        TStringTransport.write(self, data)


class EchoClientTest(unittest.TestCase):
    def setUp(self):
        self.proto = EchoClientDatagramProtocol()
        self.tr = StringTransport()
        self.ma = MockAgent()
        self.proto.parent = self.ma
        self.proto.makeConnection(self.tr)

    def test_read(self):
        args = ("msg", "host")
        self.proto.datagramReceived(*args)
        self.assertEqual([args[0]], self.ma.msgs)

    def test_write(self):
        data = ["foo", "bar"]
        host = "host"
        self.proto.sendDatagram(data[0], host)
        self.assertEqual(data[0], self.tr.value())
        self.proto.sendDatagram(data[1], host)
        self.assertEqual("".join(data), self.tr.value())
