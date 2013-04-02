from pyparsing import CaselessLiteral, Word, Optional, Group, nums, alphanums, oneOf, \
        ZeroOrMore, StringEnd, Or, Suppress, Forward
from dbp.db import Update, Insert, Delete
from dbp.where import _combinators, _ops, _operators

# Example syntax
# (SELECT, DELETE, UPDATE) (values) WHERE (column operator value)
# INSERT (values)
# INSERT (values) SELECT ? probs not.

operators = Or(CaselessLiteral(o) for o in _operators)
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
stmt = sgram | insert


def parse_sql(s):
    d = {'stmt': s}
    r = stmt.parseString(s)
    o = r.op.lower()
    if o == "insert":
        d['values'] = r.ivalues
        return Insert(d)
    elif o == "select":
        pass
    elif o == "update":
        # XXX: doesn't work
        d['where_clause'] = r.where
        return Update(d)
    elif o == "delete":
        d['where_clause'] = r.where
        return Delete(d)
    # "columns": r.columns, "where": r.where, }
