from dbp.util import title, dbprint, PaxosException
from dbp.paxos.proposal import Proposal
from ast import literal_eval


class InvalidMessageException(PaxosException):
    """Exception raised if there is an error in the message code"""
    pass


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


class Message(object):
    """Message superclass"""
    msg_type = "message"

    def __init__(self, proposal):
        self.proposal = proposal

    def __str__(self):
        return "%s(%s)" % (title(self.msg_type), self.proposal)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))

    def __eq__(self, other):
        if not isinstance(other, Message):
            return NotImplemented
        return (self.msg_type == other.msg_type and
                self.proposal == other.proposal)

    def __ne__(self, other):
        return not self == other

    def serialize(self):
        """Serialize into a format for on the wire transfer

        This returns a string which can be sent over the network and
        reconstructed by parse_message
        """
        return "%s:%s" % (self.msg_type, self.proposal.serialize())


class Prepare(Message):
    """Prepare message"""
    def __init__(self, proposal):
        super(Prepare, self).__init__(proposal)
        # Add a sanity check that we're not sending a value with our prepare
        # message
        if proposal.value is not None:
            raise InvalidMessageException(
                "Prepare messages cannot contain a value, %s has a non-None value"
                % (proposal))
    msg_type = "prepare"


class Promise(Message):
    """Promise message"""
    msg_type = "promise"


class AcceptRequest(Message):
    """Accept request message"""
    msg_type = "acceptrequest"

class AcceptNotify(Message):
    """Accept notify message"""
    msg_type = "acceptinfo"


# This is a mapping from message types to the actual classes.
# I guess we could handle this with a metaclass or something but it seems less
# magic to just hardcode it, especially as there isn't going to be an explosion
# of message types.
message_types = {
    Prepare.msg_type: Prepare,
    Promise.msg_type: Promise,
    AcceptRequest.msg_type:  AcceptRequest,
    AcceptNotify.msg_type:  AcceptNotify,
}
