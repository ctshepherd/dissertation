from paxos.util import title, dbprint
from paxos.proposal import Proposal
from ast import literal_eval


def parse_message(msg):
    """Convert a message from string format to a Python object

    This takes a string (probably received off the network) and returns the
    corresponding Message object.
    """
    mtype, p = msg.split(':')
    pt = p.split(',')  # proposal value tuple
    m = message_types[mtype](
        Proposal(literal_eval(pt[0]),   # literal_eval is a safe version of eval,
                 literal_eval(pt[1])))  # that only works for literal values
    dbprint("converting '%s' to '%s'" % (msg, m), level=1)
    return m


def send(sender, receiver, message):
    """Send a message from sender to receiver"""
    if isinstance(receiver, tuple):
        addr = receiver
    else:
        host = receiver.proto.transport.getHost()
        addr = (host.host, host.port)
    sender.proto.sendDatagram(message.serialize(), addr)


class Message(object):
    """Message superclass"""
    msg_type = "message"

    def __init__(self, proposal):
        super(Message, self).__init__()
        self.proposal = proposal

    def __str__(self):
        return "%s(%s)" % (title(self.msg_type), self.proposal)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))

    def serialize(self):
        """Serialize into a format for on the wire transfer

        This returns a string which can be sent over the network and
        reconstructed by parse_message
        """
        return "%s:%s" % (self.msg_type, self.proposal.serialize())


class Prepare(Message):
    """Prepare message"""
    msg_type = "prepare"


class Promise(Message):
    """Promise message"""
    msg_type = "promise"


class Accept(Message):
    """Accept message"""
    msg_type = "accept"


# This is a mapping from message types to the actual classes.
# I guess we could handle this with a metaclass or something but it seems less
# magic to just hardcode it, especially as there isn't going to be an explosion
# of message types.
message_types = {
    Prepare.msg_type: Prepare,
    Promise.msg_type: Promise,
    Accept.msg_type:  Accept,
}
