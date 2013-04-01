import operator
from ast import literal_eval
from pyparsing import CaselessLiteral, Word, Optional, Group, nums, alphanums, oneOf, \
        ZeroOrMore, StringEnd, Or, Suppress, Forward

class ParseException(Exception):
    """Parser error"""

# Example syntax
# (SELECT, DELETE, UPDATE) (values) WHERE (column operator value)
# INSERT (values)
# INSERT (values) SELECT ? probs not.

_operators = ("SELECT", "DELETE", "UPDATE")
operators = Or(CaselessLiteral(o) for o in _operators)
_combinators = ("AND", "OR")
combinators = Or(CaselessLiteral(c) for c in _combinators)

w = Word(alphanums)
c = Suppress(",")
values = w + ZeroOrMore(c + w)

# Grammar:
# B -> AND | OR
# T -> f op f | ( C )
# C -> T B T | T
# S -> WHERE C EOF

stringLit = Group('"' + w + '"')
intLit = Word(nums)
_ops = "< > == != <= >=".split()
C = Forward()
T = ((stringLit | intLit | w) + oneOf(_ops) + (stringLit | intLit | w)) | (Suppress("(") + C + Suppress(")"))
C << ((T + combinators + T) | T)

values = (Group(Suppress("(") + values + Suppress(")")) | '*').setResultsName("columns")

where_clause = CaselessLiteral("WHERE") + C
where = Optional(where_clause, "").setResultsName("where")

op = operators.setResultsName("op")
stmt = op + values + where + StringEnd()


class FieldTest(object):
    """Test a field to see if it satisfies a WHERE clause"""
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self)

class FieldCmpTest(FieldTest):
    """Test a field to see if it satisfies a condition"""

    op_mapping = {
        "<": operator.lt,
        ">": operator.gt,
        "<=": operator.le,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, lhs, op, rhs):
        self.lhs_is_field, self.lhs = self.field_transform(lhs)
        self.op = self.op_mapping[op]
        self.op_str = op
        self.rhs_is_field, self.rhs = self.field_transform(rhs)

    def test_row(self, schema, row):
        if self.lhs_is_field:
            lhs = self.fetch_field(schema, row, self.lhs)
        else:
            lhs = self.lhs

        if self.rhs_is_field:
            rhs = self.fetch_field(schema, row, self.rhs)
        else:
            rhs = self.rhs

        return self.op(lhs, rhs)

    @staticmethod
    def fetch_field(schema, row, field_name):
        i = schema.index(field_name)
        return row[i]

    @staticmethod
    def field_transform(v):
        """Decide if v is a literal or a field name"""
        try:
            # If literal_eval can parse it, it's a string/int (these are the only things allowed
            # by the grammar
            return False, literal_eval(v)
        except ValueError:
            # Must be a field name (hopefully)
            return True, v

    def __str__(self):
        return "%s %s %s" % (self.lhs, self.op_str, self.rhs)


class FieldCombine(FieldTest):
    """Combine two WHERE clauses"""

    op = ""

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def test_row(self, schema, row):
        return self.combine(self.a.test_row(schema, row), self.a.test_row(schema, row))

    def combine(self, a, b):
        raise NotImplementedError()

    def __str__(self):
        return "%s %s %s" % (self.a, self.op, self.b)


class FieldAnd(FieldCombine):
    """Boolean And of two WHERE clauses"""
    combine = staticmethod(lambda a,b: a and b)
    op = "AND"


class FieldOr(FieldCombine):
    """Boolean Or of two WHERE clauses"""
    combine = staticmethod(lambda a,b: a or b)
    op = "OR"


def parse_sql(s):
    r = stmt.parseString(s)
    return {
            "op": r.op,
            "columns": r.columns,
            "where": parse_where(r.where),
            }


class WhereParser(object):
    """Recursive descent parser for WHERE clauses"""

    # Grammar:
    # B -> AND | OR
    # T -> f op f | ( C )
    # C -> T B T | T
    # S -> WHERE C EOF

    _digits = set("1234567890")

    def __init__(self, next_token):
        self.next_token = next_token
        self.token = next_token()

    def mk_eof(self):
        if self.token is not None:
            raise ParseException("expected end of token, got %r" % self.token)

    def advance(self):
        t = self.token
        try:
            self.token = self.next_token()
        except StopIteration:
            self.token = None
        return t

    def mk_B(self):
        t = self.advance()
        if t in _combinators:
            return t
        raise ParseException("%r not a combinator" % t)

    def mk_F(self):
        t = self.advance()
        if set(t) <= self._digits:
            t = int(t)
        return t

    def mk_op(self):
        op = self.advance()
        if op in _ops:
            return op
        raise ParseException("%r not an operation" % op)

    def mk_T(self):
        if self.token == '(':
            self.advance()
            r = self.mk_C()
            t = self.advance()
            if t != ")":
                raise ParseException("badly bracketed token string")
            return r
        lhs = self.mk_F()
        op = self.mk_op()
        rhs = self.mk_F()
        return FieldCmpTest(lhs, op, rhs)

    def mk_C(self):
        lhs = self.mk_T()
        if self.token not in _combinators:
            return lhs
        comb = self.mk_B()
        rhs = self.mk_T()
        if comb == "AND":
            return FieldAnd(lhs, rhs)
        elif comb == "OR":
            return FieldOr(lhs, rhs)

    def mk_S(self):
        w = self.advance()
        if w != "WHERE":
            raise ParseException("clause should start with WHERE, got %r" % w)
        r = self.mk_C()
        self.mk_eof()
        return r


def parse_where(l):
    if not l:
        return None
    i = iter(l)
    p = WhereParser(i.next)
    return p.mk_S()
