#! /usr/bin/env python3

"""A more efficient compiler, using the "temp" segment as a set of registers to reduce stack usage.

Something like 50% of the opcodes produced by the standard compiler "push" values onto the stack.
The majority of those values are then consumed by the next opcode (or the one after); only a few
stay on the stack across a function call. If some of those short-lived values are stored
elsewhere, the stack pointer can be updated much less often, which saves a lot of instructions and
cycles.

The compiler has complete knowledge of which values actually need to appear on the stack
(essentially, the arguments of "call" ops.) All other values can potentially be stored elsewhere.
In particular, the 8 locations in the "temp" segment are otherwise unused, and can be treated as a
set of registers. Accessing one of them is much simpler than pushing/popping, because a) there's no
need to look up the current location of the top of the stack and b) there's no need to update the
stack pointer.

This compiler/translator starts with the normal Jack AST and analyzes it one method at a time.
Expressions are flattened through the use of temporary variables, so that no statement does
more than a single step. Then the lifetime (liveness) of each local/temporary variable is analyzed,
and each one is assigned a storage location that doesn't collide with any other variable whose
value is needed at the same time. Variables that need to retian their values across subroutine
calls are stored in the "local" space; all other variables are stored in "registers" — fixed
locations in low-memory that can be accessed without the overhead of updating the stack pointer.

Limitations:
- If an expression contains too many sub-expressions to be allocated to temps in a simple way, the
  compiler will give up and fail. This situation can be fixed at the source level by introducing
  a local variable. If necessary, the compiler could be enhanced to do that transformation itself.
"""

from nand.solutions.solved_10 import SubroutineDecP
from os import name
from typing import Dict, Generic, List, Literal, NamedTuple, Optional, Sequence, Set, Tuple, TypeVar, Union

from nand import jack_ast
from nand.platform import Platform, BUNDLED_PLATFORM
from nand.translate import AssemblySource, translate_dir
from nand.solutions import solved_05, solved_06, solved_07, solved_11
from nand.solutions.solved_11 import SymbolTable, VarKind


# IR
#
# A simplified AST for statements and expressions:
# - no expressions; each statement does a single calculation
# - if and while are still here, to simplify control-flow analysis
# - separate representations for local variables, which are not at first assigned to a specific
#     location, and other variables, for which the location is fixed in the symbol table.
# - after analysis, local variables either get turned into references to the "local" space,
#     or to specific registers (stored in the same memory the authors' VM calls the "temp" space)
#
# It doesn't have:
# - array indexing (it's been rewritten to explicit pointer arithmetic and Load/Store operations)
# - several of the address spaces of the author's VM aren't used as such "this", "that", "pointer",
#     "temp".
#
# The stack is only used for subroutine arguments and results. The "local" space (also on the stack)
# is used for local variables that cannot be stored only in registers.
#
# This AST is low-level enough that it seems to make sense to call it the VM language and "translate"
# directly to assembly from it.


class Eval(NamedTuple):
    """Evaluate an expression and store the result somewhere."""
    dest: "Local"
    expr: "Expr"

class IndirectWrite(NamedTuple):
    """Copy a value to the location given by address, aka poke()."""
    address: "Value"
    value: "Value"

class Store(NamedTuple):
    """Store a value to a location identified by segment and index."""
    location: "Location"
    value: "Value"

Cmp = Literal["!="]  # Meaning "non-zero"; TODO: the rest of the codes

class If(NamedTuple):
    test: Sequence["Stmt"]
    value: "Value"
    cmp: Cmp
    when_true: Sequence["Stmt"]
    when_false: Optional[Sequence["Stmt"]]

class While(NamedTuple):
    test: Sequence["Stmt"]
    value: "Value"
    cmp: Cmp
    body: Sequence["Stmt"]

class Return(NamedTuple):
    value: "Value"

class Push(NamedTuple):
    """Used only with Subroutine calls. Acts like Assign, but the destination is the stack."""
    expr: "Expr"

class Discard(NamedTuple):
    """Call a subroutine, then pop the stack, discarding the result."""
    expr: "CallSub"

