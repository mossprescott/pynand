"""Types for every kind of AST node necessary to represent Jack programs.

These NamedTuples make parsing and syntax analysis code easier to follow, with nicer pretty
printing and comparison than raw tuples.

Each NamedTuple corresponds to one of the productions of the Jack grammar as seen in the course
materials (e.g. Chapter 10 lecture notes, slide 84).
"""

from typing import NamedTuple, List, Optional, Union


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
    args: List["ExpressionRec"]

class Op(NamedTuple):
    symbol: str

class BinaryExpression(NamedTuple):
    left: "ExpressionRec"
    op: Op
    right: "ExpressionRec"

class UnaryExpression(NamedTuple):
    op: Op
    expr: "ExpressionRec"

# Note: no AST node for sub-expressions wrapped in parens... Just use the expression node.

Expression = Union[
    IntegerConstant, StringConstant, KeywordConstant,
    VarRef, ArrayRef, SubroutineCall,
    BinaryExpression, UnaryExpression, Op
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
    when_true: List["StatementRec"]
    when_false: Optional[List["StatementRec"]] = None

class WhileStatement(NamedTuple):
    cond: Expression
    body: List["StatementRec"]

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
    names: List[str]

class SubroutineBody(NamedTuple):
    varDecs: List[VarDec]
    statements: List[Statement]

class Parameter(NamedTuple):
    type: Type
    name: str

class SubroutineDec(NamedTuple):
    kind: str  # 'constructor', 'function', or 'method'
    result: Optional[Type]  # Note: None means "void" here
    name: str
    params: List[Parameter]
    body: SubroutineBody

class ClassVarDec(NamedTuple):
    static: bool
    type: Type
    names: List[str]

class Class(NamedTuple):
    name: str
    varDecs: List[ClassVarDec]
    subroutineDecs: List[SubroutineDec]



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
        + [_indent(repr(x)) for x in lst]
        + ["]"]
    )

# Money-patch the __reprs__ on each node that has lists of declarations and statements.
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
# SubroutineCall.__repr__ = _SubroutineCall_repr

def _WhileStatement_repr(self):
    return "\n".join([
        f"WhileStatement(",
        _indent(
            f"cond={repr(self.cond)},\n"
            f"body={_indented_list(self.body)})")
    ])
WhileStatement.__repr__ = _WhileStatement_repr

def _SubroutineBody_repr(self):
    return "\n".join([
        f"SubroutineBody(",
        _indent(
            f"varDecs={_indented_list(self.varDecs)},\n"
            f"statements={_indented_list(self.statements)})")
    ])
SubroutineBody.__repr__ = _SubroutineBody_repr

def _Class_repr(self):
    return "\n".join([
        f"Class({repr(self.name)},",
        _indent(
            f"varDecs={_indented_list(self.varDecs)},\n"
            f"subroutineDecs={_indented_list(self.subroutineDecs)})")
    ])
Class.__repr__ = _Class_repr
