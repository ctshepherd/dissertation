from dbp.paxos.agent import AcceptorProtocol, LearnerProtocol, ProposerProtocol, AgentProtocol
from dbp.paxos.message import Promise, AcceptRequest, AcceptNotify, parse_message, lm
from dbp.paxos.proposal import Proposal
from dbp.test import TestCase, enable_debug

from twisted.test.proto_helpers import StringTransport as TStringTransport


class StringTransport(TStringTransport):
    def write(self, data, host=None):
        """Wrapper around TStringTransport.write"""
        TStringTransport.write(self, data)

    def joinGroup(self, group):
        #print group
        pass


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
        a.datagramReceived(lm("prepare:1,None"), (None, None))
        a.datagramReceived(lm("promise:1,None"), (None, None))
        a.datagramReceived(lm("acceptnotify:1,None"), (None, None))
        a.datagramReceived(lm("acceptrequest:1,None"), (None, None))
        #a.datagramReceived(lm("prepare:1,2"), (None, None))
        a.datagramReceived(lm("promise:1,2"), (None, None))
        a.datagramReceived(lm("acceptnotify:1,2"), (None, None))
        a.datagramReceived(lm("acceptrequest:1,2"), (None, None))


class TestAcceptor(AgentTestMixin, TestCase):
    """Test the Acceptor agent class"""
    kls = AcceptorProtocol

    def test_promise(self):
        a = self.agent
        a.datagramReceived(lm("prepare:1,None"), (None, None))
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))

    def test_promise2(self):
        """Test that we ignore lower numbered proposals than one we've already accepted"""
        a = self.agent
        a.datagramReceived(lm("prepare:2,None"), (None, None))
        self.transport.clear()
        a.datagramReceived(lm("prepare:1,None"), (None, None))
        self.assertEqual('', self.transport.value())

    def test_promise3(self):
        """Test that we accept new, higher numbered proposals than ones we've already accepted"""
        a = self.agent
        a.datagramReceived(lm("prepare:1,None"), (None, None))
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))
        self.transport.clear()
        a.datagramReceived(lm("prepare:2,None"), (None, None))
        self.assertEqual(Promise(Proposal(2, None)), parse_message(self.transport.value()))

    # def test_promise4(self):
    #     """Test that we ignore a message setting the value on an already accepted proposal"""
    #     a = self.agent
    #     a.datagramReceived(lm("prepare:2,None"), (None, None))
    #     self.assertEqual(Promise(Proposal(2, None)), parse_message(self.transport.value()))
    #     self.transport.clear()
    #     a.datagramReceived(lm("prepare:2,3"), (None, None))
    #     self.assertEqual('', self.transport.value())

    def test_accept(self):
        flearner1 = FakeAgent()
        flearner2 = FakeAgent()
        a = self.agent
        a.network = {'learner': [flearner1, flearner2]}
        a.datagramReceived(lm("acceptrequest:1,2"), (None, None))
        self.assertEqual(Proposal(1, 2), a._cur_prop)
        self.assertEqual(AcceptNotify(Proposal(1, 2)), parse_message(self.transport.value()))

    # test ignore propose with value, nacks


class TestProposer(AgentTestMixin, TestCase):
    """Test the Proposer agent class"""
    kls = ProposerProtocol

    @enable_debug
    def test_promise_novalue(self):
        # promises - no values - send value
        fa1 = FakeAgent()
        fa2 = FakeAgent()
        fa3 = FakeAgent()
        a = self.agent
        a.network = {'acceptor': [fa1, fa2, fa3]}

        a.datagramReceived(lm("promise:1,None"), (None, 0))
        self.assertEqual('', self.transport.value())
        self.assertFalse(a.accepted)
        a.datagramReceived(lm("promise:1,None"), (None, 1))
        self.assertEqual('', self.transport.value())
        self.assertTrue(a.accepted)
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))

    @enable_debug
    def test_promise_onevalue(self):
        # promises - one value - send orig value
        fa1 = FakeAgent()
        fa2 = FakeAgent()
        fa3 = FakeAgent()
        a = self.agent
        a.network = {'acceptor': [fa1, fa2, fa3]}

        a.datagramReceived(lm("promise:1,None"), (None, 0))
        self.assertEqual('', self.transport.value())
        self.assertFalse(a.accepted)
        a.datagramReceived(lm("promise:1,1"), (None, 1))
        self.assertEqual('', self.transport.value())
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))

    @enable_debug
    def test_promise_multiple_values(self):
        # promises - multiple values - send highest value
        fa1 = FakeAgent()
        fa2 = FakeAgent()
        fa3 = FakeAgent()
        a = self.agent
        a.network = {'acceptor': [fa1, fa2, fa3]}

        a.datagramReceived(lm("promise:1,2"), (None, 0))
        self.assertEqual('', self.transport.value())
        self.assertFalse(a.accepted)
        a.datagramReceived(lm("promise:2,1"), (None, 1))
        self.assertEqual('', self.transport.value())
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))
        self.assertEqual(Promise(Proposal(1, None)), parse_message(self.transport.value()))


class TestLearner(AgentTestMixin, TestCase):
    """Test the Learner agent class"""
    kls = LearnerProtocol

    # def test_accept(self):
    #     a = self.agent

    def test_regr1(self):
        # test that if we send a Learner different accept messages for the same
        # proposal, it only accepts a majority vote
        l = [FakeAgent() for x in xrange(5)]
        a = self.agent
        a.network = {'acceptor': l}

        a.datagramReceived(lm("acceptnotify:1,2"), (None, 0))
        a.datagramReceived(lm("acceptnotify:1,2"), (None, 1))
        a.datagramReceived(lm("acceptnotify:1,3"), (None, 2))
        self.assertEqual(a.accepted_proposals, {})
        a.datagramReceived(lm("acceptnotify:1,2"), (None, 3))
        self.assertEqual(a.accepted_proposals, {1: 2})

    def test_regr2(self):
        # test that if we send a Learner a bunch of accept messages from the same
        # acceptor, it only accepts a majority vote
        l = [FakeAgent() for x in xrange(5)]
        a = self.agent
        a.network = {'acceptor': l}

        a.datagramReceived(lm("acceptnotify:1,2"), (None, 0))
        a.datagramReceived(lm("acceptnotify:1,2"), (None, 0))
        a.datagramReceived(lm("acceptnotify:1,2"), (None, 0))
        self.assertEqual(a.accepted_proposals, {})
        a.datagramReceived(lm("acceptnotify:1,2"), (None, 0))
        self.assertEqual(a.accepted_proposals, {})