Stmt = Union[Eval, IndirectWrite, If, While, Push, Discard]


class CallSub(NamedTuple):
    class_name: str
    sub_name: str
    arg_count: int

class Const(NamedTuple):
    value: int  # any value that fits in a word, including negatives

class Local(NamedTuple):
    """A variable which is local to the subroutine scope. May or may not end up actually
    being stored on the stack in the "local" space."""
    name: str  # TODO: parameterize, so we can annotate, etc.?

class Location(NamedTuple):
    """A location identified by segment and index."""
    kind: VarKind
    index: int
    name: str  # include for debugging purposes

class Reg(NamedTuple):
    """A variable which is local the the subroutine scope, does not need to persist
    across subroutine calls, and has been assigned to a register."""
    index: int
    name: str  # include for debugging purposes

Value = Union[Const, Local, Reg]
"""A value that's eligible to be referenced in any statement or expression."""

class Binary(NamedTuple):
    left: "Value"
    op: jack_ast.Op
    right: "Value"

class Unary(NamedTuple):
    op: jack_ast.Op
    value: "Value"

class IndirectRead(NamedTuple):
    """Get the value given an address, aka peek()."""
    address: "Value"

Expr = Union[CallSub, Const, Local, Location, Reg, Binary, Unary, IndirectRead]


class Subroutine(NamedTuple):
    name: str
    body: List[Stmt]

class Class(NamedTuple):
    name: str
    subroutines: List[Subroutine]


def flatten_class(ast: jack_ast.Class) -> Class:
    """Convert each subroutine to the "flattened" IR, which eliminates nested expressions and
    other compound behavior, so that each statement does one thing, more or less.
    """

    symbol_table = SymbolTable(ast.name)

    solved_11.handle_class_var_declarations(ast, symbol_table)

    return Class(ast.name, [flatten_subroutine(s, symbol_table) for s in ast.subroutineDecs])


