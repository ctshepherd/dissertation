from pyparsing import Literal, CaselessLiteral, Word, Upcase, delimitedList, Optional, \
        Combine, Group, alphas, nums, alphanums, ParseException, Forward, oneOf, quotedString, \
        ZeroOrMore, restOfLine, Keyword, StringEnd, Or, Suppress

# Example syntax
# (SELECT, DELETE, UPDATE) (values) WHERE (column operator value)

operators = ("SELECT", "DELETE", "UPDATE")
combinators = ("AND", "OR")

w = Word(alphas)
c = Suppress(",")
values = w + ZeroOrMore(c + w)

#operators = (Literal(x) for x in ("<", ">", "==", "!="))
stringLit = Group('"' + w + '"').setResultsName("strrhs")
intLit = Word(nums).setResultsName("intrhs")
condition = w.setResultsName("fieldname") + oneOf("< > == !=").setResultsName("cmp") + (stringLit | intLit).setResultsName("rhs")
boolean = condition
#boolean = condition + ZeroOrMore(c + w)

values = (Group(Suppress("(") + values + Suppress(")")) | '*').setResultsName("columns")

where_clause = CaselessLiteral("WHERE") + "(" + boolean + ")"
where = Optional(where_clause, "").setResultsName("where")

op = Or(CaselessLiteral(o) for o in operators).setResultsName("op")
stmt = op + values + where + StringEnd()

# selectStmt << ( selectToken +
#               ( '*' | columnNameList ).setResultsName( "columns" ) +
#               fromToken +
#               tableNameList.setResultsName( "tables" ) +
#               Optional( Group( CaselessLiteral("where") + whereExpression ),
#                                                    "" ).setResultsName("where") )
