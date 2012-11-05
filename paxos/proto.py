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


class Message(object):
    """Message superclass"""
    def __init__(self, proposal):
        super(Message, self).__init__()
        self.proposal = proposal
        self.sender = None
        self.receiver = None

    def transmit(self, sender, receiver):
        self.sender = sender
        self.receiver = receiver


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
    def __init__(self):
        self._msgs = []

    def send(self, msg):
        self._msgs.append(msg)
        self._send()


class Acceptor(Agent):
    """Acceptor Agent"""
    def __init__(self):
        super(Acceptor, self).__init__()
        self._cur_prop_num = 0
        self._cur_prop = Proposal(0)

    def _send(self, msg):
        if msg.msg_type == "prepare":
            if msg.proposal.prop_num > self._cur_prop_num:
                send(msg.sender, self, Promise(Proposal(msg.proposal.prop_num, self._cur_prop.value)))
                self._cur_prop_num = msg.proposal.prop_num
            else:
                pass  # Can NACK here
        elif msg.msg_type == "accept":
            if msg.proposal.prop_num >= self._cur_prop_num:
                self._cur_prop = msg.proposal
            else:
                pass  # Can NACK here

"""
(b) If an acceptor receives a prepare request with number n greater than that
of any prepare request to which it has already responded, then it responds to
the request with a promise not to accept any more proposals numbered less than
n and with the highest-numbered proposal (if any) that it has accepted.
"""

"""
(b) If an acceptor receives an accept request for a proposal numbered n , it
accepts the proposal unless it has already responded to a prepare request
having a number greater than n.
"""


class Learner(Agent):
    pass


class Proposer(Agent):
    def run_prepare_phase():
        """
    (a) A proposer selects a proposal number n, greater than any proposal number it
    has selected before, and sends a request containing n to a majority of
    acceptors. This message is known as a prepare request.
    """
    def run_commit_phase():
        """
(a) If the proposer receives a response to its prepare requests (numbered n)
from a majority of acceptors, then it sends an accept request to each of those
acceptors for a proposal numbered n with a value v, where v is the value of
the highest-numbered proposal among the responses, or if the responses reported
no proposals, a value of its own choosing.
"""
    def run():
        pass
