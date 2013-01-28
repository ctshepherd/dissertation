from dbp.paxos.agent import NodeProtocol
from dbp.paxos.message import Msg, parse_message
from dbp.test import TestCase

from twisted.internet.task import Clock
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


class AgentTestMixin(object):
    """TestCase that mocks the send and host aspects of agents"""
    def setUp(self):
        self.clock = Clock()
        self.transport = StringTransport()
        self.node = NodeProtocol(clock=self.clock)
        self.node.makeConnection(self.transport)
        # Simple hosts mapping for the tests
        self.node.hosts = {x: x for x in xrange(10)}

    def assertMsg(self, m1, m2):
        """Assert that the contents of m1 is contained within m2"""
        d1 = m1.contents
        d2 = m2.contents
        for k, v in d1.iteritems():
            if k in d2:
                self.assertEqual(v, d2[k], "%s: %s not equal to %s" % (k, v, d2[k]))
            else:
                self.fail("%s not contained in %s" % (k, d2))


class TestAcceptor(AgentTestMixin, TestCase):
    """Test the Acceptor agent class"""

    def test_promise(self):
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num':  (1, ''), "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num':  (1, ''), 'prev_prop_num': 0})
        self.assertMsg(res, parse_message(self.transport.value()))

    def test_promise2(self):
        """Test that we ignore lower numbered proposals than one we've already accepted"""
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num':  (2, ''), "uid": 1}), i)
        self.transport.clear()
        self.node.recv_prepare(Msg({'prop_num':  (1, ''), "uid": 1}), i)
        self.assertEqual('', self.transport.value())

    def test_promise3(self):
        """Test that we accept new, higher numbered proposals than ones we've already accepted"""
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num':  (1, ''), "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num':  (1, ''), 'prev_prop_num': 0})
        self.assertMsg(res, parse_message(self.transport.value()))
        self.transport.clear()
        self.node.recv_prepare(Msg({'prop_num':  (2, ''), "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num':  (2, ''), 'prev_prop_num': 0})
        self.assertMsg(res, parse_message(self.transport.value()))

    def test_promise4(self):
        """Test that we respond with any proposal we've accepted"""
        i = self.node.create_instance(1)
        self.node.recv_prepare(Msg({'prop_num': (1, ''), "uid": 1}), i)
        res = Msg({'prev_prop_value': None, 'msg_type': 'promise', 'prop_num': (1, ''), 'prev_prop_num': 0})
        self.assertMsg(res, parse_message(self.transport.value()))
        self.transport.clear()

        self.node.recv_acceptrequest(Msg({'prop_num': (1, ''), 'prop_value': 2, "uid": 1}), i)
        self.transport.clear()

        self.node.recv_prepare(Msg({'prop_num': (2, ''), "uid": 1}), i)
        res = Msg({'prev_prop_value': 2, 'msg_type': 'promise', 'prop_num': (2, ''), 'prev_prop_num': (1, '')})
        self.assertMsg(res, parse_message(self.transport.value()))

    def test_accept(self):
        """Test that on proposal acceptance the Node notifies all other nodes about its decision"""
        i = self.node.create_instance(1)
        self.node.recv_acceptrequest(Msg({'prop_num': (1, ''), 'prop_value': 2, "uid": 1}), i)
        self.assertEqual((1, ''), i['acceptor_cur_prop_num'])
        for x in xrange(10):
            self.assertMsg(Msg({"msg_type": "acceptnotify", "prop_num": (1, ''), "prop_value": 2}), parse_message(self.transport.msgs[x]))

    # test ignore propose with value, nacks


class TestProposer(AgentTestMixin, TestCase):
    """Test the Proposer agent class"""

    def test_promise_novalue(self):
        # promises - no values - send value
        n = self.node
        i = n.create_instance(1)
        i['our_val'] = 5
        i['status'] = "trying"
        i['last_tried'] = (1, '')
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num':  (1, ''), 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 1}), i)
        self.assertEqual('', self.transport.value())
        self.transport.clear()

        n.recv_promise(Msg({'prop_num':  (1, ''), 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 2}), i)
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (1, ''), "prop_value": 5}), parse_message(self.transport.msgs[0]))
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (1, ''), "prop_value": 5}), parse_message(self.transport.msgs[1]))

    def test_promise_onevalue(self):
        # promises - one value - send orig value
        n = self.node
        i = n.create_instance(1)
        i['status'] = "trying"
        i['last_tried'] = (2, '')
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num':  (2, ''), 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 1}), i)
        self.assertEqual('', self.transport.value())
        n.recv_promise(Msg({'prop_num':  (2, ''), 'prev_prop_num': 1, 'prev_prop_value': 1, 'uid': 2}), i)
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (2, ''), "prop_value": 1}), parse_message(self.transport.msgs[0]))
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (2, ''), "prop_value": 1}), parse_message(self.transport.msgs[1]))

    def test_promise_multiple_values(self):
        # promises - multiple values - send highest value
        n = self.node
        i = n.create_instance(1)
        i['status'] = "trying"
        i['last_tried'] = (3, '')
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num':  (3, ''), 'prev_prop_num': 1, 'prev_prop_value': 5, 'uid': 1}), i)
        self.assertEqual('', self.transport.value())

        n.recv_promise(Msg({'prop_num':  (3, ''), 'prev_prop_num': 2, 'prev_prop_value': 6, 'uid': 2}), i)
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (3, ''), "prop_value": 6}), parse_message(self.transport.msgs[0]))
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (3, ''), "prop_value": 6}), parse_message(self.transport.msgs[1]))

    def test_promise_multiple_values2(self):
        # promises - multiple values - send highest value
        # (same as test_promise_multiple_values but in reverse order)
        n = self.node
        i = n.create_instance(1)
        i['status'] = "trying"
        i['last_tried'] = (3, '')
        n.quorum_size = 2

        n.recv_promise(Msg({'prop_num':  (3, ''), 'prev_prop_num': (2, ''), 'prev_prop_value': 6, 'uid': 2}), i)
        self.assertEqual('', self.transport.value())

        n.recv_promise(Msg({'prop_num':  (3, ''), 'prev_prop_num': (1, ''), 'prev_prop_value': 5, 'uid': 1}), i)
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (3, ''), "prop_value": 6}), parse_message(self.transport.msgs[0]))
        self.assertMsg(Msg({"msg_type": "acceptrequest", "prop_num": (3, ''), "prop_value": 6}), parse_message(self.transport.msgs[1]))

    def test_prepare_timeout(self):
        """Test what happens when a Prepare message times out"""
        n = self.node
        i = n.create_instance(1)
        n.uid = ''

        n.proposer_start(i, "foo")
        self.assertEqual(i['our_val'], "foo")
        self.assertEqual(i['status'], "trying")
        self.assertEqual(i['last_tried'], (1, ''))

        self.clock.advance(2*n.proposer_timeout)

        self.assertEqual(i['our_val'], "foo")
        self.assertEqual(i['status'], "trying")
        self.assertEqual(i['last_tried'], (2, ''))

    def test_prepare_notimeout(self):
        """Check the timeout doesn't run if we receive responses to our message"""
        n = self.node
        i = n.create_instance(1)
        n.uid = ''

        n.proposer_start(i, "foo")
        i['status'] = "polling"

        self.clock.advance(2*n.proposer_timeout)

        self.assertEqual(i['our_val'], "foo")
        self.assertEqual(i['status'], "polling")
        self.assertEqual(i['last_tried'], (1, ''))

    def test_prepare_timeout_responses(self):
        n = self.node
        i = n.create_instance(1)
        n.quorum_size = 2
        n.uid = ''

        n.proposer_start(i, "foo")
        n.recv_promise(Msg({'prop_num':  (1, ''), 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 1}), i)
        n.recv_promise(Msg({'prop_num':  (1, ''), 'prev_prop_num': None, 'prev_prop_value': None, 'uid': 2}), i)

        self.assertEqual(i['our_val'], "foo")
        self.assertEqual(i['status'], "polling")
        self.assertEqual(i['last_tried'], (1, ''))


