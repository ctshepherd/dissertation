from dbp.util import dbprint
from dbp.paxos.network import port_map
from dbp.paxos.message import AcceptNotify, AcceptRequest, Promise, Prepare, parse_message, InvalidMessageException
from dbp.paxos.proposal import Proposal
from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol


class AgentProtocol(DatagramProtocol):
    agent_type = "agent"

    def stopProtocol(self):
        """
        Stop protocol: reset state variables.
        """

    def startProtocol(self):
        """
        Upon start, reset internal state.
        """
        self.transport.joinGroup("224.0.0.1")
        self._msgs = []
        self.discoverNetwork()
        # network.setdefault(self.agent_type, []).append(self)
        # self._num = network_num.setdefault(self.agent_type, 1)
        # reactor.listenUDP(0, self.proto)  # this returns self.proto.transport

    def discoverNetwork(self):
        self.network = {
            "acceptor": [],
            "proposer": [],
            "learner":  [],
        }

    def writeMessage(self, msg, addr):
        dbprint("%s sent message %s to %s" % (self, msg, addr), level=2)
        msg = msg.serialize()
        self.transport.write(msg, addr)

    def writeAll(self, msg, agent_type):
        dbprint("%s sent message %s to all %s" % (self, msg, agent_type), level=2)
        host = port_map[agent_type]
        msg = msg.serialize()
        self.transport.write(msg, (host, 8005))

    def datagramReceived(self, msg, host):
        """Called when a message is received by a specific agent.

        """
        dbprint("%s got message %s from %s" % (self, msg, host), level=2)
        self._msgs.append((msg, host))
        try:
            m = parse_message(msg)
            self._receive(m, host)
        except InvalidMessageException, e:
            dbprint("%s received invalid message %s (%s)" % (self, msg, e))
            return

    def _receive(self, msg, host):
        raise NotImplementedError()

    # def __str__(self):
    #     return "%s" % (title(self.agent_type), self._num)

    def __repr__(self):
        return "<%s @ %#lx>" % (self.agent_type, id(self))


class AcceptorProtocol(AgentProtocol):
    """Acceptor Agent"""
    agent_type = "acceptor"

    def startProtocol(self):
        AgentProtocol.startProtocol(self)
        self.transport.joinGroup(port_map[self.agent_type])
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
                self.writeMessage(Promise(Proposal(msg.proposal.prop_num, self._cur_prop.value)), host)
                self._cur_prop_num = msg.proposal.prop_num
                self._cur_prop = msg.proposal
            else:
                pass  # Can NACK here
        elif msg.msg_type == "acceptrequest":
            # (b) If an acceptor receives an accept request for a proposal numbered n, it
            # accepts the proposal unless it has already responded to a prepare request
            # having a number greater than n.
            if msg.proposal.prop_num >= self._cur_prop_num:
                dbprint("Accepting proposal %s (%s)" % (msg.proposal.prop_num, self._cur_prop_num))
                self._cur_prop = msg.proposal
                self.writeAll(AcceptNotify(msg.proposal), "learner")
            else:
                pass  # Can NACK here


class LearnerProtocol(AgentProtocol):
    agent_type = "learner"

    def startProtocol(self):
        AgentProtocol.startProtocol(self)
        self.transport.joinGroup(port_map[self.agent_type])
        self.received_proposals = {}
        self.accepted_proposals = {}

    def _receive(self, msg, host):
        acceptor_num = len(self.network['acceptor'])
        if msg.msg_type == "acceptnotify":
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


class ProposerProtocol(AgentProtocol):
    agent_type = "proposer"

    def startProtocol(self):
        AgentProtocol.startProtocol(self)
        self.transport.joinGroup(port_map[self.agent_type])
        self.cur_prop_num = 0
        self.accepted = False
        self.replies = []
        self.cur_value = None
        self.received = {}

        self.d = None

    def _receive(self, msg, host):
        if msg.msg_type == "promise":
            # {prop num -> [(msg, host)]}
            self.received.setdefault(msg.proposal.prop_num, []).append((msg, host))

            # (a) If the proposer receives a response to its prepare requests (numbered n)
            # from a majority of acceptors, then it sends an accept request to each of those
            # acceptors for a proposal numbered n with a value v, where v is the value of
            # the highest-numbered proposal among the responses, or if the responses reported
            # no proposals, a value of its own choosing.
            acceptor_num = len(self.network['acceptor'])
            if not self.accepted and len(self.received.get(self.cur_prop_num, ())) > acceptor_num/2:
                # If this is the message that tips us over the edge and we
                # finally accept the proposal, deal with it appropriately.
                self.accepted = True
                competing = max(self.received[self.cur_prop_num], key=lambda t: t[0].proposal.prop_num)
                dbprint("Proposal %s accepted" % self.cur_prop_num)
                self.d.callback(True)
                if competing is None:
                    # if no-one else asserted a value, we can set ours
                    value = self.cur_value
                else:
                    # otherwise, we need to restart
                    value = competing[0].proposal.value
                for (m, acceptor) in self.received.get(self.cur_prop_num, ()):
                    self.writeMessage(AcceptRequest(Proposal(msg.proposal.prop_num, value)), acceptor)
            elif self.accepted:
                # If we've already accepted the proposal, notify the acceptor
                # to deal with it
                self.writeMessage(AcceptRequest(Proposal(msg.proposal.prop_num, self.cur_value)), host)

    def run(self, value):
        # (a) A proposer selects a proposal number n, greater than any proposal number it
        # has selected before, and sends a request containing n to a majority of
        # acceptors. This message is known as a prepare request.
        self.received = {}
        self.d = defer.Deferred()
        #self.cur_prop_num += self._num
        self.cur_prop_num += 5
        n = self.cur_prop_num
        self.cur_value = value
        self.writeAll(Prepare(Proposal(n)), "acceptor")
        return self.d
