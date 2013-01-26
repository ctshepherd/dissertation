from uuid import uuid4
from dbp.util import dbprint
from dbp.paxos.message import AcceptNotify, AcceptRequest, Msg, Prepare, parse_message, InvalidMessageException
from dbp.paxos.proposal import Proposal
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
                                  'prev_prop_value': instance['acceptor_cur_prop_value']
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
            self.writeAll(AcceptNotify(Proposal(msg.prop_num, msg.prop_value)))
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
                self.writeMessage(uid, AcceptRequest(Proposal(msg.prop_num, value)))

    def proposer_start(self, instance, value):
        """Start an instance of Paxos!

        Try and complete an instance of Paxos, setting the decree to value.
        """
        # (a) A proposer selects a proposal number n, greater than any proposal number it
        # has selected before, and sends a request containing n to a majority of
        # acceptors. This message is known as a prepare request.
        instance['our_value'] = value
        self.writeAll(Prepare(Proposal(1)))


class NodeProtocol(DatagramProtocol, Proposer, Acceptor, Learner):

    def stopProtocol(self):
        """
        Stop protocol: reset state variables.
        """

    def startProtocol(self):
        """
        Upon start, reset internal state.
        """
        self.instances = {}
        self.hosts = {}
        self.uid = uuid4()
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

    def discoverNetwork(self):
        self.network = {
            "acceptor": [],
            "proposer": [],
            "learner":  [],
        }

    def writeMessage(self, uid, msg):
        dbprint("%s sent message %s to %s" % (self, msg, uid), level=2)
        msg = msg.serialize()
        addr = self.hosts[uid]
        self.transport.write(msg, addr)

    def writeAll(self, msg):
        dbprint("%s sent message %s to all" % (self, msg), level=2)
        for uid in self.hosts:
            self.writeMessage(uid, msg)

    def datagramReceived(self, msg, host):
        """Called when a message is received by a specific agent.

        """
        dbprint("%s got message %s from %s" % (self, msg, host), level=2)
        self._msgs.append((msg, host))
        try:
            m = parse_message(msg)
            t = m['msg_type']
            instance = self.instances[m['instance_id']]
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
