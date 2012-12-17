from twisted.trial import unittest
from twisted.test import proto_helpers
from paxos.protocol import *


class MockAgent(object):
    def __init__(self):
        self.msgs = []

    def receive(self, msg, host):
        self.msgs.append(msg)


class EchoClientTest(unittest.TestCase):
    def setUp(self):
        self.proto = EchoClientDatagramProtocol()
        self.tr = proto_helpers.StringTransport()
        self.ma = MockAgent()
        self.proto.parent = self.ma
        self.proto.makeConnection(self.tr)


    def test_passthru(self):
        args = ("msg", "host")
        self.proto.datagramReceived(*args)
        self.assertEqual([args[0]], self.ma.msgs)
