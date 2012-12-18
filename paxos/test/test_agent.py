from paxos import agent
from paxos.agent import Acceptor, Learner, Proposer
from paxos.message import Promise
from paxos.proposal import Proposal
from paxos.test import TestCase


class AgentTestMixin(object):
    """TestCase that mocks the send and host aspects of agents"""
    def setUp(self):
        # Put any messages sent into self.msgs
        self.msgs = []
        def s(r, h, m):
            self.msgs.append(m)
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
        a = self.agent
        a.receive("prepare:2,None", (None, None))
        self.msgs = []
        a.receive("prepare:1,None", (None, None))
        self.assertEqual([], self.msgs)

    def test_accept(self):
        a = self.agent
        a.receive("accept:1,2", (None, None))
        self.assertEqual(Promise(Proposal(1, 2)), a._cur_prop)


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