def flatten_subroutine(ast: jack_ast.SubroutineDec, symbol_table: SymbolTable) -> Subroutine:
    """Rewrite the body of a subroutine so that it contains no complex/nested expressions,
    by introducing a temporary variable to hold the result of each sub-expression.

    Note: *not* converting to SSA form here. That would improve register allocation, but
    it blows up the IR somewhat so holding off for now.
    """

    solved_11.handle_subroutine_var_declarations(ast, symbol_table)

    extra_var_count = 0
    def next_var() -> Local:
        nonlocal extra_var_count
        name = f"${extra_var_count}"
        extra_var_count += 1
        return Local(name)

    def resolve_name(name: str) -> Union[Local, Location]:
        kind = symbol_table.kind_of(name)
        if kind == "local":
            return Local(name)
        else:
            index = symbol_table.index_of(name)
            return Location(kind, index, name)

    def flatten_statement(stmt: jack_ast.Statement) -> List[Stmt]:
        if isinstance(stmt, jack_ast.LetStatement):
            if stmt.array_index is None:
                expr_stmts, expr = flatten_expression(stmt.expr, force=False)
                var = resolve_name(stmt.name)
                if isinstance(var, Local):
                    let_stmt = Eval(dest=var, expr=expr)
                else:
                    let_stmt = Store(var.kind, var.index, var.name, expr)
                return expr_stmts + [let_stmt]
            else:
                value_stmts, value_expr = flatten_expression(stmt.expr)
                address_stmts, address_expr = flatten_expression(jack_ast.BinaryExpression(jack_ast.VarRef(stmt.name), jack_ast.Op("+"), stmt.array_index))
                return value_stmts + address_stmts + [IndirectWrite(address_expr, value_expr)]

        elif isinstance(stmt, jack_ast.IfStatement):
            cond_stmts, cond = flatten_expression(stmt.cond)
            when_true = [fs for s in stmt.when_true for fs in flatten_statement(s)]
            if stmt.when_false is not None:
                when_false = [fs for s in stmt.when_false for fs in flatten_statement(s)]
            else:
                when_false = None
            # TODO: inspect the condition and figure out cmp
            return [If(cond_stmts, cond, "!=", when_true, when_false)]

        elif isinstance(stmt, jack_ast.WhileStatement):
            cond_stmts, cond = flatten_expression(stmt.cond)
            body_stmts = [fs for s in stmt.body for fs in flatten_statement(s)]
            # TODO: inspect the condition and figure out cmp
            return [While(cond_stmts, cond, "!=", body_stmts)]

        elif isinstance(stmt, jack_ast.DoStatement):
            stmts, expr = flatten_expression(stmt.expr, force=False)
            return stmts + [Discard(expr)]

        elif isinstance(stmt, jack_ast.ReturnStatement):
            if stmt.expr is not None:
                stmts, expr = flatten_expression(stmt.expr)
                return stmts + [Return(expr)]
            else:
                return [Return(Const(0))]

        else:
            raise Exception(f"Unknown statement: {stmt}")


    def flatten_expression(expr: jack_ast.Expression, force=True) -> Tuple[List[Stmt], Expr]:
        """Reduce an expression to something that's definitely trivial, possibly preceded
        by some LetStatements introducing temporary vars.

        If force is True, the resulting expression is always a "Value" (that is, either a constant
        or a local.) If not, it may be an expression which can only appear as the right-hand side
        of Eval or Push.
        """

        if isinstance(expr, jack_ast.IntegerConstant):
            return [], Const(expr.value)

        elif isinstance(expr, jack_ast.KeywordConstant):
            if expr.value == True:
                return [], Const(-1)  # Never wrapped
            elif expr.value == False:
                return [], Const(0)  # Never wrapped
            elif expr.value == None:
                return [], Const(0)  # Never wrapped
            elif expr.value == "this":
                stmts = []
                flat_expr = Location("argument", 0, "this")
            else:
                raise Exception(f"Unknown keyword constant: {expr}")

        elif isinstance(expr, jack_ast.VarRef):
            var = resolve_name(expr.name)
            if isinstance(var, Local):
                return [], var  # Never wrapped
            else:
                stmts = []
                flat_expr = var

        elif isinstance(expr, jack_ast.StringConstant):
            # Tricky: the result of each call is the string, which is the first argument to the
            # next. "Push(CallSub(...))" logically means make the call, pop the result, then
            # push it onto the stack. The actual implementation will be
            stmts = (
                [ Push(Const(len(expr.value))),
                  Push(CallSub("String", "new", 1)),
                ]
                + [s for c in expr.value for s in
                    [
                        # Note: the implicit first arg is already on the stack from the previous call
                        Push(Const(ord(c))),
                        Push(CallSub("String", "appendChar", 2)),
                    ]])
            last_push, stmts = stmts[-1], stmts[:-1]
            flat_expr = last_push.expr

        elif isinstance(expr, jack_ast.ArrayRef):
            address_stmts, address_expr = flatten_expression(jack_ast.BinaryExpression(jack_ast.VarRef(expr.name), jack_ast.Op("+"), expr.array_index))
            stmts = address_stmts
            flat_expr = IndirectRead(address_expr)

        elif isinstance(expr, jack_ast.SubroutineCall):
            pairs = [flatten_expression(a, force=False) for a in expr.args]
            arg_stmts = [s for ss, x in pairs for s in ss + [Push(x)]]
            if expr.class_name is not None:
                stmts = arg_stmts
                flat_expr = CallSub(expr.class_name, expr.sub_name, len(expr.args))
            elif expr.var_name is not None:
                stmts = [Push(resolve_name(expr.var_name))] + arg_stmts
                target_class = symbol_table.type_of(expr.var_name)
                flat_expr = CallSub(target_class, expr.sub_name, len(expr.args) + 1)
            else:
                stmts = [Push(Location("argument", 0, "this"))] + arg_stmts
                target_class = symbol_table.class_name
                flat_expr = CallSub(target_class, expr.sub_name, len(expr.args) + 1)

        elif isinstance(expr, jack_ast.BinaryExpression):
            # TODO: this transformation is the same as the standard compiler; share that code?
            if expr.op.symbol == "*":
                return flatten_expression(jack_ast.SubroutineCall("Math", None, "multiply", [expr.left, expr.right]), force=force)
            elif expr.op.symbol == "/":
                return flatten_expression(jack_ast.SubroutineCall("Math", None, "divide", [expr.left, expr.right]), force=force)
            else:
                left_stmts, left_expr = flatten_expression(expr.left)
                right_stmts, right_expr = flatten_expression(expr.right)
                stmts = left_stmts + right_stmts
                flat_expr = Binary(left_expr, expr.op, right_expr)

        elif isinstance(expr, jack_ast.UnaryExpression):
            stmts, child_expr = flatten_expression(expr.expr)
            if isinstance(child_expr, Const) and expr.op.symbol == "-":
                # This is ok because this VM handles negative constant values
                flat_expr = Const(-child_expr.value)
            # elif isinstance(child_expr, Const) and expr.op.symbol == "~":
                # TODO: figure out how to evaluate logical negation at compile time, accounting for word size...
            else:
                flat_expr = Unary(expr.op, child_expr)
        else:
            raise Exception(f"Unknown expression: {expr}")

        if force:
            var = next_var()
            let_stmt = Eval(var, flat_expr)
            return stmts + [let_stmt], var
        else:
            return stmts, flat_expr

    statements = [ fs
        for s in ast.body.statements
        for fs in flatten_statement(s)
    ]

    return Subroutine(ast.name, statements)


