import re
from typing import Sequence

from nand import jack_ast
from nand.parsing import *

# integerConstant: a decimal number in the range 0 ... 32767
# stringConstant: '"', a sequence of Unicode characters, not including double quote or newline, '"'
# identifier: a sequence of letters, digits, and underscore ( '_' ) not starting with a digit.

def lex(string):
    # This is simple and requires no additional packages, but there are more elegant ways to get
    # this job done.

    keywords = set([
        "class", "constructor", "function",
        "method", "field", "static", "var", "int",
        "char", "boolean", "void", "true", "false",
        "null", "this", "let", "do", "if", "else",
        "while", "return",
    ])
    symbols = set("'{}()[].,;+-*/&|<>=~")

    tokens = []

    while string != "":
        m = re.match(r"^([0-9]+)", string)
        if m is not None:
            token_str = m.group(1)
            int_val = int(token_str)
            if not (0 <= int_val <= 32767):
                raise Exception(f"Integer constant out of range: {int_val}")
            tokens.append(("integerConstant", token_str))
            string = string[len(token_str):]
            continue

        m = re.match(r'^"([^"\n]*)"', string)
        if m is not None:
            token_str = m.group(1)
            tokens.append(("stringConstant", token_str))
            string = string[len(token_str)+2:]
            continue

        m = re.match(r"^([a-zA-Z_][a-zA-Z_0-9]*)", string)
        if m is not None:
            token_str = m.group(1)
            if token_str in keywords:
                tokens.append(("keyword", token_str))
            else:
                tokens.append(("identifier", token_str))
            string = string[len(token_str):]
            continue

        # Single-line comments:
        m = re.match(r"^(//[^\n]*)", string)
        if m is not None:
            string = string[len(m.group(1)):]
            continue

        # Multi-line comments:
        # Note the non-greedy match.
        m = re.match(r"^(/\*.*?\*/)", string, re.DOTALL)
        if m is not None:
            string = string[len(m.group(1)):]
            continue

        if string[0] in symbols:
            tokens.append(("symbol", string[0]))
            string = string[1:]
            continue

        # White space is simply dropped:
        if string[0] in " \t\n":
            string = string[1:]
            continue

        raise Exception("Unexpected input: {string}")

    return tokens



#
# Now, parsers for Jack:
#

TT = Tuple[str, str]
"""Type for tokens: a type (which is "keyword", etc.), and the string that was matched."""


def ByTypeP(token_type: str) -> Parser[TT, str]:
    """Match any token having the given type, producing the token itself."""

    any: Parser[TT, TT] = AnyP()
    return any.filter(lambda t: t[0] == token_type).map(lambda t: t[1])

# Note: slightly improved error messages this way, but I'm trying to avoid subclassing
# Parser in this module.
#
# class ByTypeP(Parser[TT, str]):
#     def __init__(self, token_type: str):
#         self.token_type = token_type
#     def __call__(self, loc: ParseLocation[TT]) -> Tuple[str, ParseLocation[TT]]:
#         typ, val = loc.current_token()
#         if typ == self.token_type:
#             return val, loc.advance()
#         else:
#             raise ParseFailure(self.token_type, loc)


def KeywordP(kw: str) -> Parser[TT, str]:
    """Match a specific keyword (e.g. "class"), and yield the value (because we sometimes use it)."""

    return TokenP(('keyword', kw), kw)


def SymbolP(sym: str) -> Parser[TT, None]:
    """Match a specific symbol (e.g. "+"), producing no value."""

    return TokenP(("symbol", sym), None)


#
# Expressions:
#

ExpressionP: DeferP[TT, jack_ast.Expression] = DeferP("ExpressionP")


BinaryOpP = OrP(*[SymbolP(sym).const(jack_ast.Op(sym)) for sym in "+-*/&|<>="])

UnaryOpP = OrP(*[SymbolP(sym).const(jack_ast.Op(sym)) for sym in "-~"])

IdentifierP = ByTypeP("identifier")

VarNameP = IdentifierP.map(jack_ast.VarRef)

VarNameAndArrayIndexP = (
    IdentifierP
    & BracketP(
        SymbolP("["),
        ExpressionP,
        SymbolP("]"))
).mapConstr(jack_ast.ArrayRef)

IntegerConstantP: Parser[TT, jack_ast.Expression] = ByTypeP("integerConstant").map(lambda str: jack_ast.IntegerConstant(int(str)))

StringConstantP = ByTypeP("stringConstant").map(jack_ast.StringConstant)

KeywordConstantP = (
    TokenP(("keyword", "true"),  jack_ast.KeywordConstant(True))
    | TokenP(("keyword", "false"), jack_ast.KeywordConstant(False))
    | TokenP(("keyword", "null"),  jack_ast.KeywordConstant(None))
    | TokenP(("keyword", "this"),  jack_ast.KeywordConstant("this"))
)


def _unpack_subroutineCall(qual_name: Optional[str], name: str, exprs: Sequence[jack_ast.Expression]):
    class_name = None
    var_name = None
    if qual_name is not None:
        if qual_name[0].isupper():
            class_name = qual_name
        else:
            var_name = qual_name
    return jack_ast.SubroutineCall(class_name=class_name, var_name=var_name, sub_name=name, args=exprs)

