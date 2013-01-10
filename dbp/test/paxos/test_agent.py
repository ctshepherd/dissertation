from dbp.paxos.agent import AcceptorProtocol, LearnerProtocol, ProposerProtocol, AgentProtocol
from dbp.paxos.message import Promise, AcceptRequest, AcceptNotify, parse_message
from dbp.paxos.proposal import Proposal
from dbp.test import TestCase

from twisted.test.proto_helpers import StringTransport as TStringTransport


class StringTransport(TStringTransport):
    def write(self, data, host=None):
        """Wrapper around TStringTransport.write"""
        TStringTransport.write(self, data)

    def joinGroup(self, group):
        #print group
        pass


# class TestEchoClient(TestCase):
#     def setUp(self):
#         self.proto = EchoClientDatagramProtocol()
#         self.tr = StringTransport()
#         self.ma = MockAgent()
#         self.proto.parent = self.ma
#         self.proto.makeConnection(self.tr)
#
#     def test_read(self):
#         args = ("msg", "host")
#         self.proto.datagramReceived(*args)
#         self.assertEqual([args[0]], self.ma.msgs)
#
#     def test_write(self):
#         data = ["foo", "bar"]
#         host = "host"
#         self.proto.sendDatagram(data[0], host)
#         self.assertEqual(data[0], self.tr.value())
#         self.proto.sendDatagram(data[1], host)
#         self.assertEqual("".join(data), self.tr.value())

class FakeAgent(AgentProtocol):
    """FakeAgent class to record messages passed"""
    def _receive(self, m, host):
        pass


class AgentTestMixin(object):
    """TestCase that mocks the send and host aspects of agents"""
    def setUp(self):
        self.transport = StringTransport()
        self.agent = self.kls()
        self.agent.makeConnection(self.transport)

    def test_receive(self):
        """Test all agents can receive any message without crashing"""
        a = self.agent
        a.datagramReceived("prepare:1,None", (None, None))
        a.datagramReceived("promise:1,None", (None, None))
        a.datagramReceived("acceptnotify:1,None", (None, None))
        a.datagramReceived("acceptrequest:1,None", (None, None))
        a.datagramReceived("prepare:1,2", (None, None))
        a.datagramReceived("promise:1,2", (None, None))
        a.datagramReceived("acceptnotify:1,2", (None, None))
        a.datagramReceived("acceptrequest:1,2", (None, None))


class TestAcceptor(AgentTestMixin, TestCase):
    """Test the Acceptor agent class"""
    kls = AcceptorProtocol

    def test_promise(self):
        a = self.agent
        a.datagramReceived("prepare:1,None", (None, None))
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))

    def test_promise2(self):
        """Test that we ignore lower numbered proposals than one we've already accepted"""
        a = self.agent
        a.datagramReceived("prepare:2,None", (None, None))
        self.transport.clear()
        a.datagramReceived("prepare:1,None", (None, None))
        self.assertEqual('', self.transport.value())

    def test_promise3(self):
        """Test that we accept new, higher numbered proposals than ones we've already accepted"""
        a = self.agent
        a.datagramReceived("prepare:1,None", (None, None))
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))
        a.datagramReceived("prepare:2,None", (None, None))
        self.transport.clear()
        self.assertEqual(Promise(Proposal(2, None)), parse_message(self.transport.value()))

    def test_promise4(self):
        """Test that we ignore a message setting the value on an already accepted proposal"""
        a = self.agent
        a.datagramReceived("prepare:2,None", (None, None))
        self.assertEqual(Promise(Proposal(2, None)), parse_message(self.transport.value()))
        a.datagramReceived("prepare:2,3", (None, None))
        self.assertEqual('', self.transport.value())

    def test_accept(self):
        flearner1 = FakeAgent()
        flearner2 = FakeAgent()
        network = {'learner': [flearner1, flearner2]}
        a = self.agent
        a.datagramReceived("acceptnotify:1,2", (None, None))
        self.assertEqual(Proposal(1, 2), a._cur_prop)
        self.assertEqual(self.hmsgs[flearner1], AcceptRequest(Proposal(1, 2)))
        self.assertEqual(self.hmsgs[flearner2], AcceptRequest(Proposal(1, 2)))


class TestProposer(AgentTestMixin, TestCase):
    """Test the Proposer agent class"""
    kls = ProposerProtocol

    def test_accept(self):
        a = self.agent
        a.datagramReceived("prepare:1,None", (None, None))
        #self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))

    # def test_decline(self):
    #     a = self.agent

    # def test_run(self):
    #     a = self.agent


class TestLearner(AgentTestMixin, TestCase):
    """Test the Learner agent class"""
    kls = LearnerProtocol

    # def test_accept(self):
    #     a = self.agent

    def test_regr1(self):
        # test that if we send a Learner different accept messages for the same
        # proposal, it only accepts a majority vote
        l = []
        h = {}
        for x in xrange(5):
            fa = FakeAgent()
            l.append(fa)
            h[x] = fa
        network = {'acceptor': l}
        hosts = h
        a = self.agent

        a.datagramReceived("acceptnotify:1,2", (None, 0))
        a.datagramReceived("acceptnotify:1,2", (None, 1))
        a.datagramReceived("acceptnotify:1,3", (None, 2))
        self.assertEqual(a.accepted_proposals, {})
        a.datagramReceived("acceptnotify:1,2", (None, 3))
        self.assertEqual(a.accepted_proposals, {1: 2})

    def test_regr2(self):
        # test that if we send a Learner a bunch of accept messages from the same
        # acceptor, it only accepts a majority vote
        l = []
        h = {}
        for x in xrange(5):
            fa = FakeAgent()
            h[x] = fa
            l.append(fa)
        network = {'acceptor': l}
        hosts = h
        a = self.agent

        a.datagramReceived("acceptnotify:1,2", (None, 0))
        a.datagramReceived("acceptnotify:1,2", (None, 0))
        a.datagramReceived("acceptnotify:1,2", (None, 0))
        self.assertEqual(a.accepted_proposals, {})
        a.datagramReceived("acceptnotify:1,2", (None, 0))
        self.assertEqual(a.accepted_proposals, {})