class LiveStmt(NamedTuple):
    statement: Stmt
    before: Set[str]
    during: Set[str]
    after: Set[str]

def analyze_liveness(stmts: Sequence[Stmt], live_at_end: Set[str] = set()) -> List[LiveStmt]:
    """Analyze variable lifetimes; a variable is live within all statements which
    follow an assignment (not including the assignment), up to the last statement
    that uses the value (including that statement.)

    The point is that the value has to be stored somewhere at those points in the
    program, and that location has to be somewhere that's not overwritten by the
    statements.

    This is the first step to allocating variables to locations (i.e. registers.)

    Because I can't figure out how this should work, currently producing three results:
    "live before" (e.g. the arguments of a subroutine call are live before the call is
    performed) and "live after" (e.g. the arguments are no longer live once the call
    happens, unless they're otherwise needed.) For now, the "after" of one statement is
    identical to the "before" of the next. "during" may be different from them both,
    in the case that the statement both reads and writes the same variable.
    Update: now that the IR is much simpler, the difference is no longer very interesting
    and it seems like "before" is good enough: we're only going to want to know what's
    live when a CallSub happens, and CallSubs don't read anything now, so their before
    and during are the same.
    """

    result = []
    live_set = set(live_at_end)

    for stmt in reversed(stmts):
        written = set()
        read = set()
        if isinstance(stmt, Eval):
            read.update(refs(stmt.expr))
            written.update(refs(stmt.dest))
        elif isinstance(stmt, IndirectWrite):
            read.update(refs(stmt.address))
            read.update(refs(stmt.value))
        elif isinstance(stmt, Store):
            read.update(refs(stmt.value))
        elif isinstance(stmt, If):
            # TODO: apply to the child blocks and thread properly
            raise Exception("TODO")
        elif isinstance(stmt, While):
            # TODO: need to do some kind of fixed-point thing in case a
            # var's lifetime wraps around? What would that look like?
            # Wouldn't that only matter if it wasn't properly initialized?
            body_liveness = analyze_liveness(stmt.body, live_at_end=live_set)
            if len(body_liveness) > 0:
                live_at_body_start = body_liveness[0].before
            else:
                live_at_body_start = live_set
            test_liveness = analyze_liveness(stmt.test, live_at_end=live_at_body_start)
            if len(test_liveness) > 0:
                live_at_test_start = test_liveness[0].before
            else:
                live_at_test_start = live_at_body_start
            stmt = While(test_liveness, stmt.value, stmt.cmp, body_liveness)
            live_set = live_at_test_start
        elif isinstance(stmt, Return):
            read.update(refs(stmt.value))
        elif isinstance(stmt, Push):
            read.update(refs(stmt.expr))
        elif isinstance(stmt, Discard):
            pass
        else:
            raise Exception(f"Unknown statement: {stmt}")

        after = live_set.copy()
        live_set.difference_update(written)
        during = live_set.copy()
        live_set.update(read)
        before = live_set.copy()
        result.insert(0, LiveStmt(stmt, before, during, after))

    return result


