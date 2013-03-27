from pyparsing import Literal, CaselessLiteral, Word, Upcase, delimitedList, Optional, \
        Combine, Group, alphas, nums, alphanums, ParseException, Forward, oneOf, quotedString, \
        ZeroOrMore, restOfLine, Keyword, StringEnd, Or, Suppress

# Example syntax
# (SELECT, DELETE, UPDATE) (values) WHERE (column operator value)
# INSERT (values)
# INSERT (values) SELECT ? probs not.

_operators = ("SELECT", "DELETE", "UPDATE")
operators = Or(CaselessLiteral(o) for o in _operators)
_combinators = ("AND", "OR")
combinators = Or(CaselessLiteral(c) for c in _combinators)

w = Word(alphas)
c = Suppress(",")
values = w + ZeroOrMore(c + w)

stringLit = Group('"' + w + '"').setResultsName("strrhs")
intLit = Word(nums).setResultsName("intrhs")
condition = w.setResultsName("fieldname") + oneOf("< > == !=").setResultsName("cmp") + (stringLit | intLit).setResultsName("rhs")
boolean = condition + ZeroOrMore(combinators + condition)

values = (Group(Suppress("(") + values + Suppress(")")) | '*').setResultsName("columns")

where_clause = CaselessLiteral("WHERE") + "(" + boolean + ")"
where = Optional(where_clause, "").setResultsName("where")

op = operators.setResultsName("op")
stmt = op + values + where + StringEnd()