class TestLearner(AgentTestMixin, TestCase):
    """Test the Learner agent class"""

    def test_regr1(self):
        # test that if we send a Learner different accept messages for the same
        # proposal, it only accepts a majority vote
        n = self.node

        n.quorum_size = 3
        i = n.create_instance(1)
        i['status'] = "polling"
        n.recv_acceptnotify(Msg({'prop_num': (1, ''), 'prop_value': 1, 'uid': 1}), i)
        n.recv_acceptnotify(Msg({'prop_num': (1, ''), 'prop_value': 1, 'uid': 2}), i)
        n.recv_acceptnotify(Msg({'prop_num': (2, ''), 'prop_value': 2, 'uid': 3}), i)
        self.assertEqual(i['status'], "polling")
        n.recv_acceptnotify(Msg({'prop_num': (1, ''), 'prop_value': 1, 'uid': 4}), i)
        self.assertEqual(i['status'], "completed")
        self.assertEqual(i['value'], 1)

    def test_regr2(self):
        # test that if we send a Learner a bunch of accept messages from the same
        # acceptor, it only accepts a majority vote
        n = self.node

        n.quorum_size = 3
        i = n.create_instance(1)
        i['status'] = "polling"
        n.recv_acceptnotify(Msg({'prop_num': (1, ''), 'prop_value': 1, 'uid': 1}), i)
        n.recv_acceptnotify(Msg({'prop_num': (1, ''), 'prop_value': 1, 'uid': 1}), i)
        n.recv_acceptnotify(Msg({'prop_num': (2, ''), 'prop_value': 2, 'uid': 1}), i)
        self.assertEqual(i['status'], "polling")