# def refs(expr: jack_ast.Expression) -> Set[str]:
#     if isinstance(expr, (IntegerConstant, StringConstant, KeywordConstant)):
#         return set([])
#     if isinstance(expr, VarRef):
#         return set([expr.name])
#     elif isinstance(expr, ArrayRef):
#         return refs(expr.array_index).union(set([expr.name]))
#     elif isinstance(expr, SubroutineCall):
#         var_ref = [expr.var_name] if expr.var_name is not None else []
#         return set(var_ref + [r for x in expr.args for r in refs(x)])
#     elif isinstance(expr, BinaryExpression):
#         return refs(expr.left).union(refs(expr.right))
#     elif isinstance(expr, UnaryExpression):
#         return refs(expr.expr)
#     else:
#         raise Exception(f"Unknown expression: {expr}")

def refs(expr: Expr) -> Set[str]:
    if isinstance(expr, Local):
        return set([expr.name])
    elif isinstance(expr, Binary):
        return refs(expr.left).union(refs(expr.right))
    elif isinstance(expr, Unary):
        return refs(expr.value)
    elif isinstance(expr, IndirectRead):
        return refs(expr.address)
    else:
        return set()



def need_saving(liveness: Sequence[LiveStmt]) -> Set[str]:
    """Identify variables that need to be stored in a location that won't be
    overwritten by a subroutine call (because at some time or other, their value
    is "live" when a subroutine call occurs.)
    """

    result = set()
    for l in liveness:
        if isinstance(l.statement, (Eval, Push, Discard)) and isinstance(l.statement.expr, CallSub):
            result.update(l.before)
        elif isinstance(l.statement, If):
            result.update(need_saving(l.statement.test))
            result.update(need_saving(l.statement.when_true))
            if result.when_false is not None:
                result.update(need_saving(l.statement.when_false))
        elif isinstance(l.statement, While):
            result.update(need_saving(l.statement.test))
            result.update(need_saving(l.statement.body))
        else:
            pass

    return result


def promote_locals(stmts: Sequence[Stmt], map: Dict[Local, Location], prefix: str) -> List[Stmt]:
    """Rewrite statements and expressions, updating references to locals to refer to the given
    locations. Where necessary, additional statements are introduced to move values around.

    `prefix` has to be unique across calls; it ensures that names generated in different passes
    don't collide.
    """

    extra_var_count = 0
    def next_var() -> Local:
        nonlocal extra_var_count
        name = f"${prefix}{extra_var_count}"
        extra_var_count += 1
        return Local(name)

    def rewrite_value(value: Value) -> Tuple[Sequence[Stmt], Value]:
        if value in map:
            var = next_var()
            return [Eval(var, map[value])], var
        else:
            return [], value

    def rewrite_expr(expr: Expr) -> Tuple[Sequence[Stmt], Expr]:
        if isinstance(expr, (CallSub, Const, Location)):
            return [], expr
        elif isinstance(expr, Local):
            if expr in map:
                return [], map[expr]
        elif isinstance(expr, Binary):
            left_stmts, left_value = rewrite_value(expr.left)
            right_stmts, right_value = rewrite_value(expr.right)
            return left_stmts + right_stmts, Binary(left_value, expr.op, right_value)
        elif isinstance(expr, Unary):
            stmts, value = rewrite_value(expr.value)
            return stmts, Unary(expr.op, value)
        elif isinstance(expr, IndirectRead):
            stmts, address = rewrite_value(expr.address)
            return stmts, IndirectRead(address)
        else:
            raise Exception(f"Unknown Expr: {expr}")

    def rewrite_statement(stmt: Stmt) -> Sequence[Stmt]:
        if isinstance(stmt, Eval):
            expr_stmts, expr = rewrite_expr(stmt.expr)
            if stmt.dest in map:
                if isinstance(expr, (Const, Local)):
                    return expr_stmts + [Store(map[stmt.dest], expr)]
                else:
                    var = next_var()
                    return expr_stmts + [Eval(var, expr), Store(map[stmt.dest], var)]
            else:
                return expr_stmts + [Eval(stmt.dest, expr)]
        else:
            # raise Exception(f"Unknown Stmt: {stmt}")
            return [stmt]

    return [rs for s in stmts for rs in rewrite_statement(s)]


