network = {}
network_num = {}


def title(s):
    """capitalizes only first character of a string"""
    if len(s) < 2:
        return s.capitalize()
    return s[0].capitalize() + s[1:]


def send(sender, receiver, message):
    """Send a message from sender to receiver"""
    message.transmit(sender, receiver)
    receiver.send(message)


class Proposal(object):
    """Proposal object"""
    def __init__(self, prop_num, value=None):
        super(Proposal, self).__init__()
        self.prop_num = prop_num
        self.value = value

    def __str__(self):
        return "Proposal(%s: %s)" % (self.prop_num, self.value)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))


class Message(object):
    """Message superclass"""
    msg_type = "message"

    def __init__(self, proposal):
        super(Message, self).__init__()
        self.proposal = proposal
        self.sender = None
        self.receiver = None

    def transmit(self, sender, receiver):
        self.sender = sender
        self.receiver = receiver

    def __str__(self):
        if self.sender is None:
            assert(self.receiver is None)
            addr = ""
        else:
            addr = "from %s to %s " % (self.sender, self.receiver)
        return "%s(%s (%s))" % (title(self.msg_type), addr, self.proposal)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))


class Prepare(Message):
    """Prepare message"""
    msg_type = "prepare"


class Promise(Message):
    """Promise message"""
    msg_type = "promise"


class Accept(Message):
    """Accept message"""
    msg_type = "accept"


class Agent(object):
    agent_type = "agent"

    def __init__(self):
        self._msgs = []
        network.setdefault(self.agent_type, []).append(self)
        self._num = network_num.setdefault(self.agent_type, 0)
        network_num[self.agent_type] += 1

    def send(self, msg):
        self._msgs.append(msg)
        self._send(msg)

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

    def _send(self, msg):
        if msg.msg_type == "prepare":
            # (b) If an acceptor receives a prepare request with number n greater than that
            # of any prepare request to which it has already responded, then it responds to
            # the request with a promise not to accept any more proposals numbered less than
            # n and with the highest-numbered proposal (if any) that it has accepted.
            if msg.proposal.prop_num > self._cur_prop_num:
                send(self, msg.sender, Promise(Proposal(msg.proposal.prop_num, self._cur_prop.value)))
                self._cur_prop_num = msg.proposal.prop_num
            else:
                pass  # Can NACK here
        elif msg.msg_type == "accept":
            # (b) If an acceptor receives an accept request for a proposal numbered n , it
            # accepts the proposal unless it has already responded to a prepare request
            # having a number greater than n.
            if msg.proposal.prop_num >= self._cur_prop_num:
                self._cur_prop = msg.proposal
            else:
                pass  # Can NACK here


class Learner(Agent):
    agent_type = "learner"


class Proposer(Agent):
    agent_type = "proposer"

    def __init__(self):
        super(Proposer, self).__init__()
        self.num = 0

    def _send(self, msg):
        self.received.setdefault(msg.proposal.prop_num, []).append(msg)

    def run(self, value):
        # (a) A proposer selects a proposal number n, greater than any proposal number it
        # has selected before, and sends a request containing n to a majority of
        # acceptors. This message is known as a prepare request.
        self.received = {}
        self.num += 1
        n = self.num
        for a in network['acceptor']:
            send(self, a, Prepare(Proposal(n)))

        # (a) If the proposer receives a response to its prepare requests (numbered n)
        # from a majority of acceptors, then it sends an accept request to each of those
        # acceptors for a proposal numbered n with a value v, where v is the value of
        # the highest-numbered proposal among the responses, or if the responses reported
        # no proposals, a value of its own choosing.
        acceptor_num = len(network['acceptor'])
        # if acceptor_num > :
        #     pass
        print self.received


p1 = Proposer()
a1 = Acceptor()
l1 = Learner()
