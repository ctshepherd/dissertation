from uuid import uuid4
from dbp.util import dbprint
from dbp.config import NODE_TIMEOUT, PROPOSER_TIMEOUT, NACKS_ENABLED
from dbp.paxos.message import Msg, parse_message, InvalidMessageException
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, defer


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
            if NACKS_ENABLED:
                d = {
                    'msg_type': 'nack_promise',
                    'prop_num': msg['prop_num'],
                    'instance_id': instance['instance_id'],
                }
                if NACKS_ENABLED == 2:
                    d['prev_prop_num'] = instance['acceptor_cur_prop_num']
                    d['prev_prop_value'] = instance['acceptor_cur_prop_value']
                self.writeMessage(msg['uid'], Msg(d))

    def recv_acceptrequest(self, msg, instance):
        """Update instance state appropriately based upon msg.

        (b) If an acceptor receives an accept request for a proposal numbered n, it
        accepts the proposal unless it has already responded to a prepare request
        having a number greater than n.
        """
        if msg['prop_num'] >= instance['acceptor_prepare_prop_num']:
            dbprint("Instance %d: accepting prop %s (current is %s)"
                    % (instance['instance_id'],
                       msg['prop_num'],
                       instance['acceptor_cur_prop_num']),
                    level=4)
            instance['acceptor_cur_prop_num'] = msg.prop_num
            instance['acceptor_cur_prop_value'] = msg.prop_value
            self.writeAll(Msg({
                "msg_type": "acceptnotify",
                "prop_num": msg.prop_num,
                "prop_value": msg.prop_value,
                "instance_id": instance['instance_id']
            }))
        else:
            if NACKS_ENABLED:
                d = {
                    'msg_type': 'nack_acceptrequest',
                    'prop_num': msg['prop_num'],
                    'instance_id': instance['instance_id'],
                }
                if NACKS_ENABLED == 2:
                    d['prev_prop_num'] = instance['acceptor_cur_prop_num']
                    d['prev_prop_value'] = instance['acceptor_cur_prop_value']
                self.writeMessage(msg['uid'], Msg(d))


class Learner(object):
    """Learner Agent"""

    @staticmethod
    def learner_init_instance(instance):
        # Global
        instance['value'] = None
        # Learner specific
        instance['learner_accepted'] = {}

    def recv_acceptnotify(self, msg, instance):
        """Update instance state appropriately based upon msg.

        If the proposal has been accepted by a quorum, it's completed.
        """
        # if we've already learnt it's been accepted, there's no need to
        # deal with it any more
        if instance['status'] == "completed":
            return
        s = instance['learner_accepted'].setdefault(msg['prop_num'], set())
        s.add(msg['uid'])
        if len(s) >= self.quorum_size:
            dbprint("Instance %d: learnt value %s (prop %s)"
                    % (instance['instance_id'],
                       msg['prop_value'],
                       msg['prop_num']),
                    level=4)
            instance['status'] = "completed"
            instance['value'] = msg['prop_value']
            assert not instance['callback'].called, "completion error 1: %s: %s" % (msg, instance)
            instance['callback'].callback(instance)


