"""Types for every kind of AST node necessary to represent Jack programs.

These NamedTuples make parsing and syntax analysis code easier to follow, with nicer pretty
printing and comparison than raw tuples.

Each NamedTuple corresponds to one of the productions of the Jack grammar as seen in the course
materials (e.g. Chapter 10 lecture notes, slide 84).
"""

from typing import NamedTuple, Optional, Sequence, Union


Type = str
"""Either 'int', 'char', or 'boolean', or a class name."""


# Expressions:

class IntegerConstant(NamedTuple):
    value: int

class StringConstant(NamedTuple):
    value: str

class KeywordConstant(NamedTuple):
    value: object

class VarRef(NamedTuple):
    name: str

class ArrayRef(NamedTuple):
    name: str
    array_index: "ExpressionRec"

class SubroutineCall(NamedTuple):
    """Note: either class_name or var_name or neither may be present."""

    class_name: Optional[str]
    var_name: Optional[str]
    sub_name: str
    args: Sequence["ExpressionRec"]

class BinaryExpression(NamedTuple):
    left: "ExpressionRec"
    op: "Op"
    right: "ExpressionRec"

class UnaryExpression(NamedTuple):
    op: "Op"
    expr: "ExpressionRec"

class Op(NamedTuple):
    symbol: str

# Note: no AST node for sub-expressions wrapped in parens... Just use the expression node.

Expression = Union[
    IntegerConstant, StringConstant, KeywordConstant,
    VarRef, ArrayRef, SubroutineCall,
    BinaryExpression, UnaryExpression
]

ExpressionRec = object
"""A type for when you want to say "Expression", but the type checker complains about a
"possible cyclic definition".
"""


# Statements:

class LetStatement(NamedTuple):
    name: str
    array_index: Optional[Expression]
    expr: Expression

class IfStatement(NamedTuple):
    cond: Expression
    when_true: Sequence["StatementRec"]
    when_false: Optional[Sequence["StatementRec"]] = None

class WhileStatement(NamedTuple):
    cond: Expression
    body: Sequence["StatementRec"]

class DoStatement(NamedTuple):
    expr: SubroutineCall

class ReturnStatement(NamedTuple):
    expr: Optional[Expression]

Statement = Union[LetStatement, IfStatement, WhileStatement, DoStatement, ReturnStatement]

StatementRec = object
"""A type for when you want to say "Statement", but the type checker complains about a
"possible cyclic definition".
"""


# Program Structure:

class VarDec(NamedTuple):
    type: Type
    names: Sequence[str]

class SubroutineBody(NamedTuple):
    varDecs: Sequence[VarDec]
    statements: Sequence[Statement]

class Parameter(NamedTuple):
    type: Type
    name: str

SubKind = str  # requires 3.8: Literal["function", "method", "constructor"]

class SubroutineDec(NamedTuple):
    kind: SubKind
    result: Optional[Type]  # Note: None means "void" here
    name: str
    params: Sequence[Parameter]
    body: SubroutineBody

class ClassVarDec(NamedTuple):
    static: bool
    type: Type
    names: Sequence[str]

class Class(NamedTuple):
    name: str
    varDecs: Sequence[ClassVarDec]
    subroutineDecs: Sequence[SubroutineDec]



#
# Pretty-print hacks:
#

def _indent(str):
    return "\n".join(
        "   " + line
        for line in str.split("\n"))

def _indented_list(lst):
    return "\n".join(
        ["["]
        + [_indent(repr(x)) + "," for x in lst]
        + ["]"]
    )

# Monkey-patch the __reprs__ on each node that has lists of declarations and statements.
# The idea is to be identical to the default __repr__, with added white space.

# def _SubroutineCall_repr(self):
#     return "\n".join([
#         f"SubroutineCall(",
#         _indent("\n".join([
#             f"class_name={repr(self.class_name)},",
#             f"var_name={repr(self.var_name)},",
#             f"sub_name={repr(self.sub_name)},",
#             f"args={_indented_list(self.args)}",
#         ])) + ")",
#     ])
# SubroutineCall.__repr__ = _SubroutineCall_repr  # type: ignore

def _IfStatement_repr(self):
    return "\n".join([
        f"IfStatement(",
        _indent(
            f"cond={repr(self.cond)},\n"
            f"when_true={_indented_list(self.when_true)},\n"
            f"when_false={_indented_list(self.when_false) if self.when_false is not None else None})")
    ])
IfStatement.__repr__ = _IfStatement_repr  # type: ignore

def _WhileStatement_repr(self):
    return "\n".join([
        f"WhileStatement(",
        _indent(
            f"cond={repr(self.cond)},\n"
            f"body={_indented_list(self.body)})")
    ])
WhileStatement.__repr__ = _WhileStatement_repr  # type: ignore

def _SubroutineBody_repr(self):
    return "\n".join([
        f"SubroutineBody(",
        _indent(
            f"varDecs={_indented_list(self.varDecs)},\n"
            f"statements={_indented_list(self.statements)})")
    ])
SubroutineBody.__repr__ = _SubroutineBody_repr  # type: ignore

def _Class_repr(self):
    return "\n".join([
        f"Class({repr(self.name)},",
        _indent(
            f"varDecs={_indented_list(self.varDecs)},\n"
            f"subroutineDecs={_indented_list(self.subroutineDecs)})")
    ])
Class.__repr__ = _Class_repr  # type: ignore