SubroutineCallP = (
    OptionalP((IdentifierP >> SymbolP(".")))
    & IdentifierP
    & BracketP(
        SymbolP("("),
        SepByP(ExpressionP, SymbolP(",")),
        SymbolP(")"))
).mapConstr(_unpack_subroutineCall)


TermP: DeferP[TT, jack_ast.Expression] = DeferP("Term")

TermP.set(
    IntegerConstantP
    | StringConstantP
    | KeywordConstantP
    | SubroutineCallP
    | VarNameAndArrayIndexP
    | VarNameP
    | BracketP(SymbolP("("), ExpressionP, SymbolP(")"))
    | (UnaryOpP & TermP).mapConstr(jack_ast.UnaryExpression)
)


# TODO: SepBy1P? Probably, because this doesn't work for left-associative operators.
ExpressionP.set(OrP(
    (TermP & BinaryOpP & ExpressionP).mapConstr(jack_ast.BinaryExpression),  # Bug: *right* associative
    TermP,
))


#
# Statements:
#

StatementP: DeferP[TT, jack_ast.Statement] = DeferP("Statement")

LetStatementP: Parser[TT, jack_ast.Statement] = (
    KeywordP("let")
    & IdentifierP
    & OptionalP(BracketP(
        SymbolP("["),
        ExpressionP,
        SymbolP("]")))
    & SymbolP("=")
    & ExpressionP
    & SymbolP(";")
).mapConstr(jack_ast.LetStatement, [1, 2, 4])

IfStatementP = (
    KeywordP("if")
    & BracketP(
        SymbolP("("),
        ExpressionP,
        SymbolP(")"))
    & BracketP(
        SymbolP("{"),
        ManyP(StatementP),
        SymbolP("}"))
    & OptionalP(
        BracketP(
            ( KeywordP("else")
            & SymbolP("{")),
            ManyP(StatementP),
            SymbolP("}")))
).mapConstr(jack_ast.IfStatement, [1, 2, 3])

WhileStatementP = (
    KeywordP("while")
    & SymbolP("(")
    & ExpressionP
    & SymbolP(")")
    & SymbolP("{")
    & ManyP(StatementP)
    & SymbolP("}")
).mapConstr(jack_ast.WhileStatement, [2, 5])

DoStatementP = BracketP(
    KeywordP("do"),
    SubroutineCallP,
    SymbolP(";")
).map(jack_ast.DoStatement)

ReturnStatementP = BracketP(
    KeywordP("return"),
    OptionalP(ExpressionP),
    SymbolP(";"),
).map(jack_ast.ReturnStatement)


StatementP.set(
    LetStatementP
    | IfStatementP
    | WhileStatementP
    | DoStatementP
    | ReturnStatementP
)


#
# Program Structure:
#

TypeP = (
    KeywordP("int")
    | KeywordP("char")
    | KeywordP("boolean")
    | IdentifierP.filter(lambda str: str[0].isupper())
).map(jack_ast.Type)

VarDecP = (
    KeywordP("var")
    & TypeP
    & SepByP(
        IdentifierP,
        SymbolP(","),
        one_or_more=True)
    & SymbolP(";")
).mapConstr(jack_ast.VarDec, [1, 2])

SubroutineBodyP = BracketP(
    SymbolP("{"),
    ( ManyP(VarDecP)
      & ManyP(StatementP)
    ),
    SymbolP("}")
).mapConstr(jack_ast.SubroutineBody)

ParameterP = (
    TypeP
    & IdentifierP
).mapConstr(jack_ast.Parameter)

ResultTypeP: Parser[TT, Optional[jack_ast.Type]] = OrP(KeywordP("void").const(None), TypeP)

SubroutineDecP = (
    ( KeywordP("constructor")
      | KeywordP("function")
      | KeywordP("method"))
    & ResultTypeP
    & IdentifierP
    & BracketP(
        SymbolP("("),
        SepByP(ParameterP, SymbolP(",")),
        SymbolP(")"))
    & SubroutineBodyP
).mapConstr(jack_ast.SubroutineDec)

ClassVarDecP = (
    ( KeywordP("static").const(True)
      | KeywordP("field").const(False))
    & TypeP
    & SepByP(IdentifierP, SymbolP(","), one_or_more=True)
    & SymbolP(";")
).mapConstr(jack_ast.ClassVarDec, [0, 1, 2])

ClassP = (
    KeywordP("class")
    & IdentifierP
    & SymbolP("{")
    & ManyP(ClassVarDecP)
    & ManyP(SubroutineDecP)
    & SymbolP("}")
).mapConstr(jack_ast.Class, [1, 3, 4])

  # Uglier, no?
# ClassP = (
#     KeywordP("class") <<
#     IdentifierP &
#         (SymbolP("{") << ManyP(ClassVarDecP) & ManyP(SubroutineDecP) >> SymbolP("}"))
# ).mapConstr(jack_ast.Class)