# Next step: assign variables to locations (aka register allocation)
# - consult the symbol table: anything not "local" already has its place
# - any variable that needs saving gets asigned an index in "local" space
# - what's left is local variables that can potentially be assigned to registers
#
# Now, try to assign each un-allocated local variable a color such that:
# - no two variables that are live at the same time have the same color
# - one of: as few colors as possible; a reasonably small number of colors; no more than eight colors
#
# Choose no more than eight colors to be assigned to "registers". The remaining
# get mapped to "local".
#
#


"""
Do I want to be able to refer to static/argument/local in arbitrary VM opcodes?
For example:
  add (field 10) (local 1) (constant 2)  // RAM[THIS + 10] = RAM[LCL + 1] + 2
That would mean having to fold address calculation into the generated add code:
  A=LCL; A=A+1; D=M
  A=2
  D=A+D
  <somewhere>=D
  A=10; D=A; A=THIS; A=A+D
  M=<somehow get the value from wherever it was stashed>
Note: this is something like 15 or more instructions.

No, that seems horrible. Want to allow only locations/values which are available without
doing any arithmetic:
  add (temp 1) (static 5) (constant 15)  // RAM[R1] = RAM[Foo.0] + 15
Might look like:
  A=(Foo.0);D=M
  A=15
  D=A+D
  A=6; M=D
That's one or two instructions per operand, one to add, and two to store the result (so, 6 here.)
If the next instruction uses "temp 1", it's going to reload the same address in A (A=6; D=M). Hmm.

This seems much more tractable, so probably the way to go. Now what are the VM opcodes?

Register-register:
- add {dest: 0-7} {src_a: reg | constant} {src_b: reg | constant}  // sub, and, or, eq, lt, gt, etc.
- not {dest: 0-7} {src: reg | constant}  // neg
- return {src: reg | constant}
- if-goto {src: reg}

Move:
- load {dest: 0-7} {segment} {index}
- store {src: 0-7} {segment} {index}

Hybrid:
- push {segment} {index}  // including temp; pointer?
- pop {segment} {index}  // including temp
- pop <nowhere>
... Note: this flexibility is an optimization; in some cases, the address calculation is simple
and you can do it "inline" with an instruction or two. When it's not, it ends up using R15, which
is effectively the same as if we introduced a temp. Maybe get that optimization back later by
doing the lazy "leave it in D" trick? Seems tricky.

Other (basically unchanged):
- label, goto
- function
- call

"""


def pprint_subroutine_dec(ast: jack_ast.SubroutineDec):
    return "\n".join(
        [f"{ast.kind} {ast.result} {ast.name}({', '.join(str(p) for p in ast.params)}) {{"]
        + [f"  var {vd.type} {', '.join(vd.names)};" for vd in ast.body.varDecs]
        + [""]
        + ["  " + ls for s in ast.body.statements for ls in pprint_statement(s) ]
        + ["}"])


def pprint_statement(stmt: jack_ast.Statement) -> List[str]:
    if isinstance(stmt, jack_ast.LetStatement):
        if stmt.array_index is None:
            return [f"let {stmt.name} = {pprint_trivial_expression(stmt.expr)};"]
        else:
            return [f"let {stmt.name}[{pprint_trivial_expression(stmt.array_index)}] = {pprint_trivial_expression(stmt.expr)};"]
    elif isinstance(stmt, jack_ast.IfStatement):
        return (
            [f"if ({pprint_trivial_expression(stmt.cond)}) {{"]
            + ["  " + l for s in stmt.when_true  for ls in pprint_statement(s) for l in ls]
            + ["}"]
            + ([] if stmt.when_false is None else (
                ["else {"]
                + ["  " + l for s in stmt.when_false for ls in pprint_statement(s) for l in ls]
                + [")"])))

    elif isinstance(stmt, jack_ast.WhileStatement):
        raise Exception(f"TODO: {stmt}")
    elif isinstance(stmt, jack_ast.DoStatement):
        return [f"do {pprint_trivial_expression(stmt.expr)};"]
    elif isinstance(stmt, jack_ast.ReturnStatement):
        if stmt.expr is None:
            return [f"return;"]
        else:
            return [f"return {pprint_trivial_expression(stmt.expr)};"]
    else:
        raise Exception(f"Unknown statement: {stmt}")

