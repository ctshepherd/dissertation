from dbp.util import dbprint, PaxosException
from dbp.paxos.proposal import Proposal
from ast import literal_eval


class InvalidMessageException(PaxosException):
    """Exception raised if there is an error in the message code"""
    pass


def lm(msg):
    mtype, p = msg.split(':')
    pt = p.split(',')  # proposal value tuple
    m = message_types[mtype](
        Proposal(literal_eval(pt[0]),   # literal_eval is a safe version of eval,
                 literal_eval(pt[1])))  # that only works for literal values
    dbprint("converting '%s' to '%s'" % (msg, m), level=1)
    return m.serialize()


def parse_message(msg):
    """Convert a message from string format to a Python object

    This takes a string (probably received off the network) and returns the
    corresponding Message object.
    """
    try:
        # literal_eval is a safe version of eval
        d = literal_eval(msg)
        if 'proposal' in d:
            pt = d['proposal'].split(',')  # proposal value tuple
            d['proposal'] = Proposal(literal_eval(pt[0]), literal_eval(pt[1]))
        return Msg(d)
    except (SyntaxError, ValueError, KeyError), e:
        raise InvalidMessageException("invalid msg '%s' (%r)" % (msg, e))


class Msg(object):
    """Message container"""

    def __init__(self, contents):
        self.contents = contents

    def __str__(self):
        return "Msg(%s)" % (self.contents)

    def __repr__(self):
        return "<%s @ %#lx>" % (self, id(self))

    def __eq__(self, other):
        if not isinstance(other, Msg):
            return NotImplemented
        return self.contents == other.contents

    def __ne__(self, other):
        return not self == other

    def __getattr__(self, n):
        if n in self.contents:
            return self.contents[n]
        return object.__getattr__(self, n)

    def serialize(self):
        """Serialize into a format for on the wire transfer

        This returns a string which can be sent over the network and
        reconstructed by parse_message.
        """
        return str(self.contents)


class LegacyMessage(Msg):
    def __init__(self, proposal):
        d = {'msg_type': self.msg_type,
             'proposal': proposal,
             }
        Msg.__init__(self, d)

    def serialize(self):
        p = self.contents['proposal']
        self.contents['proposal'] = self.contents['proposal'].serialize()
        ret = Msg.serialize(self)
        self.contents['proposal'] = p
        return ret


class Prepare(LegacyMessage):
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


class Promise(LegacyMessage):
    """Promise message"""
    msg_type = "promise"


class AcceptRequest(LegacyMessage):
    """Accept request message"""
    msg_type = "acceptrequest"


class AcceptNotify(LegacyMessage):
    """Accept notify message"""
    msg_type = "acceptnotify"


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
