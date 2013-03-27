import operator
from ast import literal_eval
from pyparsing import CaselessLiteral, Word, Optional, Group, nums, alphanums, oneOf, \
        ZeroOrMore, StringEnd, Or, Suppress

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

stringLit = Group('"' + w + '"')
intLit = Word(nums)
condition = (stringLit | intLit | w) + oneOf("< > == !=") + (stringLit | intLit | w)
boolean = condition + ZeroOrMore(combinators + condition)

values = (Group(Suppress("(") + values + Suppress(")")) | '*').setResultsName("columns")

where_clause = CaselessLiteral("WHERE") + "(" + boolean + ")"
where = Optional(where_clause, "").setResultsName("where")

op = operators.setResultsName("op")
stmt = op + values + where + StringEnd()


class FieldTest(object):
    """Test a field to see if it satisfies a WHERE clause"""

class FieldCmpTest(FieldTest):
    """Test a field to see if it satisfies a condition"""

    op_mapping = {
        "<": operator.lt,
        ">": operator.gt,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, lhs, op, rhs):
        self.lhs_is_field, self.lhs = self.field_transform(lhs)
        self.op = self.op_mapping[op]
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


class FieldCombine(object):
    """Combine two WHERE clauses"""
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def test_row(self, schema, row):
        return self.combine(self.a.test_row(schema, row), self.a.test_row(schema, row))

    def combine(self, a, b):
        raise NotImplementedError()


class FieldAnd(FieldCombine):
    """Boolean And of two WHERE clauses"""
    combine = staticmethod(lambda a,b: a and b)


class FieldOr(FieldCombine):
    """Boolean Or of two WHERE clauses"""
    combine = staticmethod(lambda a,b: a or b)


def parse_sql(s):
    r = stmt.parseString(s)
    return {
            "op": r.op,
            "columns": r.columns,
            "where": r.where,
            }

def parse_where(s):
    pass
