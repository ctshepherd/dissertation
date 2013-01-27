from uuid import uuid4
from dbp.util import dbprint
from dbp.paxos.message import Msg, parse_message, InvalidMessageException
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import defer


class Acceptor(object):
    """Acceptor Agent"""

    @staticmethod
    def acceptor_init_instance(instance):
        instance['acceptor_prepare_prop_num'] = None
        instance['acceptor_cur_prop_num'] = 0
        instance['acceptor_cur_prop_value'] = None

    def recv_prepare(self, msg, instance):
        """Update instance state appropriately based upon msg.

        (b) If an acceptor receives a prepare request with number n greater than that
        of any prepare request to which it has already responded, then it responds to
        the request with a promise not to accept any more proposals numbered less than
        n and with the highest-numbered proposal (if any) that it has accepted.
        """
        if msg.prop_num > instance['acceptor_prepare_prop_num']:
            self.writeMessage(msg['uid'],
                              Msg({
                                  'msg_type': 'promise',
                                  'prop_num': msg['prop_num'],
                                  'prev_prop_num': instance['acceptor_cur_prop_num'],
                                  'prev_prop_value': instance['acceptor_cur_prop_value'],
                                  'instance_id': instance['instance_id'],
                                  }))
            instance['acceptor_prepare_prop_num'] = msg.prop_num
        else:
            pass  # Can NACK here

    def recv_acceptrequest(self, msg, instance):
        """Update instance state appropriately based upon msg.

        (b) If an acceptor receives an accept request for a proposal numbered n, it
        accepts the proposal unless it has already responded to a prepare request
        having a number greater than n.
        """
        if msg['prop_num'] >= instance['acceptor_prepare_prop_num']:
            dbprint("Accepting proposal %s (current accepted is %s)" % (msg['prop_num'], instance['acceptor_cur_prop_num']))
            instance['acceptor_cur_prop_num'] = msg.prop_num
            instance['acceptor_cur_prop_value'] = msg.prop_value
            self.writeAll(Msg({
                "msg_type": "acceptnotify",
                "prop_num": msg.prop_num,
                "prop_value": msg.prop_value,
                "instance_id": instance['instance_id']
            }))
        else:
            pass  # Can NACK here


class Learner(object):
    """Learner Agent"""

    @staticmethod
    def learner_init_instance(instance):
        # Global
        instance['completed'] = False
        instance['value'] = None
        # Learner specific
        instance['learner_accepted'] = {}

    def recv_acceptnotify(self, msg, instance):
        """Update instance state appropriately based upon msg.

        If the proposal has been accepted by a quorum, it's completed.
        """
        # if we've already learnt it's been accepted, there's no need to
        # deal with it any more
        if instance['completed']:
            return
        s = instance['learner_accepted'].setdefault(msg['prop_num'], set())
        s.add(msg['uid'])
        if len(s) >= self.quorum_size:
            instance['completed'] = True
            instance['value'] = msg['prop_value']
            instance['callback'].callback(instance['value'])


class Proposer(object):
    """Proposer Agent"""

    @staticmethod
    def proposer_init_instance(instance):
        # Global
        instance['last_tried'] = 0
        instance['quorum'] = set()

    def recv_promise(self, msg, instance):
        """Update instance state appropriately based upon msg.

        (a) If the proposer receives a response to its prepare requests (numbered n)
        from a majority of acceptors, then it sends an accept request to each of those
        acceptors for a proposal numbered n with a value v, where v is the value of
        the highest-numbered proposal among the responses, or if the responses reported
        no proposals, a value of its own choosing.
        """
        if instance['completed']:
            # if we're done, ignore this message
            return

        instance['quorum'].add(msg['uid'])
        if len(instance['quorum']) >= self.quorum_size:
            # If this is the message that tips us over the edge and we
            # finally accept the proposal, deal with it appropriately.
            if msg['prev_prop_num'] is None:
                # if no-one else asserted a value, we can set ours
                if 'our_val' in instance:
                    value = instance['our_val']
                else:
                    # if 'our_val' isn't in instance, we didn't try and
                    # initiate this Paxos round
                    raise Exception("error!")
            else:
                # otherwise, we need to restart
                value = msg['prev_prop_value']
            for uid in instance['quorum']:
                self.writeMessage(uid,
                                  Msg({
                                      "msg_type": "acceptrequest",
                                      "prop_num": msg.prop_num,
                                      "prop_value": value,
                                      "instance_id": instance['instance_id']
                                  }))

    def proposer_start(self, instance, value):
        """Start an instance of Paxos!

        Try and complete an instance of Paxos, setting the decree to value.
        """
        # (a) A proposer selects a proposal number n, greater than any proposal number it
        # has selected before, and sends a request containing n to a majority of
        # acceptors. This message is known as a prepare request.
        instance['our_value'] = value
        self.writeAll(Msg({"msg_type": "prepare", "prop_num": (1, str(self.uid)), "instance_id": instance['instance_id']}))


