from pyparsing import CaselessLiteral, Word, Optional, Group, nums, alphanums, oneOf, \
        ZeroOrMore, StringEnd, Or, Suppress, Forward, ParseException as pyPE
from dbp.db import Update, Insert, Delete
from dbp.where import _combinators, _ops, ParseException

# Example syntax
# (SELECT, UPDATE) (values) WHERE (column operator value)
# INSERT (values)
# DELETE WHERE ...
# INSERT (values) SELECT ? probs not.

_operators = ("SELECT", "UPDATE")
operators = Or(CaselessLiteral(o) for o in _operators)
combinators = Or(CaselessLiteral(c) for c in _combinators)

# comma separated values
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
C = Forward()
T = ((stringLit | intLit | w) + oneOf(_ops) + (stringLit | intLit | w)) | (Suppress("(") + C + Suppress(")"))
C << ((T + combinators + T) | T)

bvalues = Group(Suppress("(") + values + Suppress(")"))
svalues = (bvalues | '*').setResultsName("columns")

where_clause = CaselessLiteral("WHERE") + C
where = Optional(where_clause, "").setResultsName("where")

op = operators.setResultsName("op")
sgram = op + svalues + where + StringEnd()
insert = CaselessLiteral("INSERT").setResultsName("op") + bvalues.setResultsName('ivalues') + StringEnd()
delete = CaselessLiteral("DELETE").setResultsName("op") + where + StringEnd()
stmt = sgram | insert | delete


def parse_sql(s):
    d = {'stmt': s}
    try:
        r = stmt.parseString(s)
    except pyPE, e:
        raise ParseException(e)
    o = r.op.lower()
    if o == "insert":
        d['values'] = list(r.ivalues)
        return Insert(d)
    elif o == "select":
        raise NotImplemented()
    elif o == "update":
        # XXX: doesn't work
        d['where_clause'] = r.where
        return Update(d)
    elif o == "delete":
        d['where_clause'] = r.where
        return Delete(d)
    # "columns": r.columns, "where": r.where, }
