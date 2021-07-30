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

        m = re.match(r"^(//[^\n]*)", string)
        if m is not None:
            string = string[len(m.group(1)):]
            continue

        m = re.match(r"^(/\*.*\*/)", string, re.DOTALL)
        if m is not None:
            string = string[len(m.group(1)):]
            continue

        if string[0] in symbols:
            tokens.append(("symbol", string[0]))
            string = string[1:]
            continue

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


def KeywordP(kw: str) -> Parser[TT, None]:
    """Match a specific keyword (e.g. "class"), producing no value."""

    return TokenP(('keyword', kw), None)


def SymbolP(sym: str) -> Parser[TT, None]:
    """Match a specific symbol (e.g. "+"), producing no value."""

    return TokenP(("symbol", sym), None)


def unflatten(f):
    """Helper for use with Parser.map. Takes a function with multiple args, wraps it in
    a function that accepts the same args in a list.

    TODO: push this into Parser.map in some way.
    """
    return lambda args: f(*args)


#
# Expressions:
#

ExpressionP: DeferP[TT, jack_ast.Expression] = DeferP("ExpressionP")


BinaryOpP = OrP(*[SymbolP(sym).const(jack_ast.Op(sym)) for sym in "+-*/&|<>="])

UnaryOpP = OrP(*[SymbolP(sym).const(jack_ast.Op(sym)) for sym in "-~"])

IdentifierP = ByTypeP("identifier")

VarNameP = IdentifierP.map(jack_ast.VarRef)

VarNameAndArrayIndexP = SeqP(
    IdentifierP,
    BracketP(
        SymbolP("["),
        ExpressionP,
        SymbolP("]"),
    )).map(unflatten(jack_ast.ArrayRef))

IntegerConstantP = ByTypeP("integerConstant").map(lambda str: jack_ast.IntegerConstant(int(str)))

StringConstantP = ByTypeP("stringConstant").map(jack_ast.StringConstant)

KeywordConstantP = OrP(
    TokenP(("keyword", "true"),  jack_ast.KeywordConstant(True)),
    TokenP(("keyword", "false"), jack_ast.KeywordConstant(False)),
    TokenP(("keyword", "null"),  jack_ast.KeywordConstant(None)),
    TokenP(("keyword", "this"),  jack_ast.KeywordConstant("this")),
)
# (not checked) type: Parser[TT, KeywordConstant]


def _unpack_subroutineCall(qual: Optional[Sequence[str]], name: str, exprs: Sequence[jack_ast.Expression]):
    class_name = None
    var_name = None
    if qual is not None:
        qual_name, _ = qual
        if qual_name[0].isupper():
            class_name = qual_name
        else:
            var_name = qual_name
    return jack_ast.SubroutineCall(class_name=class_name, var_name=var_name, sub_name=name, args=exprs)

SubroutineCallP = SeqP(
    OptionalP(SeqP(IdentifierP, SymbolP("."))),
    IdentifierP,
    BracketP(
        SymbolP("("),
        SepByP(ExpressionP, SymbolP(",")),
        SymbolP(")"),
    )).map(unflatten(_unpack_subroutineCall))


TermP: DeferP[TT, jack_ast.Expression] = DeferP("Term")

TermP.set(OrP(
    IntegerConstantP,
    StringConstantP,
    KeywordConstantP,
    SubroutineCallP,
    VarNameAndArrayIndexP,
    VarNameP,
    BracketP(SymbolP("("), ExpressionP, SymbolP(")")),
    SeqP(UnaryOpP, TermP).map(unflatten(jack_ast.UnaryExpression)),
))


# TODO: SepBy1P? Probably, because this doesn't work for left-associative operators.
ExpressionP.set(OrP(
    SeqP(TermP, BinaryOpP, ExpressionP).map(unflatten(jack_ast.BinaryExpression)),  # Bug: *right* associative
    TermP,
))


#
# Statements:
#

StatementP: DeferP[TT, jack_ast.Statement] = DeferP("Statement")

