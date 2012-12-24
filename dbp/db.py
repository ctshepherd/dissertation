"""DB module.

This module contains the DB class, the backing store for all our operations. At
the moment it only supports get and set operations but will support more later.
"""

from paxos.util import dbprint


class InvalidOp(Exception):
    """Invalid serialization of an Op"""


class Op(object):
    """Database operation"""
    op_name = "op"
    args = None

    def __init__(self, s, args):
        self.statement = s
        self.args = args

    def perform_op(self, db):
        raise NotImplementedError("perform_op: %s" % self)

    def __str__(self):
        return "%s(%s)" % (self.op_name, self.args)

    def __repr__(self):
        return "<%s @ %#lx>" % (str(self), id(self))

    def __eq__(self, other):
        if not isinstance(other, Op):
            return NotImplemented
        return (self.op_name == other.op_name and
                self.args    == other.args)

    def __ne__(self, other):
        return not self == other


class NOP(Op):
    """NOP operation - does nothing."""
    op_name = "nop"
    num_args = 0

    def __init__(self, s, args):
        super(NOP, self).__init__(s, args)

    def perform_op(self, db):
        pass


class Get(Op):
    """Get operation - get an attribute from a DB"""
    op_name = "get"
    num_args = 1

    def __init__(self, s, args):
        super(Get, self).__init__(s, args)
        self.key = self.args[0]

    def perform_op(self, db):
        return db.get(self.key)


class Set(Op):
    """Set operation - set an attribute on a DB"""
    op_name = "set"
    num_args = 2

    def __init__(self, s, args):
        super(Set, self).__init__(s, args)
        self.key, self.value = self.args

    def perform_op(self, db):
        return db.set(self.key, self.value)


ops = {
    NOP.op_name: NOP,
    Get.op_name: Get,
    Set.op_name: Set,
}


def parse_op(s):
    """Parse a string containing an op serialization and return an Op class.

    Raises InvalidOp if s is not a valid op.
    """
    try:
        op_name = s[:3]
        kls = ops[op_name]
        paran = s[3:]
        if paran[0] != '(' or paran[-1] != ')':
            raise InvalidOp(s)
        p_args = paran[1:-1]
        if not p_args:
            args = []
        else:
            args = p_args.split(',')
        if len(args) != kls.num_args:
            raise InvalidOp(s)
        return kls(s, args)
    except (KeyError, IndexError):
        raise InvalidOp(s)


class DB(object):
    """Database backing store class"""
    def __init__(self, start=()):
        self._db = dict(start)

    def set(self, key, val):
        """Set a key in the database to equal val."""
        dbprint("setting %s to %s" % (key, val), level=1)
        self._db[key] = val

    def get(self, key):
        """Return the value of key in the database. Raises a KeyError if key does not exist."""
        dbprint("getting key %s" % key, level=1)
        return self._db[key]
