from dbp.paxos import agent
from dbp.paxos.agent import Acceptor, Learner, Proposer, Agent
from dbp.paxos.message import Promise, Accept
from dbp.paxos.proposal import Proposal
from dbp.test import TestCase


class FakeAgent(Agent):
    """FakeAgent class to record messages passed"""
    def _receive(self, m, host):
        pass


class AgentTestMixin(object):
    """TestCase that mocks the send and host aspects of agents"""
    def setUp(self):
        # Put any messages sent into self.msgs
        self.msgs = []
        self.hmsgs = {}
        def s(r, h, m):
            self.msgs.append(m)
            self.hmsgs[h] = m
        # Save agent.send
        self.s = agent.send
        agent.send = s
        # Save agent.host
        self.h = agent.hosts
        agent.hosts = {None: None}
        # Make sure we clean up after the test
        self.agent = self.kls()
        self.addCleanup(self.agent.proto.transport.stopListening)

    def test_receive(self):
        """Test all agents can receive any message without crashing"""
        a = self.agent
        a.receive("prepare:1,None", (None, None))
        a.receive("promise:1,None", (None, None))
        a.receive("accept:1,None", (None, None))
        a.receive("prepare:1,2", (None, None))
        a.receive("promise:1,2", (None, None))
        a.receive("accept:1,2", (None, None))

    def tearDown(self):
        agent.send = self.s
        agent.hosts = self.h


class TestAcceptor(AgentTestMixin, TestCase):
    """Test the Acceptor agent class"""
    kls = Acceptor

    def test_promise(self):
        a = self.agent
        a.receive("prepare:1,None", (None, None))
        self.assertEqual(Promise(Proposal(1, None)), self.msgs.pop())

    def test_promise2(self):
        """Test that we ignore lower numbered proposals than one we've already accepted"""
        a = self.agent
        a.receive("prepare:2,None", (None, None))
        self.msgs.pop()
        a.receive("prepare:1,None", (None, None))
        self.assertEqual([], self.msgs)

    def test_promise3(self):
        """Test that we accept new, higher numbered proposals than ones we've already accepted"""
        a = self.agent
        a.receive("prepare:1,None", (None, None))
        self.assertEqual(Promise(Proposal(1, None)), self.msgs.pop())
        a.receive("prepare:2,None", (None, None))
        self.assertEqual(Promise(Proposal(2, None)), self.msgs.pop())

    def test_promise4(self):
        """Test that we ignore a message setting the value on an already accepted proposal"""
        a = self.agent
        a.receive("prepare:2,None", (None, None))
        self.assertEqual(Promise(Proposal(2, None)), self.msgs.pop())
        a.receive("prepare:2,3", (None, None))
        self.assertEqual([], self.msgs)

    def test_accept(self):
        n = agent.network
        flearner1 = FakeAgent()
        flearner2 = FakeAgent()
        self.addCleanup(flearner1.proto.transport.stopListening)
        self.addCleanup(flearner2.proto.transport.stopListening)
        agent.network = {'learner': [flearner1, flearner2]}
        a = self.agent
        a.receive("accept:1,2", (None, None))
        self.assertEqual(Proposal(1, 2), a._cur_prop)
        self.assertEqual(self.hmsgs[flearner1], Accept(Proposal(1, 2)))
        self.assertEqual(self.hmsgs[flearner2], Accept(Proposal(1, 2)))
        agent.network = n


class TestProposer(AgentTestMixin, TestCase):
    """Test the Proposer agent class"""
    kls = Proposer

    def test_accept(self):
        a = self.agent
        a.receive("prepare:1,None", (None, None))
        #self.assertEqual(Promise(Proposal(1, None)), self.msgs.pop())

    # def test_decline(self):
    #     a = self.agent

    # def test_run(self):
    #     a = self.agent


class TestLearner(AgentTestMixin, TestCase):
    """Test the Learner agent class"""
    kls = Learner

    # def test_accept(self):
    #     a = self.agent

    def test_regr1(self):
        # test that if we send a Learner different accept messages for the same
        # proposal, it only accepts a majority vote
        n = agent.network
        l = []
        h = {}
        for x in xrange(5):
            fa = FakeAgent()
            l.append(fa)
            h[x] = fa
            self.addCleanup(fa.proto.transport.stopListening)
        agent.network = {'acceptor': l}
        agent.hosts = h
        a = self.agent

        a.receive("accept:1,2", (None, 0))
        a.receive("accept:1,2", (None, 1))
        a.receive("accept:1,3", (None, 2))
        self.assertEqual(a.accepted_proposals, {})
        a.receive("accept:1,2", (None, 3))
        self.assertEqual(a.accepted_proposals, {1: 2})

        agent.network = n

    def test_regr2(self):
        # test that if we send a Learner a bunch of accept messages from the same
        # acceptor, it only accepts a majority vote
        n = agent.network
        l = []
        h = {}
        for x in xrange(5):
            fa = FakeAgent()
            h[x] = fa
            l.append(fa)
            self.addCleanup(fa.proto.transport.stopListening)
        agent.network = {'acceptor': l}
        agent.hosts = h
        a = self.agent

        a.receive("accept:1,2", (None, 0))
        a.receive("accept:1,2", (None, 0))
        a.receive("accept:1,2", (None, 0))
        self.assertEqual(a.accepted_proposals, {})
        a.receive("accept:1,2", (None, 0))
        self.assertEqual(a.accepted_proposals, {})

        agent.network = n
