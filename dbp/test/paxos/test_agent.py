from dbp.paxos.agent import NodeProtocol
from dbp.paxos.message import Msg, AcceptRequest, AcceptNotify, parse_message
from dbp.paxos.proposal import Proposal
from dbp.test import TestCase

from twisted.test.proto_helpers import StringTransport as TStringTransport


class StringTransport(TStringTransport):
    def __init__(self):
        TStringTransport.__init__(self)
        self.msgs = []

    def write(self, data, host=None):
        """Wrapper around TStringTransport.write"""
        TStringTransport.write(self, data)
        self.msgs.append(data)

    def clear(self):
        TStringTransport.clear(self)
        self.msgs = []

    def joinGroup(self, group):
        #print group
        pass


# class FakeAgent(AgentProtocol):
#     """FakeAgent class to record messages passed"""
#     def _receive(self, m, host):
#         pass


class AgentTestMixin(object):
    """TestCase that mocks the send and host aspects of agents"""
    def setUp(self):
        self.transport = StringTransport()
        self.node = NodeProtocol()
        self.node.makeConnection(self.transport)
        # Simple hosts mapping for the tests
        self.node.hosts = {x: x for x in xrange(10)}


class TestAcceptor(AgentTestMixin, TestCase):
    """Test the Acceptor agent class"""

    def test_promise(self):
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num': 1, "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num': 1, 'prev_prop_num': 0})
        self.assertEqual(res, parse_message(self.transport.value()))

    def test_promise2(self):
        """Test that we ignore lower numbered proposals than one we've already accepted"""
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num': 2, "uid": 1}), i)
        self.transport.clear()
        self.node.recv_prepare(Msg({'prop_num': 1, "uid": 1}), i)
        self.assertEqual('', self.transport.value())

    def test_promise3(self):
        """Test that we accept new, higher numbered proposals than ones we've already accepted"""
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num': 1, "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num': 1, 'prev_prop_num': 0})
        self.assertEqual(res, parse_message(self.transport.value()))
        self.transport.clear()
        self.node.recv_prepare(Msg({'prop_num': 2, "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num': 2, 'prev_prop_num': 0})
        self.assertEqual(res, parse_message(self.transport.value()))

    def test_promise4(self):
        """Test that we respond with any proposal we've accepted"""
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num': 1, "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num': 1, 'prev_prop_num': 0})
        self.assertEqual(res, parse_message(self.transport.value()))
        self.transport.clear()

        self.node.recv_acceptrequest(Msg({'prop_num': 1, 'prop_value': 2, "uid": 1}), i)
        self.transport.clear()

        self.node.recv_prepare(Msg({'prop_num': 2, "uid": 1}), i)
        res = Msg({'prev_prop_value': 2, 'msg_type': 'promise', 'prop_num': 2, 'prev_prop_num': 1})
        self.assertEqual(res, parse_message(self.transport.value()))

    def test_accept(self):
        """Test that on proposal acceptance the Node notifies all other nodes about its decision"""
        i = self.node.create_instance(1)
        self.node.recv_acceptrequest(Msg({'prop_num': 1, 'prop_value': 2, "uid": 1}), i)
        self.assertEqual(1, i['acceptor_cur_prop_num'])
        for x in xrange(10):
            self.assertEqual(AcceptNotify(Proposal(1, 2)), parse_message(self.transport.msgs[x]))

    # test ignore propose with value, nacks


class TestProposer(AgentTestMixin, TestCase):
    """Test the Proposer agent class"""

    def test_promise_novalue(self):
        # promises - no values - send value
        n = self.node
        i = n.create_instance(1)
        i['our_val'] = 5
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num': 1, 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 1}), i)
        self.assertEqual('', self.transport.value())
        self.transport.clear()

        n.recv_promise(Msg({'prop_num': 1, 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 2}), i)
        self.assertEqual(AcceptRequest(Proposal(1, 5)), parse_message(self.transport.msgs[0]))
        self.assertEqual(AcceptRequest(Proposal(1, 5)), parse_message(self.transport.msgs[1]))

    def test_promise_onevalue(self):
        # promises - one value - send orig value
        n = self.node
        i = n.create_instance(1)
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num': 2, 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 1}), i)
        self.assertEqual('', self.transport.value())
        n.recv_promise(Msg({'prop_num': 2, 'prev_prop_num': 1, 'prev_prop_value': 1, 'uid': 2}), i)
        self.assertEqual(AcceptRequest(Proposal(2, 1)), parse_message(self.transport.msgs[0]))
        self.assertEqual(AcceptRequest(Proposal(2, 1)), parse_message(self.transport.msgs[1]))

    def test_promise_multiple_values(self):
        # promises - multiple values - send highest value
        n = self.node
        i = n.create_instance(1)
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num': 3, 'prev_prop_num': 1, 'prev_prop_value': 5, 'uid': 1}), i)
        self.assertEqual('', self.transport.value())

        n.recv_promise(Msg({'prop_num': 3, 'prev_prop_num': 2, 'prev_prop_value': 6, 'uid': 2}), i)
        self.assertEqual(AcceptRequest(Proposal(3, 6)), parse_message(self.transport.msgs[0]))
        self.assertEqual(AcceptRequest(Proposal(3, 6)), parse_message(self.transport.msgs[1]))

    def test_promise_multiple_values2(self):
        # promises - multiple values - send highest value
        # (same as test_promise_multiple_values but in reverse order)
        n = self.node
        i = n.create_instance(1)
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num': 3, 'prev_prop_num': 2, 'prev_prop_value': 6, 'uid': 2}), i)
        self.assertEqual('', self.transport.value())

        n.recv_promise(Msg({'prop_num': 3, 'prev_prop_num': 1, 'prev_prop_value': 5, 'uid': 1}), i)
        self.assertEqual(AcceptRequest(Proposal(3, 6)), parse_message(self.transport.msgs[0]))
        self.assertEqual(AcceptRequest(Proposal(3, 6)), parse_message(self.transport.msgs[1]))


class TestLearner(AgentTestMixin, TestCase):
    """Test the Learner agent class"""

    def test_regr1(self):
        # test that if we send a Learner different accept messages for the same
        # proposal, it only accepts a majority vote
        n = self.node

        n.quorum_size = 3
        i = n.create_instance(1)
        n.recv_acceptnotify(Msg({'prop_num': 1, 'prop_value': 1, 'uid': 1}), i)
        n.recv_acceptnotify(Msg({'prop_num': 1, 'prop_value': 1, 'uid': 2}), i)
        n.recv_acceptnotify(Msg({'prop_num': 2, 'prop_value': 2, 'uid': 3}), i)
        self.assertFalse(i['completed'])
        n.recv_acceptnotify(Msg({'prop_num': 1, 'prop_value': 1, 'uid': 4}), i)
        self.assertTrue(i['completed'])
        self.assertEqual(i['value'], 1)

    def test_regr2(self):
        # test that if we send a Learner a bunch of accept messages from the same
        # acceptor, it only accepts a majority vote
        n = self.node

        n.quorum_size = 3
        i = n.create_instance(1)
        n.recv_acceptnotify(Msg({'prop_num': 1, 'prop_value': 1, 'uid': 1}), i)
        n.recv_acceptnotify(Msg({'prop_num': 1, 'prop_value': 1, 'uid': 1}), i)
        n.recv_acceptnotify(Msg({'prop_num': 2, 'prop_value': 2, 'uid': 1}), i)
        self.assertFalse(i['completed'])


class NodeTest(AgentTestMixin, TestCase):
    def test_receive(self):
        """Test all agents can receive any message without crashing"""
        a = self.node
        a.datagramReceived(Msg({'msg_type': "prepare", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': None}), None)
        a.datagramReceived(Msg({'msg_type': "promise", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': None}), None)
        a.datagramReceived(Msg({'msg_type': "acceptnotify", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': None}), None)
        a.datagramReceived(Msg({'msg_type': "acceptrequest", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': None}), None)
        a.datagramReceived(Msg({'msg_type': "prepare", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': 2}), None)
        a.datagramReceived(Msg({'msg_type': "promise", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': 2}), None)
        a.datagramReceived(Msg({'msg_type': "acceptnotify", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': 2}), None)
        a.datagramReceived(Msg({'msg_type': "acceptrequest", 'uid': 1, 'instance_id': 1, 'prop_num': 1, 'prop_value': 2}), None)

    def test_run(self):
        n = self.node
        n.run("foo")
        self.assertEqual('', self.transport.value())