def pprint_trivial_expression(expr: jack_ast.Expression) -> str:
    """Very dumb but should work for already-flattened expressions."""
    if isinstance(expr, jack_ast.IntegerConstant):
        return str(expr.value)
    elif isinstance(expr, jack_ast.StringConstant):
        return repr(expr.value)
    elif isinstance(expr, jack_ast.KeywordConstant):
        return expr.value
    elif isinstance(expr, jack_ast.VarRef):
        return expr.name
    elif isinstance(expr, jack_ast.ArrayRef):
        return f"{expr.name}[{pprint_trivial_expression(expr.array_index)}]"
    elif isinstance(expr, jack_ast.SubroutineCall):
        if expr.class_name is not None:
            qual = f"{expr.class_name}."
        elif expr.var_name is not None:
            qual = f"{expr.var_name}."
        else:
            qual = ""
        return f"{qual}{expr.sub_name}({', '.join(pprint_trivial_expression(x) for x in expr.args)})"
    elif isinstance(expr, jack_ast.BinaryExpression):
        return f"{pprint_trivial_expression(expr.left)} {expr.op.symbol} {pprint_trivial_expression(expr.right)}"
    elif isinstance(expr, jack_ast.UnaryExpression):
        return f"{expr.op.symbol}{pprint_trivial_expression(expr.expr)}"
    else:
        raise Exception(f"Unknown expression: {expr}")


class Translator(solved_07.Translator):
    def load(self, reg, segment_name, index):
        self.asm.start(f"load {reg} {segment_name} {index}")

        if segment_name == "constant":
            value = index
            if value <= 1:
                # Save one instruction when the value is 0 or 1 (both very common)
                self.asm.instr(f"@R{5+reg}")
                self.asm.instr("M={value}")
            else:
                self.asm.instr(f"@{value}")
                self.asm.instr(f"@R{5+reg}")
                self.asm.instr("M=D")
        else:
            if segment_name =="local":
                segment_ptr = "LCL"
            elif segment_name == "argument":
                segment_ptr = "ARG"
            elif segment_name == "this":
                segment_ptr = "THIS"
            elif segment_name == "that":
                segment_ptr = "THAT"
            else:
                raise Exception(f"Unknown segment: {segment_name}")

            if index == 0:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M")
                self.asm.instr("D=M")
            elif index == 1:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M+1")
                self.asm.instr("D=M")
            elif index == 2:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M+1")
                self.asm.instr("A=A+1")
                self.asm.instr("D=M")
            else:
                self.asm.instr(f"@{index}")
                self.asm.instr("D=A")
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=D+M")
                self.asm.instr("D=M")

            self.asm.instr(f"@R{5+reg}")
            self.asm.instr("M=D")

    def add(self, dest_reg, x_reg, y_reg):
        return self._binary("add", "+", dest_reg, x_reg, y_reg)

    def _binary(self, opcode, op, dest_reg, x_reg, y_reg):
        self.asm.start(f"{opcode} {dest_reg} {x_reg} {y_reg}; (temp{dest_reg} = temp{x_reg} {op} temp{y_reg})")
        self.asm.instr(f"@R{5+x_reg}")
        self.asm.instr( "D=M")
        self.asm.instr(f"@R{5+y_reg}")
        self.asm.instr(f"D=M{op}D")
        self.asm.instr(f"@R{5+dest_reg}")
        self.asm.instr( "M=D")

    # def replace(self, segment_name, index):
    #     self.asm.start(f"replace {segment_name} {index}")
    #     raise Exception("TODO")

    # def rewrite_ops(self, ops):
    #     result = []
    #     while ops:
    #         if len(ops) >= 2 and ops[0][0] == "pop" and len(ops[0][1]) == 0 and ops[1][0] == "push":
    #             replace_op = ("replace", ops[1][1])
    #             ops = replace_op + ops[2:]
    #         else:
    #             result.append(ops[0])
    #             ops = ops[1:]
    #     return result