class Proposer(object):
    """Proposer Agent"""

    proposer_timeout = PROPOSER_TIMEOUT

    @staticmethod
    def proposer_init_instance(instance):
        # Global
        assert not instance['callback'].called, "completion error 2: %s" % instance
        instance['quorum'] = set()
        instance['status'] = "idle"
        instance['last_tried'] = 0
        instance['restart'] = False
        # Proposer only
        instance['proposer_prev_prop_num'] = 0
        instance['proposer_prev_prop_value'] = None

    def recv_promise(self, msg, instance):
        """Update instance state appropriately based upon msg.

        (a) If the proposer receives a response to its prepare requests (numbered n)
        from a majority of acceptors, then it sends an accept request to each of those
        acceptors for a proposal numbered n with a value v, where v is the value of
        the highest-numbered proposal among the responses, or if the responses reported
        no proposals, a value of its own choosing.
        """
        # If this is an old message or we're in the wrong state, ignore
        if msg['prop_num'] != instance['last_tried']:# or instance['status'] != "trying":
            dbprint("proposer ignoring msg %s, not appropriate (%s)"
                    % (msg, instance),
                    level=1)
            return

        instance['quorum'].add(msg['uid'])

        if msg['prev_prop_value'] is not None:
            if msg['prev_prop_num'] > instance['proposer_prev_prop_num']:
                dbprint("loading old prop value of %s (num %s)"
                        % (msg['prev_prop_value'], msg['prev_prop_num']),
                        level=2)
                instance['proposer_prev_prop_num'] = msg['prev_prop_num']
                instance['proposer_prev_prop_value'] = msg['prev_prop_value']
            else:
                dbprint("ignoring old prop value of %s (num %s) for prop %s"
                        % (msg['prev_prop_value'],
                           msg['prev_prop_num'],
                           instance['proposer_prev_prop_value']),
                        level=2)

        if len(instance['quorum']) >= self.quorum_size:
            # If this is the message that tips us over the edge and we
            # finally accept the proposal, deal with it appropriately.
            if instance['status'] == 'trying':
                self.poll(instance, msg['prop_num'])
            # XXX: this is new code, test before committing!
            # # Otherwise just reply
            # else:
            #     self.send_acceptrequest(msg['uid'], msg['prop_num'], value, instance)

    def poll(self, instance, prop_num):
        instance['status'] = "polling"

        # Decide what value to use
        # if no-one else asserted a value, we can set ours
        if instance['proposer_prev_prop_value'] is None:
            assert('our_val' in instance) # if 'our_val' isn't in instance, we
                                          # didn't try and initiate this Paxos
                                          # round, so we have no idea what to
                                          # do? (Maybe could just nop here?)
            value = instance['our_val']
        else:
            # otherwise we have to use the already asserted one and restart
            value = instance['proposer_prev_prop_value']
            # if we wanted to set a value, try again
            if 'our_val' in instance and instance['restart']:
                self.run(instance['our_val'])
                # delete our_val so we don't try and restart too often
                del instance['our_val']
                instance['restart'] = None
                #instance['restarted'] = True

        for uid in instance['quorum']:
            self.send_acceptrequest(uid, prop_num, value, instance)

        self.reactor.callLater(self.proposer_timeout, self.handle_proposer_timeout, instance, "polling")

    def send_acceptrequest(self, uid, prop_num, value, instance):
        d = {
            "msg_type": "acceptrequest",
            "prop_num": prop_num,
            "prop_value": value,
            "instance_id": instance['instance_id']
        }
        self.writeMessage(uid, Msg(d))

    def proposer_start(self, instance, value, prop_num=1, restart=True):
        """Start an instance of Paxos!

        Try and complete an instance of Paxos, setting the decree to value.
        """
        # (a) A proposer selects a proposal number n, greater than any proposal number it
        # has selected before, and sends a request containing n to a majority of
        # acceptors. This message is known as a prepare request.
        instance['our_val'] = value
        instance['status'] = "trying"
        p = (prop_num, self.uid)
        instance['last_tried'] = p
        instance['restart'] = restart
        self.writeAll(
            Msg({
                "msg_type": "prepare",
                "prop_num": p,
                "instance_id": instance['instance_id']
            }))
        self.reactor.callLater(self.proposer_timeout, self.handle_proposer_timeout, instance, "trying")

    def handle_proposer_timeout(self, instance, expected_status):
        """What to do if no-one replied to our prepare message.

        This method is called after a timeout period. If we haven't moved on to
        the next stage of a proposal in time, this method will restart with a
        higher proposal number.
        """
        # If we're still waiting to hear back from enough people, try a higher
        # proposal number
        if instance['status'] == expected_status:
            # if 'restarted' in instance:
            #     dbprint("restarted instance %d" % instance['instance_id'], level=2)
            #     return
            v = instance['our_val']
            l = instance['last_tried'][0]
            r = instance['restart']
            self.proposer_init_instance(instance)
            self.proposer_start(instance, v, prop_num=l+1, restart=r)


