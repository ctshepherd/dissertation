from util import title
from proposal import Proposal
from ast import literal_eval


def parse_message(msg):
    mtype, p = msg.split(':')
    pt = p.split(',')
    m = message_types[mtype](Proposal(literal_eval(pt[0]), literal_eval(pt[1])))
    print "converting '%s' to '%s'" % (msg, m)
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
        if self.sender is None:
            assert(self.receiver is None)
            addr = ""
        else:
            addr = "from %s to %s " % (self.sender, self.receiver)
        return "%s(%s (%s))" % (title(self.msg_type), addr, self.proposal)

    def serialize(self):
        return "%s:%s" % (self.msg_type, self.proposal.serialize())

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

message_types = {
    Prepare.msg_type: Prepare,
    Promise.msg_type: Promise,
    Accept.msg_type:  Accept,
}