LetStatementP = SeqP(
    KeywordP("let"),
    IdentifierP,
    OptionalP(BracketP(
        SymbolP("["),
        ExpressionP,
        SymbolP("]"))),
    SymbolP("="),
    ExpressionP,
    SymbolP(";")
).map(lambda vals: jack_ast.LetStatement(vals[1], vals[2], vals[4])) # (unchecked) type: Parser[TT, jack_ast.LetStatement]

IfStatementP = SeqP(
    BracketP(
        SeqP(
            KeywordP("if"),
            SymbolP("("),
        ),
        ExpressionP,
        SymbolP(")")),
    BracketP(
        SymbolP("{"),
        ManyP(StatementP),
        SymbolP("}")),
    OptionalP(
        BracketP(
            SeqP(
                KeywordP("else"),
                SymbolP("{"),
            ),
            ManyP(StatementP),
            SymbolP("}"))),
).map(unflatten(jack_ast.IfStatement))

WhileStatementP = BracketP(
    KeywordP("while"),
    SeqP(
        BracketP(
            SymbolP("("),
            ExpressionP,
            SymbolP(")"),
        ),
        BracketP(
            SymbolP("{"),
            ManyP(StatementP),
            SymbolP("}"),
        ),
    ),
    SeqP()  # Hack: match nothing, just so I can use BracketP to drop the keyword.
).map(unflatten(jack_ast.WhileStatement))

DoStatementP = BracketP(KeywordP("do"), SubroutineCallP, SymbolP(";")).map(jack_ast.DoStatement)

ReturnStatementP = BracketP(
    KeywordP("return"),
    OptionalP(ExpressionP),
    SymbolP(";"),
).map(jack_ast.ReturnStatement)

StatementP.set(OrP(
    LetStatementP,
    IfStatementP,
    WhileStatementP,
    DoStatementP,
    ReturnStatementP,
))


#
# Program Structure:
#

TypeP = OrP(
    KeywordP("int").const("int"),
    KeywordP("char").const("char"),
    KeywordP("boolean").const("boolean"),
    IdentifierP.filter(lambda str: str[0].isupper())
).map(jack_ast.Type)


VarDecP = BracketP(
    KeywordP("var"),
    SeqP(
        TypeP,
        SepByP(
            IdentifierP,
            SymbolP(","),
            one_or_more=True)
    ),
    SymbolP(";")).map(unflatten(jack_ast.VarDec))


SubroutineBodyP = BracketP(
    SymbolP("{"),
    SeqP(
        ManyP(VarDecP),
        ManyP(StatementP),
    ),
    SymbolP("}")
).map(unflatten(jack_ast.SubroutineBody))

ParameterP = SeqP(
    TypeP,
    IdentifierP,
).map(unflatten(jack_ast.Parameter))

SubroutineDecP = SeqP(
    OrP(
        KeywordP("constructor").const("constructor"),
        KeywordP("function").const("function"),
        KeywordP("method").const("method"),
    ),
    OrP(
        KeywordP("void"),
        TypeP,
    ),
    IdentifierP,
    BracketP(
        SymbolP("("),
        SepByP(ParameterP, SymbolP(",")),
        SymbolP(")")
    ),
    SubroutineBodyP,
).map(unflatten(jack_ast.SubroutineDec))

ClassVarDecP = BracketP(
    SeqP(),  # Hack: match nothing, just so I can use BracketP to drop the keyword.
    SeqP(
        OrP(
            KeywordP("static").const(True),
            KeywordP("field").const(False),
        ),
        TypeP,
        SepByP(IdentifierP, SymbolP(","), one_or_more=True),
    ),
    SymbolP(";")
).map(unflatten(jack_ast.ClassVarDec))

ClassP = SeqP(
    KeywordP("class"),
    IdentifierP,
    SymbolP("{"),
    ManyP(ClassVarDecP),
    ManyP(SubroutineDecP),
    SymbolP("}"),
).map(lambda vals: jack_ast.Class(vals[1], vals[3], vals[4]))