# Hackish pretty-printing:
def _Class_str(self: Class) -> str:
    return "\n".join([f"class {self.name}"]
                     + [jack_ast._indent(str(s)) for s in self.subroutines])
Class.__str__ = _Class_str

def _Subroutine_str(self: Subroutine) -> str:
    return "\n".join([f"function {self.name}"]
                     + [jack_ast._indent(_Stmt_str(s)) for s in self.body])

Subroutine.__str__ = _Subroutine_str

def _Stmt_str(stmt: Stmt) -> str:
    if isinstance(stmt, Eval):
        return f"{_Expr_str(stmt.dest)} = {_Expr_str(stmt.expr)}"
    elif isinstance(stmt, IndirectWrite):
        return f"mem[{_Expr_str(stmt.address)}] = {_Expr_str(stmt.value)}"
    elif isinstance(stmt, Store):
        return f"{_Expr_str(stmt.location)} = {_Expr_str(stmt.value)}"
    elif isinstance(stmt, If):
        return "\n".join([
            f"if ({'; '.join(_Stmt_str(s) for s in stmt.test)}; {_Expr_str(stmt.value)} {stmt.cmp} zero)",
            jack_ast._indent("\n".join(_Stmt_str(s) for s in stmt.when_true)),
        ]
        + ([] if stmt.when_false is None else [
            f"else",
            jack_ast._indent("\n".join(_Stmt_str(s) for s in stmt.when_false)),
        ]))
    elif isinstance(stmt, While):
        return f"while ({'; '.join(_Stmt_str(s) for s in stmt.test)}; {_Expr_str(stmt.value)} {stmt.cmp} zero)\n" + jack_ast._indent("\n".join(_Stmt_str(s) for s in stmt.body))
    elif isinstance(stmt, Return):
        return f"return {_Expr_str(stmt.value)}"
    elif isinstance(stmt, Push):
        return f"push {_Expr_str(stmt.expr)}"
    elif isinstance(stmt, Discard):
        return f"_ = {_Expr_str(stmt.expr)}"
    elif isinstance(stmt, LiveStmt):
        # This won't type check, but we're embedding LiveStmts in If/While, so whaddayagonnado?
        liveness = ", ".join(stmt.before)
        lines = _Stmt_str(stmt.statement).split("\n")
        # decorate the first line, which is "while ()" or "if ()"
        return "\n".join([f"{lines[0]} /* {liveness} */"] + lines[1:])
    else:
        raise Exception(f"Unknown Stmt: {stmt}")

def _Expr_str(expr: Expr) -> str:
    """Note: this also works on Value, since it's a subset of Expr."""
    if isinstance(expr, CallSub):
        return f"call {expr.class_name}.{expr.sub_name} {expr.arg_count}"
    elif isinstance(expr, Const):
        return f"{expr.value}"
    elif isinstance(expr, Local):
        return f"{expr.name}"
    elif isinstance(expr, Location):
        return f"{expr.kind}[{expr.index}] ({expr.name})"
    elif isinstance(expr, Binary):
        return f"{_Expr_str(expr.left)} {expr.op.symbol} {_Expr_str(expr.right)}"
    elif isinstance(expr, Unary):
        return f"{expr.op.symbol} {_Expr_str(expr.value)}"
    elif isinstance(expr, IndirectRead):
        return f"mem[{_Expr_str(expr.address)}]"
    else:
        raise Exception(f"Unknown Expr: {expr}")


REG_PLATFORM = BUNDLED_PLATFORM._replace(
    translator=Translator)
    # compiler=Compiler)

if __name__ == "__main__":
    # Note: this import requires pygame; putting it here allows the tests to import the module
    import computer

    computer.main(REG_PLATFORM)
