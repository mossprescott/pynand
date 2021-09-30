# Compiler I: Syntax Analysis
#
# See https://www.nand2tetris.org/project10

"""On parsers:

nand.parsing provides a collection of primitive parsers which can be assembled into the parsers
you need to implement here. That module includes a tutorial on the basics and documentation for
each combinator.

Each component parser can act as a function taking a parse location and returning a result value
and a new location (if it succeeds). If a parser doesn't recognize the tokens at the given location,
it raises ParseFailure.

Each component parser also provides `parse(tokens)`, which can be called directly to parse a program
fragment.

For example:

>>> KeywordConstantP.parse([('keyword', 'true')])
KeywordConstant(value=True)

>>> ExpressionP.parse([('identifier', 'a'), ('symbol', '+'), ('integerConstant', '1')])
BinaryExpression(left=VarRef(name='a'), op=Op(symbol='+'), right=IntegerConstant(value=1))
"""

from nand.parsing import *
from nand import jack_ast

# SOLVERS: remove this import to get started
from nand.solutions import solved_10

# a label for each token type:
KEYWORD = 'keyword'
SYMBOL = 'symbol'
INT = 'integerConstant'
STR = 'stringConstant'
IDENTIFIER = 'identifier'


def lex(string):
    """Break the text of Jack source code into a list of tokens.

    White space and comments are ignored. Each token is converted to a tuple of (token-type, value).

    >>> lex("a + 1")
    [('identifier', 'a'), ('symbol', '+'), ('integerConstant', '1')]
    """

    # SOLVERS: replace this with code to break the input string into a sequence of tokens
    tokens = solved_10.lex(string)

    return tokens


def parse_class(string):
    """Convenience function which just applies the lexer and then the ClassP parser implemented below.
    """
    return ClassP.parse(lex(string))



#
# Simple Values:
#

# Example: match one of the keywords that represents a simple constant value (or the "this" reference)
KeywordConstantP = (
    TokenP(("keyword", "true"),  jack_ast.KeywordConstant(True))
    | TokenP(("keyword", "false"), jack_ast.KeywordConstant(False))
    | TokenP(("keyword", "null"),  jack_ast.KeywordConstant(None))
    | TokenP(("keyword", "this"),  jack_ast.KeywordConstant("this")))

# SOLVERS: replace this with a parser of jack_ast.Op
UnaryOpP = solved_10.UnaryOpP

# SOLVERS: replace this with a parser of jack_ast.Op
BinaryOpP = solved_10.BinaryOpP

# SOLVERS: replace this with a parser of jack_ast.IntegerConstant
IntegerConstantP = solved_10.IntegerConstantP

# SOLVERS: replace this with a parser of jack_ast.StringConstant
StringConstantP = solved_10.StringConstantP

# SOLVERS: replace this with a parser of jack_ast.VarRef
# Note the name discrepancy: the grammar defines `varName` and uses it twice. The AST has `VarRef` and
# `ArrayRef` for the two cases.
VarNameP = solved_10.VarNameP

#
# Complex Expressions:
#

# Tricky: the grammar for expressions is recursive, so need a way to refer to this parser before
# actually giving its own definition.
ExpressionP = DeferP("ExpressionP")

# SOLVERS: replace this with a parser of jack_ast.ArrayRef
# Note the name discrepancy: the grammar defines `varName` and uses it twice. The AST has `VarRef` and
# `ArrayRef` for the two cases.
VarNameAndArrayIndexP = solved_10.VarNameAndArrayIndexP

# SOLVERS: replace this with a parser of jack_ast.Expression
ExpressionP.set(solved_10.ExpressionP)


#
# Statements:
#

# Tricky: the grammar for statements is recursive, so need a way to refer to this parser before
# actually giving its own definition.
StatementP = DeferP("StatementP")

# SOLVERS: replace this with a parser of jack_ast.DoStatement
DoStatementP = solved_10.DoStatementP

# SOLVERS: replace this with a parser of jack_ast.ReturnStatement
ReturnStatementP = solved_10.ReturnStatementP

# SOLVERS: replace this with a parser of jack_ast.LetStatement
LetStatementP = solved_10.LetStatementP

# SOLVERS: replace this with a parser of jack_ast.IfStatement
IfStatementP = solved_10.IfStatementP

# SOLVERS: replace this with a parser of jack_ast.WhileStatement
WhileStatementP = solved_10.WhileStatementP

StatementP.set(LetStatementP | IfStatementP | WhileStatementP | DoStatementP | ReturnStatementP)

#
# Program Structure:
#

# SOLVERS: replace this with a parser of jack_ast.Type (aka str)
TypeP = solved_10.TypeP

# SOLVERS: replace this with a parser of jack_ast.jack_ast.VarDec
VarDecP = solved_10.VarDecP

# SOLVERS: replace this with a parser of jack_ast.SubroutineDec
SubroutineDecP = solved_10.SubroutineDecP

# SOLVERS: replace this with a parser of jack_ast.ClassVarDec
ClassVarDecP = solved_10.ClassVarDecP

# SOLVERS: replace this with a parser of jack_ast.Class
ClassP = solved_10.ClassP
