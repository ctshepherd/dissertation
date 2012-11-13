from util import title


def send(sender, receiver, message):
    """Send a message from sender to receiver"""
    message.transmit(sender, receiver)
    receiver.send(message)


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