class TestNode(AgentTestMixin, TestCase):
    def test_receive(self):
        """Test all agents can receive any message without crashing"""
        a = self.node
        a.datagramReceived(Msg({'msg_type': "prepare", 'uid': 1, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': None}).serialize(), None)
        #a.datagramReceived(Msg({'msg_type': "promise", 'uid': 1, 'prev_prop_value': None, 'prev_prop_num': 0, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': None}).serialize(), None)
        a.datagramReceived(Msg({'msg_type': "acceptnotify", 'uid': 1, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': None}).serialize(), None)
        a.datagramReceived(Msg({'msg_type': "acceptrequest", 'uid': 1, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': None}).serialize(), None)
        a.datagramReceived(Msg({'msg_type': "prepare", 'uid': 1, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': 2}).serialize(), None)
        a.datagramReceived(Msg({'msg_type': "promise", 'uid': 1, 'instance_id': 1, 'prev_prop_value': None, 'prev_prop_num': 0, 'prop_num':  (1, ''), 'prop_value': 2}).serialize(), None)
        a.datagramReceived(Msg({'msg_type': "acceptnotify", 'uid': 1, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': 2}).serialize(), None)
        a.datagramReceived(Msg({'msg_type': "acceptrequest", 'uid': 1, 'instance_id': 1, 'prop_num':  (1, ''), 'prop_value': 2}).serialize(), None)

    def test_run(self):
        n = self.node
        n.uid = 1
        n.run("foo")
        for m in self.transport.msgs:
            self.assertMsg(Msg({'msg_type': "prepare", 'uid': 1, 'instance_id': 1, 'prop_num': (1, 1)}), parse_message(m))

    def test_invalid_message(self):
        """Test there's no problems with invalid messages"""
        self.node.datagramReceived("foobar", None)
        self.node.datagramReceived("'baz'", None)
        self.node.datagramReceived("bar()", None)
        self.node.datagramReceived("{xyz", None)

    def test_unknown_host(self):
        self.node.datagramReceived(Msg({'msg_type': "pong", 'uid': 100, 'instance_id': None}).serialize(), None)
        self.assertTrue(100 in self.node.hosts)
        self.assertEqual(self.node.hosts[100], None)
        self.node.datagramReceived(Msg({'msg_type': "pong", 'uid': 101, 'instance_id': None}).serialize(), None)
        self.node.datagramReceived(Msg({'msg_type': "pong", 'uid': 102, 'instance_id': None}).serialize(), None)
        self.assertEqual(self.node.quorum_size, 7)

    def test_unknown_instance(self):
        self.node.datagramReceived(Msg({'msg_type': "prepare", 'uid': 1, 'instance_id': 500, 'prop_num': (1, ''), 'prop_value': None}).serialize(), None)
        self.assertTrue(self.node.instances[500])

    def test_autodiscover(self):
        self.node.bootstrap = object()
        self.node.discoverNetwork()
        self.assertMsg(Msg({"msg_type": "ehlo", "instance_id": None}), parse_message(self.transport.value()))

    def test_receive_ehlo(self):
        self.node.recv_ehlo(Msg({"uid": 1}), None)
        self.assertMsg(Msg({"msg_type": "notify", "hosts": self.node.hosts, "instance_id": None}), parse_message(self.transport.value()))

    def test_receive_notify(self):
        self.node.recv_notify(Msg({'msg_type': "notify", "uid": 1, "hosts": {"foo": "bar"}}), None)
        self.assertEqual(self.node.hosts["foo"], "bar")
        self.assertMsg(Msg({"msg_type": "ehlo", "instance_id": None}), parse_message(self.transport.value()))

    def test_receive_ping(self):
        self.node.recv_ping(Msg({"uid": 1}), None)
        self.assertMsg(Msg({"msg_type": "pong"}), parse_message(self.transport.value()))

    def test_timeout(self):
        self.clock.advance(self.node.timeout)
        self.node.recv_pong(Msg({"uid": 1}), None)
        self.node.recv_pong(Msg({"uid": 2}), None)
        self.clock.advance(self.node.timeout)
        self.assertEqual(self.node.hosts, {1: 1, 2: 2})