class NodeProtocol(DatagramProtocol, Proposer, Acceptor, Learner):

    def __init__(self, bootstrap=None):
        self.bootstrap = bootstrap

    def stopProtocol(self):
        """
        Stop protocol: reset state variables.
        """

    def startProtocol(self):
        """
        Upon start, reset internal state.
        """
        self.instances = {}
        self.current_instance_number = 1
        self.quorum_size = 1
        self.hosts = {}
        self.uid = uuid4()
        self._msgs = []
        #reactor.listenUDP(0, self.proto)  # this returns self.proto.transport
        # Initiate discovery
        self.discoverNetwork()

    def create_instance(self, instance_id):
        instance = {}
        instance['instance_id'] = instance_id
        instance['callback'] = defer.Deferred()
        self.proposer_init_instance(instance)
        self.acceptor_init_instance(instance)
        self.learner_init_instance(instance)
        return instance

    def recv_ping(self, msg, instance):
        self.writeMessage(msg['uid'], Msg({"msg_type": "pong", "instance_id": None}))

    def recv_ehlo(self, msg, instance):
        self.writeMessage(msg['uid'], Msg({"msg_type": "notify", "hosts": self.hosts, "instance_id": None}))

    def recv_notify(self, msg, instance):
        h = msg['hosts']
        for host in self.hosts:
            h.pop(host, None)
        if h:
            for host, addr in h.iteritems():
                self.addHost(host, addr)
                self.writeMessage(msg['uid'], Msg({"msg_type": "ehlo", "instance_id": None}))

    def discoverNetwork(self):
        if self.bootstrap is not None:
            m = Msg({"msg_type": "ehlo", "uid": str(self.uid), "instance_id": None})
            self.transport.write(m.serialize(), self.bootstrap)

    def writeMessage(self, uid, msg):
        dbprint("Sent %s message to %s\n%s\n" % (msg['msg_type'], uid, msg), level=1)
        msg.contents['uid'] = str(self.uid)
        msg = msg.serialize()
        addr = self.hosts[uid]
        self.transport.write(msg, addr)

    def writeAll(self, msg):
        dbprint("%s sent message %s to all" % (self, msg), level=2)
        for uid in self.hosts:
            self.writeMessage(uid, msg)

    def addHost(self, uid, host):
        dbprint("Adding node %s (%s)" % (uid, host), level=3)
        self.hosts[uid] = host
        self.quorum_size = len(self.hosts) // 2

    def datagramReceived(self, msg, host):
        """Called when a message is received by a specific agent.

        """
        self._msgs.append((msg, host))
        try:
            m = parse_message(msg)
            # If we haven't heard this host before, add them to the record
            if m['uid'] not in self.hosts and m['uid'] != self.uid:
                self.addHost(m['uid'], host)
            t = m['msg_type']
            dbprint("Got %s message from %s\n%s\n" % (m['msg_type'], host, m), level=2)
            if m['instance_id'] is not None:
                i = m['instance_id']
                if i not in self.instances:
                    self.instances[i] = self.create_instance(i)
                instance = self.instances[i]
            else:
                instance = None
            method = getattr(self, "recv_%s" % t)
            method(m, instance)
        except InvalidMessageException, e:
            dbprint("%s received invalid message %s (%s)" % (self, msg, e))
            return

    def __repr__(self):
        u = getattr(self, "uid", None)
        if u is None:
            u = "Unknown UID"
        return "<Node(%s) @ %#lx>" % (u, id(self))

    def run(self, operation):
        i_num = self.current_instance_number
        self.current_instance_number += 1
        i = self.create_instance(i_num)
        self.proposer_start(i, operation)