class NodeProtocol(DatagramProtocol, Proposer, Acceptor, Learner):

    # If we don't hear from a node every timeout period, time them out
    timeout = NODE_TIMEOUT

    def __init__(self, bootstrap=None, clock=None):
        self.bootstrap = bootstrap
        if clock is not None:
            self.reactor = clock
        else:
            self.reactor = reactor

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
        self.uid = str(uuid4())
        self._msgs = []

        # Initiate discovery
        self.discoverNetwork()

        # Start timeout tests
        self.timeout_test(init=True)

    def create_instance(self, instance_id):
        """Create an instance dict with id instance_id and return it."""
        instance = {}
        instance['instance_id'] = instance_id
        instance['callback'] = defer.Deferred()
        self.proposer_init_instance(instance)
        self.acceptor_init_instance(instance)
        self.learner_init_instance(instance)
        return instance


    def timeout_test(self, init=False):
        # If this isn't the first time we've run, do some pruning
        if not init:
            # Remove any hosts we haven't heard from yet
            for h in self.timeout_hosts:
                self.hosts.pop(h, None)

        # Start again
        self.timeout_hosts = dict(self.hosts)
        for h in self.hosts:
            self.writeMessage(h, Msg({"msg_type": "ping", "instance_id": None}))
        self.reactor.callLater(self.timeout, self.timeout_test)

    def recv_ping(self, msg, instance):
        """Reply to a PING with a PONG (as a heartbeat)"""
        self.writeMessage(msg['uid'], Msg({"msg_type": "pong", "instance_id": None}))

    def recv_pong(self, msg, instance):
        """When we get a PONG from someone, remove them from the timeout pruning dictionary."""
        self.timeout_hosts.pop(msg['uid'], None)
        self.write_notify(msg['uid'])


    # Network discovery methods
    def write_notify(self, uid):
        """Send a NOTIFY message with all the hosts we know about."""
        self.writeMessage(uid, Msg({"msg_type": "notify", "hosts": self.hosts, "instance_id": None}))

    def do_ehlo(self):
        for host in self.hosts:
            self.write_ehlo(host)

    def write_ehlo(self, uid):
        self.writeMessage(uid, Msg({"msg_type": "ehlo", "instance_id": None}))

    def recv_ehlo(self, msg, instance):
        """Reply to an EHLO message with a NOTIFY message."""
        self.write_notify(msg['uid'])

    def recv_notify(self, msg, instance):
        """Add any hosts we don't know about on receiving a NOTIFY message, and send them EHLOs too."""
        h = msg['hosts']
        for host in self.hosts:
            h.pop(host, None)
        if h:
            for host, addr in h.iteritems():
                self.addHost(host, addr)
                self.write_ehlo(msg['uid'])

    def discoverNetwork(self):
        if self.bootstrap is not None:
            m = Msg({"msg_type": "ehlo", "uid": self.uid, "instance_id": None})
            self.transport.write(m.serialize(), self.bootstrap)

    def addHost(self, uid, host):
        dbprint("Adding node %s (%s)" % (uid, host), level=3)
        self.hosts[uid] = host
        self.quorum_size = (len(self.hosts)+1) // 2


    def writeMessage(self, uid, msg):
        dbprint("Sent %s message to %s\n%s\n" % (msg['msg_type'], uid, msg), level=1)
        msg.contents['uid'] = self.uid
        msg = msg.serialize()
        addr = self.hosts[uid]
        self.transport.write(msg, addr)

    def writeAll(self, msg):
        dbprint("%s sent message %s to all" % (self, msg), level=1)
        for uid in self.hosts:
            self.writeMessage(uid, msg)


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
            dbprint("Got %s message from %s\n%s\n" % (m['msg_type'], host, m), level=1)
            if m['instance_id'] is not None:
                i = m['instance_id']
                if i not in self.instances:
                    if i >= self.current_instance_number:
                        self.current_instance_number = i+1
                    self.instances[i] = self.create_instance(i)
                else:
                    assert i < self.current_instance_number, "known but oddly large instance number %s (%s)" % (i, self.current_instance_number)
                instance = self.instances[i]
                if instance['status'] == 'completed':
                    dbprint("dropping msg as instance %s is already completed" % i, level=2)
                    return
            else:
                instance = None
            method = getattr(self, "recv_%s" % t)
            method(m, instance)
        except (InvalidMessageException, KeyError), e:
            dbprint("%s received invalid message %s (%s)" % (self, msg, e), level=4)
            raise

    def __repr__(self):
        u = getattr(self, "uid", None)
        if u is None:
            u = "Unknown UID"
        return "<Node(%s) @ %#lx>" % (u, id(self))

    def run(self, operation):
        i_num = self.current_instance_number
        self.current_instance_number += 1
        i = self.create_instance(i_num)
        assert i_num not in self.instances, "internal error: %s should not be in instances (%s)" % (
            i_num, self.current_instance_number)
        self.instances[i_num] = i
        self.proposer_start(i, operation)
        return i['callback']
