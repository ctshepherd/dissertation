"""DB module.

This module contains the DB class, the backing store for all our operations. At
the moment it only supports get and set operations but will support more later.
"""

from dbp.util import dbprint
from dbp.config import DB_SCHEMA as SCHEMA
from dbp.where import parse_where


class InvalidOp(Exception):
    """Invalid serialization of an Op"""


class InvalidSchemaException(Exception):
    """Invalid Schema specified"""


class Op(object):
    """Database operation"""
    op_name = "op"

    def __init__(self, args):
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

    def serialize(self):
        d = dict(self.args)
        d['type'] = "db_op"
        d['op_name'] = self.op_name
        return d


class NOP(Op):
    """NOP operation - does nothing."""
    op_name = "nop"

    def perform_op(self, db):
        pass


class Update(Op):
    """Change some rows in the database"""
    op_name = "update"

    def perform_op(self, db):
        w = parse_where(self.args['where_clause'])
        # Store changes in update, then apply them after (because we don't want
        # to modify the dict while we iterate over it)
        update = {}
        for key, row in db.rows.iteritems():
            if w.match(row):
                update[key] = self.change(row)
        db.rows.update(update)


class Insert(Op):
    """Insert some rows in the database"""
    op_name = "insert"

    def perform_op(self, db):
        db.insert(self.args['values'])


class Delete(Op):
    op_name = "delete"

    def perform_op(self, db):
        # Store rows to be deleted in delete, then apply them after (because we
        # don't want to modify the dict while we iterate over it)
        delete = []
        if 'where_clause' not in self.args:
            db.rows = {}
        for key, row in db.rows.iteritems():
            if self.args['where_clause'].match(row):
                delete.append(key)
        for key in delete:
            del db.rows[key]


ops = {
    NOP.op_name: NOP,
    Update.op_name: Update,
    Insert.op_name: Insert,
    Delete.op_name: Delete,
}


def parse_op(d):
    """Parse a string containing an op serialization and return an Op class.

    Raises InvalidOp if s is not a valid op.
    """
    try:
        args = {}
        op_name = d['op_name']
        kls = ops[op_name]
        args['stmt'] = d['stmt']
        args['where'] = d.get('where')
        args['values'] = d.get('values')
        return kls(args)
    except KeyError:
        raise InvalidOp(d)


class DB(object):
    """Database backing store class"""
    def __init__(self, schema=None):
        """Initialise DB object.

        schema - database schema, taken from db.config.SCHEMA if none is specified
        """
        self.rows = {} # integer pk : row values
        if schema is None:
            schema = SCHEMA
        if not schema:
            raise InvalidSchemaException("Need to specify a valid schema!")
        self.schema = schema

    def insert(self, values):
        """Insert a new row, values, into the DB.

        Raises InvalidOp if values doesn't conform to self.schema and inserts
        an automatic primary key if necessary.
        """
        if not self.check_schema(values):
            raise InvalidOp(values)
        if len(values) == len(self.schema)+1:
            pk = values[0]
            values = values[1:]
        else:
            pk = self.auto_pk()
        self.rows[pk] = values


    def check_schema(self, values):
        """Check whether values conforms to self.schema.

        Returns True if values is conforming, False if not.
        """
        if len(values) != len(self.schema):
            # We can specify the primary key too
            if len(values) != len(self.schema) + 1:
                return False

            # First val should be an int
            try:
                pk = int(values[0])
            except ValueError:
                return False
            # And should be unique
            if pk in self.rows:
                return False

        # That's all the constraints
        return True

    def auto_pk(self):
        """Return a new primary key that is unique"""
        if not self.rows:
            return 1
        return max(self.rows)+1
