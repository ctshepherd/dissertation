from paxos.network import network, network_num, hosts
from paxos.util import title, dbprint
from paxos.message import Accept, Promise, Prepare, send, parse_message, InvalidMessageException
from paxos.proposal import Proposal
from paxos.protocol import EchoClientDatagramProtocol, reactor


class Agent(object):
    agent_type = "agent"

    def __init__(self):
        self._msgs = []
        network.setdefault(self.agent_type, []).append(self)
        self._num = network_num.setdefault(self.agent_type, 1)
        self.proto = EchoClientDatagramProtocol()
        self.proto.parent = self
        reactor.listenUDP(0, self.proto)  # this returns self.proto.transport
        hosts[self.proto.transport.getHost().port] = self
        network_num[self.agent_type] += 1

    def receive(self, msg, host):
        """Called when a message is received by a specific agent.

        """
        host = hosts[host[1]]
        dbprint("%s got message %s from %s" % (self, msg, host), level=2)
        self._msgs.append((msg, host))
        try:
            m = parse_message(msg)
        except InvalidMessageException, e:
            dbprint("%s received invalid message %s (%s)" % (self, msg, e))
            return
        self._receive(m, host)

    def _receive(self, msg, host):
        raise NotImplementedError()

    def __str__(self):
        return "%s(%s)" % (title(self.agent_type), self._num)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))


class Acceptor(Agent):
    """Acceptor Agent"""
    agent_type = "acceptor"

    def __init__(self):
        super(Acceptor, self).__init__()
        self._cur_prop_num = 0
        self._cur_prop = Proposal(0)

    def _receive(self, msg, host):
        if msg.msg_type == "prepare":
            # (b) If an acceptor receives a prepare request with number n greater than that
            # of any prepare request to which it has already responded, then it responds to
            # the request with a promise not to accept any more proposals numbered less than
            # n and with the highest-numbered proposal (if any) that it has accepted.
            if msg.proposal.value is not None:
                # Sanity check - prepare messages should not have a value
                dbprint("Warning: %s received a Prepare message %s with an unexpected value"
                        % (self, msg), level=5)
                return
            if msg.proposal.prop_num > self._cur_prop_num:
                send(self, host, Promise(Proposal(msg.proposal.prop_num, self._cur_prop.value)))
                self._cur_prop_num = msg.proposal.prop_num
                self._cur_prop = msg.proposal
            else:
                pass  # Can NACK here
        elif msg.msg_type == "accept":
            # (b) If an acceptor receives an accept request for a proposal numbered n, it
            # accepts the proposal unless it has already responded to a prepare request
            # having a number greater than n.
            if msg.proposal.prop_num >= self._cur_prop_num:
                dbprint("Accepting proposal %s (%s)" % (msg.proposal.prop_num, self._cur_prop_num))
                self._cur_prop = msg.proposal
                for l in network['learner']:
                    send(self, l, Accept(msg.proposal))
            else:
                pass  # Can NACK here


class Learner(Agent):
    agent_type = "learner"

    def __init__(self):
        super(Learner, self).__init__()
        self.received_proposals = {}
        self.accepted_proposals = {}

    def _receive(self, msg, host):
        acceptor_num = len(network['acceptor'])
        if msg.msg_type == "accept":
            # if we've already learnt it's been accepted, there's no need to
            # deal with it any more
            if msg.proposal.prop_num in self.accepted_proposals:
                return
            p = self.received_proposals.setdefault(msg.proposal.prop_num, {})
            s = p.setdefault(msg.proposal.value, set())
            s.add(host)
            if len(s) > acceptor_num/2:
                self.accepted_proposals[msg.proposal.prop_num] = msg.proposal.value
                dbprint("Proposal %s accepted" % msg.proposal, level=3)


class Proposer(Agent):
    agent_type = "proposer"

    def __init__(self):
        super(Proposer, self).__init__()
        self.cur_prop_num = 0
        self.accepted = False
        self.replies = []
        self.cur_value = None
        self.received = {}

    def _receive(self, msg, host):
        if msg.msg_type == "promise":
            self.received.setdefault(msg.proposal.prop_num, []).append((msg, host))

            # (a) If the proposer receives a response to its prepare requests (numbered n)
            # from a majority of acceptors, then it sends an accept request to each of those
            # acceptors for a proposal numbered n with a value v, where v is the value of
            # the highest-numbered proposal among the responses, or if the responses reported
            # no proposals, a value of its own choosing.
            acceptor_num = len(network['acceptor'])
            if not self.accepted and len(self.received.get(self.cur_prop_num, ())) > acceptor_num/2:
                self.accepted = True
                competing = max(self.received[self.cur_prop_num])
                dbprint("Proposal %s accepted", self.cur_prop_num)
                for (m, acceptor) in self.received.get(self.cur_prop_num, ()):
                    send(self, acceptor, Accept(msg.proposal))
            elif self.accepted:
                send(self, host, Accept(msg.proposal))

    def run(self, value):
        # (a) A proposer selects a proposal number n, greater than any proposal number it
        # has selected before, and sends a request containing n to a majority of
        # acceptors. This message is known as a prepare request.
        self.received = {}
        self.cur_prop_num += self._num
        n = self.cur_prop_num
        self.cur_value = value
        for a in network['acceptor']:
            send(self, a, Prepare(Proposal(n, value)))
