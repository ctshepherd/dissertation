from dbp.util import PaxosException
from ast import literal_eval


class InvalidMessageException(PaxosException):
    """Exception raised if there is an error in the message code"""
    pass


def parse_message(msg):
    """Convert a message from string format to a Python object

    This takes a string (probably received off the network) and returns the
    corresponding Message object.
    """
    try:
        # literal_eval is a safe version of eval
        d = literal_eval(msg)
        return Msg(d)
    except SyntaxError, e:
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

    def __getitem__(self, item):
        return self.contents[item]

    def __getattr__(self, n):
        if n in self.contents:
            return self.contents[n]
        return object.__getattribute__(self, n)

    def serialize(self):
        """Serialize into a format for on the wire transfer

        This returns a string which can be sent over the network and
        reconstructed by parse_message.
        """
        return str(self.contents)
