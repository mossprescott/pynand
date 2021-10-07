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
value is needed at the same time. Variables that need to retain their values across subroutine
calls are stored in the "local" space; all other variables are stored in "registers" — fixed
locations in low-memory that can be accessed without the overhead of updating the stack pointer.

Note: this compiler does not use the standard VM opcodes; instead, it translates to its own
IR (intermediate representation), which is more suited to analysis. Its Translator then converts
the IR directly to assembly. That makes the calling sequence a bit different from the rest of the
implementations.

Other differences:

- Subroutine results are stored in r0 (aka @5)
- Return addresses are stored at @4 (aka THAT)
- Each call site just pushes arguments, stashes the return address and then jumps to the "function"
    address. It's up to each function to do any saving of registers and adjustment of the stack
    that it wants to. That makes it possible do less work in the case of a simple function.
    Note: it also means that things go (more) haywire if a call provides the wrong number of args.
- THIS and THAT are otherwise unused; they could be treated as additional registers, but most of the
    time 8 is more than enough.

These changes mean that the debug/trace logging done by some test cases doesn't always show the
correct arguments, locals, return addresses, and result values.
"""

import itertools
from os import name
from typing import Dict, Generic, List, NamedTuple, Optional, Sequence, Set, Tuple, TypeVar, Union

from nand import jack_ast
from nand.platform import Platform, BUNDLED_PLATFORM
from nand.translate import AssemblySource
from nand.solutions import solved_07, solved_11
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

Cmp = str  # requires 3.8: Literal["!=", "=", "<", ">", "<=", ">=""]

class If(NamedTuple):
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
    """Evaluate expr, store the value in the "RESULT" register, and return to the caller."""
    expr: "Expr"

class Push(NamedTuple):
    """Used only with Subroutine calls. Acts like Eval, but the destination is the stack."""
    expr: "Expr"

class Discard(NamedTuple):
    """Call a subroutine, then pop the stack, discarding the result."""
    expr: "CallSub"

Stmt = Union[Eval, IndirectWrite, Store, If, While, Push, Discard]


class CallSub(NamedTuple):
    """Call a subroutine (whose arguments have already been pushed onto the stack), and
    recover the result from the "RESULT" register."""
    class_name: str
    sub_name: str
    num_args: int

class Const(NamedTuple):
    value: int  # any value that fits in a word, including negatives

class Local(NamedTuple):
    """A variable which is local to the subroutine scope. May or may not end up actually
    being stored on the stack in the "local" space."""
    name: str  # TODO: parameterize, so we can annotate, etc.?

class Location(NamedTuple):
    """A location identified by segment and index."""
    kind: VarKind
    idx: int
    name: str  # include for debugging purposes

class Reg(NamedTuple):
    """A variable which is local the the subroutine scope, does not need to persist
    across subroutine calls, and has been assigned to a register."""
    idx: int
    kind: str  # in case there is more than one place where "registers" are stored
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
    num_args: int
    num_vars: int
    leaf: Optional[bool]
    body: List[Stmt]

class Class(NamedTuple):
    name: str
    num_statics: int
    subroutines: List[Subroutine]


def flatten_class(ast: jack_ast.Class) -> Class:
    """Convert each subroutine to the "flattened" IR, which eliminates nested expressions and
    other compound behavior, so that each statement does one thing, more or less.
    """

    symbol_table = SymbolTable(ast.name)

    solved_11.handle_class_var_declarations(ast, symbol_table)

    return Class(
        ast.name,
        sum(len(vd.names) for vd in ast.varDecs if vd.static),
        [flatten_subroutine(s, symbol_table) for s in ast.subroutineDecs])


def flatten_subroutine(ast: jack_ast.SubroutineDec, symbol_table: SymbolTable) -> Subroutine:
    """Rewrite the body of a subroutine so that it contains no complex/nested expressions,
    by introducing a temporary variable to hold the result of each sub-expression.

    Note: *not* converting to SSA form here. That would improve register allocation, but
    it blows up the IR somewhat so holding off for now.
    """

    solved_11.handle_subroutine_var_declarations(ast, symbol_table)

    extra_var_count = 0
    def next_var(name: Optional[str] = None) -> Local:
        nonlocal extra_var_count
        name = f"${name or ''}{extra_var_count}"
        extra_var_count += 1
        return Local(name)

    if ast.kind == "method":
        this_expr = Location("argument", 0, "this")
    elif ast.kind == "constructor":
        this_expr = next_var("this")

    def resolve_name(name: str) -> Union[Local, Location]:
        # TODO: this makes sense for locals, arguments, and statics, but "this" needs to get flattened.
        # How to deal with that?
        kind = symbol_table.kind_of(name)
        if kind == "local":
            return Local(name)
        else:
            index = symbol_table.index_of(name)
            return Location(kind, index, name)

    def flatten_statement(stmt: jack_ast.Statement) -> List[Stmt]:
        if isinstance(stmt, jack_ast.LetStatement):
            if stmt.array_index is None:
                loc = resolve_name(stmt.name)
                if isinstance(loc, Local):
                    expr_stmts, expr = flatten_expression(stmt.expr, force=False)
                    let_stmt = Eval(dest=loc, expr=expr)
                    return expr_stmts + [let_stmt]
                elif loc.kind == "this":
                    if isinstance(this_expr, Local):
                        this_var = this_expr
                        this_stmts = []
                    else:
                        this_var = next_var("this")
                        this_stmts = [Eval(this_var, Location("argument", 0, "self"))]
                    if loc.idx == 0:
                        addr_var = this_var
                        addr_stmts = []
                    else:
                        addr_var = next_var(loc.name)
                        addr_stmts = [Eval(addr_var, Binary(this_var, jack_ast.Op("+"), Const(loc.idx)))]
                    value_stmts, value_expr = flatten_expression(stmt.expr)
                    return value_stmts + this_stmts + addr_stmts + [IndirectWrite(addr_var, value_expr)]
                else:
                    expr_stmts, expr = flatten_expression(stmt.expr, force=True)
                    let_stmt = Store(loc, expr)
                    return expr_stmts + [let_stmt]
            else:
                value_stmts, value_expr = flatten_expression(stmt.expr)
                if stmt.array_index == jack_ast.IntegerConstant(0):
                    # Index 0 is the most common case:
                    address = jack_ast.VarRef(stmt.name)
                else:
                    address = jack_ast.BinaryExpression(jack_ast.VarRef(stmt.name), jack_ast.Op("+"), stmt.array_index)
                address_stmts, address_expr = flatten_expression(address)
                return value_stmts + address_stmts + [IndirectWrite(address_expr, value_expr)]

        elif isinstance(stmt, jack_ast.IfStatement):
            test_stmts, test_value, test_cmp = flatten_condition(stmt.cond)
            when_true = [fs for s in stmt.when_true for fs in flatten_statement(s)]
            if stmt.when_false is not None:
                when_false = [fs for s in stmt.when_false for fs in flatten_statement(s)]
            else:
                when_false = None
            return test_stmts + [If(test_value, test_cmp, when_true, when_false)]

        elif isinstance(stmt, jack_ast.WhileStatement):
            test_stmts, test_value, test_cmp = flatten_condition(stmt.cond)
            body_stmts = [fs for s in stmt.body for fs in flatten_statement(s)]
            return [While(test_stmts, test_value, test_cmp, body_stmts)]
        elif isinstance(stmt, jack_ast.DoStatement):
            stmts, expr = flatten_expression(stmt.expr, force=False)
            return stmts + [Discard(expr)]

        elif isinstance(stmt, jack_ast.ReturnStatement):
            if stmt.expr is not None:
                stmts, expr = flatten_expression(stmt.expr, force=False)
                return stmts + [Return(expr)]
            else:
                return [Return(Const(0))]

        else:
            raise Exception(f"Unknown statement: {stmt}")

    def flatten_condition(expr: jack_ast.Expression) -> Tuple[List[Stmt], Expr, Cmp]:
        """Inspect an expression used as the condition of if/while, and reduce it to some statements
        preparing a value to be compared with zero.
        """

        # Collapse simple negated conditions:
        if isinstance(expr, jack_ast.UnaryExpression) and expr.op.symbol == "~":
            if isinstance(expr.expr, jack_ast.BinaryExpression) and expr.expr.op.symbol == "<":
                expr = jack_ast.BinaryExpression(expr.expr.left, jack_ast.Op(">="), expr.expr.right)
            elif isinstance(expr.expr, jack_ast.BinaryExpression) and expr.expr.op.symbol == ">":
                expr = jack_ast.BinaryExpression(expr.expr.left, jack_ast.Op("<="), expr.expr.right)
            elif isinstance(expr.expr, jack_ast.BinaryExpression) and expr.expr.op.symbol == "=":
                expr = jack_ast.BinaryExpression(expr.expr.left, jack_ast.Op("!="), expr.expr.right)

        # Collapse anything that's become a comparison between two values:
        if isinstance(expr, jack_ast.BinaryExpression) and expr.op.symbol in ("<", ">", "=", "<=", ">=", "!="):
            if expr.right == jack_ast.IntegerConstant(0):
                left_stmts, left_value = flatten_expression(expr.left)
                return left_stmts, left_value, expr.op.symbol
            elif expr.left == jack_ast.IntegerConstant(0):
                right_stmts, right_value = flatten_expression(expr.right)
                return right_stmts, right_value, negate_cmp(expr.op.symbol)
            else:
                left_stmts, left_value = flatten_expression(expr.left)
                right_stmts, right_value = flatten_expression(expr.right)
                diff_var = next_var()
                diff_stmt = Eval(diff_var, Binary(left_value, jack_ast.Op("-"), right_value))
                return left_stmts + right_stmts + [diff_stmt], diff_var, expr.op.symbol
        else:
            expr_stmts, expr_value = flatten_expression(expr)
            return expr_stmts, expr_value, "!="

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
                flat_expr = this_expr
            else:
                raise Exception(f"Unknown keyword constant: {expr}")

        elif isinstance(expr, jack_ast.VarRef):
            loc = resolve_name(expr.name)
            if isinstance(loc, Local):
                return [], loc  # Never wrapped
            elif loc.kind == "this":
                if isinstance(this_expr, Local):
                    this_var = this_expr
                    this_stmts = []
                else:
                    this_var = next_var("this")
                    this_stmts = [Eval(this_var, Location("argument", 0, "self"))]
                if loc.idx == 0:
                    addr_var = this_var
                    addr_stmts = []
                else:
                    addr_var = next_var(loc.name)
                    addr_stmts = [Eval(addr_var, Binary(this_var, jack_ast.Op("+"), Const(loc.idx)))]
                stmts = this_stmts + addr_stmts
                flat_expr = IndirectRead(addr_var)
            else:
                stmts = []
                flat_expr = loc

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
            if expr.array_index == jack_ast.IntegerConstant(0):
                # Index 0, probably the most common case:
                address = jack_ast.VarRef(expr.name)
            else:
                address = jack_ast.BinaryExpression(jack_ast.VarRef(expr.name), jack_ast.Op("+"), expr.array_index)
            address_stmts, address_expr = flatten_expression(address)
            stmts = address_stmts
            flat_expr = IndirectRead(address_expr)

        elif isinstance(expr, jack_ast.SubroutineCall):
            pairs = [flatten_expression(a, force=False) for a in expr.args]
            arg_stmts = [s for ss, x in pairs for s in ss + [Push(x)]]
            if expr.class_name is not None:
                stmts = arg_stmts
                flat_expr = CallSub(expr.class_name, expr.sub_name, len(expr.args))
            elif expr.var_name is not None:
                instance_stmts, instance_expr = flatten_expression(jack_ast.VarRef(expr.var_name), force=False)
                stmts = instance_stmts + [Push(instance_expr)] + arg_stmts
                target_class = symbol_table.type_of(expr.var_name)
                flat_expr = CallSub(target_class, expr.sub_name, len(expr.args) + 1)
            else:
                stmts = [Push(this_expr)] + arg_stmts
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

    if ast.kind == "function":
        preamble_stmts = []
    elif ast.kind == "method":
        preamble_stmts = []
    elif ast.kind == "constructor":
        instance_word_count = symbol_table.count("this")
        preamble_stmts = [
            Push(Const(instance_word_count)),
            Eval(this_expr, CallSub("Memory", "alloc", 1)),
        ]
    else:
        raise Exception(f"Unknown subroutine kind: {ast}")

    statements = preamble_stmts + [ fs
        for s in ast.body.statements
        for fs in flatten_statement(s)
    ]

    num_args = symbol_table.count("argument")
    num_vars = None  # bogus, but this isn't meaningful until the next phase anyway
    any_callsub = any(isinstance(n, CallSub) for s in statements for n in traverse_nodes(s))
    return Subroutine(ast.name, num_args, num_vars, not any_callsub, statements)

def negate_cmp(cmp: Cmp) -> Cmp:
    return {"<": ">=", ">": "<=", "=": "!=", "<=": ">", ">=": "<", "!=": "="}[cmp]


def traverse_nodes(ast: object):
    """Generator yielding every node in the tree, in pre-order."""
    yield ast

    if isinstance(ast, Eval):
        yield from traverse_nodes(ast.dest)
        yield from traverse_nodes(ast.expr)
    elif isinstance(ast, IndirectWrite):
        yield from traverse_nodes(ast.address)
        yield from traverse_nodes(ast.value)
    elif isinstance(ast, Store):
        yield from traverse_nodes(ast.location)
        yield from traverse_nodes(ast.value)
    elif isinstance(ast, If):
        yield from (traverse_nodes(s) for s in ast.when_true)
        if ast.when_false is not None:
            yield from (traverse_nodes(s) for s in ast.when_false)
    elif isinstance(ast, While):
        yield from (traverse_nodes(s) for s in ast.body)
    elif isinstance(ast, Return):
        yield from traverse_nodes(ast.expr)
    elif isinstance(ast, Push):
        yield from traverse_nodes(ast.expr)
    elif isinstance(ast, Discard):
        yield from traverse_nodes(ast.expr)

    elif isinstance(ast, (CallSub, Const, Local, Location, Reg)):
        pass
    elif isinstance(ast, Binary):
        yield ast.left
        yield ast.right
    elif isinstance(ast, Unary):
        yield ast.value
    elif isinstance(ast, IndirectRead):
        yield ast.address

    else:
        raise Exception(f"Unknown node: {ast}")


class LiveStmt(NamedTuple):
    statement: Stmt
    before: Set[str]

def analyze_liveness(stmts: Sequence[Stmt], live_at_end: Set[str] = set()) -> Tuple[List[LiveStmt], Set[str]]:
    """Analyze variable lifetimes; a variable is live within all statements which
    follow an assignment (not including the assignment), up to the last statement
    that uses the value (including that statement.)

    The point is that the value has to be stored somewhere at those points in the
    program, and that location has to be somewhere that's not overwritten by the
    statements.

    This is the first step to allocating variables to locations (i.e. registers.)

    Return a list of annotated stmts, and the set of variables that are live at the
    start.
    """

    def analyze_if(stmt: If, live_at_end: Set[str]) -> Tuple[Stmt, Set[str]]:
        """Nothing especially tricky here; it's just a pain that there may or may not
        be an "else" block to thread the information through.
        """

        when_true_liveness, live_at_when_true_start = analyze_liveness(stmt.when_true, live_at_end=live_at_end)

        if stmt.when_false is not None:
            when_false_liveness, live_at_when_false_start = analyze_liveness(stmt.when_false, live_at_end=live_at_end)
        else:
            when_false_liveness = None
            live_at_when_false_start = live_at_end

        live_at_body_start = live_at_when_true_start.union(live_at_when_false_start)

        stmt = If(stmt.value, stmt.cmp, when_true_liveness, when_false_liveness)
        live = live_at_body_start.union(refs(stmt.value))

        return stmt, live


    def analyze_while(stmt: While, live_at_end) -> Tuple[While, Set[str]]:
        """While is tricky because variables that are live at the beginning of the loop
        therefore are also live at the end, which creates a circularity in the analysis.
        Fortunately there's not much going on and simply repeating the same analysis should
        arrive at a fixed point after one more pass.
        """

        body_liveness, live_at_body_start = analyze_liveness(stmt.body, live_at_end=live_at_end)

        live_at_test_end = live_at_body_start.union(refs(stmt.value))

        test_liveness, live_at_test_start = analyze_liveness(stmt.test, live_at_end=live_at_test_end)

        stmt = While(test_liveness, stmt.value, stmt.cmp, body_liveness)
        live = live_at_test_start

        return stmt, live.copy()

    result = []
    live_set = live_at_end.copy()

    for stmt in reversed(stmts):
        # Tricky: when analysis is repeated, strip out previous annotations
        if isinstance(stmt, LiveStmt):
            stmt = stmt.statement

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
            # Note: overwriting stmt (and live_set) here:
            stmt, live_set = analyze_if(stmt, live_set)

        elif isinstance(stmt, While):
            stmt1, live_set_at_top1 = analyze_while(stmt, live_set)
            stmt2, live_set_at_top2 = analyze_while(stmt1, live_set_at_top1)

            assert live_set_at_top2 == live_set_at_top1, "Liveness fixed point not reached"

            # Note: overwriting stmt (and live_set) here:
            stmt, live_set = stmt2, live_set_at_top2

        elif isinstance(stmt, Return):
            read.update(refs(stmt.expr))
        elif isinstance(stmt, Push):
            read.update(refs(stmt.expr))
        elif isinstance(stmt, Discard):
            pass
        else:
            raise Exception(f"Unknown statement: {stmt}")

        live_set.difference_update(written)
        live_set.update(read)
        before = live_set.copy()
        result.insert(0, LiveStmt(stmt, before))

    return (result, live_set)


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
            result.update(need_saving(l.statement.when_true))
            if l.statement.when_false is not None:
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
    def next_var(name: Optional[str] = None) -> Local:
        nonlocal extra_var_count
        name = f"${prefix}{name or ''}{extra_var_count}"
        extra_var_count += 1
        return Local(name)

    def rewrite_value(value: Value) -> Tuple[Sequence[Stmt], Value]:
        if value in map:
            var = next_var(map[value].name)
            return [Eval(var, map[value])], var
        else:
            return [], value

    def rewrite_expr(expr: Expr) -> Tuple[List[Stmt], Expr]:
        if isinstance(expr, (CallSub, Const, Location)):
            return [], expr
        elif isinstance(expr, Local):
            if expr in map:
                return [], map[expr]
            else:
                return [], expr
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

    def rewrite_statement(stmt: Stmt) -> List[Stmt]:
        if isinstance(stmt, Eval):
            expr_stmts, expr = rewrite_expr(stmt.expr)
            if stmt.dest in map:
                if isinstance(expr, (Const, Local)):
                    return expr_stmts + [Store(map[stmt.dest], expr)]
                else:
                    var = next_var(map[stmt.dest].name)
                    return expr_stmts + [Eval(var, expr), Store(map[stmt.dest], var)]
            else:
                return expr_stmts + [Eval(stmt.dest, expr)]
        elif isinstance(stmt, IndirectWrite):
            address_stmts, address_value = rewrite_value(stmt.address)
            value_stmts, value_value = rewrite_value(stmt.value)
            return address_stmts + value_stmts + [IndirectWrite(address_value, value_value)]
        elif isinstance(stmt, Store):
            value_stmts, value = rewrite_expr(stmt.value)
            return value_stmts + [Store(stmt.location, value)]
        elif isinstance(stmt, If):
            value_stmts, value = rewrite_expr(stmt.value)
            when_true = rewrite_statements(stmt.when_true)
            when_false = stmt.when_false and rewrite_statements(stmt.when_false)
            return value_stmts + [If(value, stmt.cmp, when_true, when_false)]
        elif isinstance(stmt, While):
            test = rewrite_statements(stmt.test)
            value_stmts, value = rewrite_expr(stmt.value)
            body = rewrite_statements(stmt.body)
            return [While(test + value_stmts, value, stmt.cmp, body)]
        elif isinstance(stmt, Return):
            value_stmts, value = rewrite_expr(stmt.expr)
            return value_stmts + [Return(value)]
        elif isinstance(stmt, Push):
            expr_stmts, expr = rewrite_expr(stmt.expr)
            return expr_stmts + [Push(expr)]
        elif isinstance(stmt, Discard):
            return [stmt]
        else:
            raise Exception(f"Unknown Stmt: {stmt}")

    def rewrite_statements(stmts: Sequence[Stmt]) -> List[Stmt]:
        return [rs for s in stmts for rs in rewrite_statement(s)]

    return rewrite_statements(stmts)


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

V = TypeVar("V")

def color_graph(vertices: Sequence[V], edges: Sequence[Tuple[V, V]]) -> List[Set[V]]:
    """Given a collection of vertices, and a collection of edges, each connecting
    two vertices of a graph, assign each vertex a color such that no vertex has the
    same color as any other vertex with which it shares an edge.

    There may be unconnected vertices, but there must be no edges that refer to
    vertices that aren't present.

    Return a set of sets, each containing vertices of a particular color. Note:
    the colors are purely conceptual; there's no actual color value associated with
    each set.

    In theory, you would want this to return the optimal result: the smallest possible
    number of colors. At the moment, it doesn't try very hard, but it shouldn't produce
    a trivially bad result; there won't be any two colors that could be merged together.
    Beyond that, it tends to put vertices in the first possible set, so the color groups
    should get smaller as you get further into the result.

    It's also probably not fast. At worst O(v*c + e), v = # of vertices, e = # of edges,
    c = # of colors. Wikipedia says you can get the same result faster by reversing the
    nesting of loops (https://en.wikipedia.org/wiki/Greedy_coloring).

    >>> color_graph(vertices=[1,2,3,4], edges=[(1,2), (2,3)])
    [{1, 3, 4}, {2}]
    """

    # Set of connected vertices for each vertex (bidirectionally):
    adjacency: Dict[V, Set[V]] = { v: set() for v in vertices }
    for x, y in edges:
        adjacency[x].add(y)
        adjacency[y].add(x)

    # Visit each vertex in order. Assign each vertex to the lowest-numbered color
    # which it is still possible for it have, based on the color assignments that have
    # been made so far. Note: this should always give the same result, when the vertices
    # are supplied in the same order. The order of edges is irrelevant.
    prohibited_colors: Dict[V, Set[int]] = { v: set() for v in vertices }
    color_sets: List[Set[V]] = []
    for v in vertices:
        color = [c for c in range(len(color_sets)+1) if (c not in prohibited_colors[v])][0]
        if color == len(color_sets):
            color_sets.append(set())
        color_sets[color].add(v)
        for a in adjacency[v]:
            prohibited_colors[a].add(color)

    return color_sets


def color_locals(liveness: Sequence[LiveStmt]) -> List[Set[Local]]:
    """Color the liveness graph (in a super dumb way), grouping locals such that:
    - no two locals that are alive at the same time are in the same set
    - TODO: when one local is the source and another the destination of a particular operation,
        they're in the same group

    But mostly the first thing.
    """

    vars: Set[Local] = set()
    overlaps: Set[Tuple[Local, Local]] = set()
    def add_live_set(live: Sequence[Local]):
        for l in live: vars.add(l)
        for pair in itertools.combinations(live, 2):
            overlaps.add(pair)

    def visit_stmt(stmt: LiveStmt):
        add_live_set([Local(n) for n in stmt.before])

        if isinstance(stmt.statement, If):
            visit_stmts(stmt.statement.when_true)
            visit_stmts(stmt.statement.when_false)
        elif isinstance(stmt.statement, While):
            visit_stmts(stmt.statement.test)
            visit_stmts(stmt.statement.body)
            # Arg: the value being tested may not otherwise ever be live, but it needs to be accounted for
            if isinstance(stmt.statement.value, Local):
                add_live_set([stmt.statement.value] + [Local(l) for l in stmt.statement.body[0].before])

    def visit_stmts(stmts: Optional[Sequence[LiveStmt]]):
        if stmts is not None:
            for stmt in stmts:
                visit_stmt(stmt)

    visit_stmts(liveness)

    # Sort the vars so that named vars get assigned to registers first, mostly to make the result
    # more predictable for test assertions.
    sorted_vars = sorted(vars, key=lambda lcl: (lcl.name.startswith("$"), lcl.name))

    color_sets = color_graph(vertices=sorted_vars, edges=overlaps)
    # import pprint
    # pprint.pprint(color_sets)

    return color_sets


def lock_down_locals(stmts: Sequence[Stmt], map: Dict[Local, Reg]) -> List[Stmt]:
    """Rewrite statements and expressions, updating references to locals to refer to the given
    registers. If any local is not accounted for, fail.
    """

    def rewrite_value(value: Value) -> Value:
        if isinstance(value, Local):
            # TODO: a more informative error
            return map[value]
        else:
            return value

    def rewrite_expr(expr: Expr) -> Expr:
        if isinstance(expr, (CallSub, Const, Location)):
            return expr
        elif isinstance(expr, Local):
            # TODO: a more informative error
            return map[expr]
        elif isinstance(expr, Binary):
            left_value = rewrite_value(expr.left)
            right_value = rewrite_value(expr.right)
            return Binary(left_value, expr.op, right_value)
        elif isinstance(expr, Unary):
            value = rewrite_value(expr.value)
            return Unary(expr.op, value)
        elif isinstance(expr, IndirectRead):
            address = rewrite_value(expr.address)
            return IndirectRead(address)
        else:
            raise Exception(f"Unknown Expr: {expr}")

    def rewrite_statement(stmt: Stmt) -> Stmt:
        if isinstance(stmt, Eval):
            expr = rewrite_expr(stmt.expr)
            dest = rewrite_value(stmt.dest)
            return Eval(dest, expr)
        elif isinstance(stmt, IndirectWrite):
            address = rewrite_value(stmt.address)
            value = rewrite_value(stmt.value)
            return IndirectWrite(address, value)
        elif isinstance(stmt, Store):
            # print(f"rewrite Store: {stmt}")
            value = rewrite_value(stmt.value)
            return Store(stmt.location, value)
        elif isinstance(stmt, If):
            value = rewrite_value(stmt.value)
            when_true = rewrite_statements(stmt.when_true)
            when_false = stmt.when_false and rewrite_statements(stmt.when_false)
            return If(value, stmt.cmp, when_true, when_false)
        elif isinstance(stmt, While):
            test = rewrite_statements(stmt.test)
            value = rewrite_value(stmt.value)
            body = rewrite_statements(stmt.body)
            return While(test, value, stmt.cmp, body)
        elif isinstance(stmt, Return):
            value = rewrite_expr(stmt.expr)
            return Return(value)
        elif isinstance(stmt, Push):
            expr = rewrite_expr(stmt.expr)
            return Push(expr)
        elif isinstance(stmt, Discard):
            return stmt
        else:
            raise Exception(f"Unknown Stmt: {stmt}")

    def rewrite_statements(stmts: Sequence[Stmt]) -> List[Stmt]:
        return [rewrite_statement(s) for s in stmts ]

    return rewrite_statements(stmts)


def phase_two(ast: Subroutine, registers: List[Reg]) -> Subroutine:
    """The input is IR with all locals represented by Local.

    Output has Local eliminated, replaced by Reg where possible, or by Location (i.e. the stack)
    with additional temporary variables.

    Note: it looks like there must be at least 2 available registers.

    Tricky: anything variable found to be live at the start wasn't explicitly initialized, so
    it needs to be initialized to zero. A more precise way to do that would be to find the first
    use, inject an assignment, and re-run the analysis, but a simpler way to get a correct result
    for this very unusual case is just to promote the variable; stack-allocated variables are
    always initialized on function entry. See KeyboardTest.jack for the relevant example.
    """

    # TODO: treat THIS and THAT as additional locations for "saved" vars.
    # TODO: color vars needing saving as well? probably not worth it for stack-allocated.

    promoted_count = 0
    def next_location(var: Local) -> Location:
        nonlocal promoted_count
        loc = Location("local", promoted_count, var.name)
        promoted_count += 1
        return loc

    liveness, live_at_start = analyze_liveness(ast.body)

    need_promotion = need_saving(liveness).union(live_at_start)

    # for s in liveness:
    #     print(_Stmt_str(s))
    # print(f"need saving: {need_promotion}")
    # if len(live_at_start) > 0:
    #     print(f"uninitialized locals in {ast.name}: {live_at_start} (will probably be promoted)")

    body = promote_locals(ast.body, { Local(l): next_location(Local(l)) for l in need_promotion }, "p_")

    while True:
        liveness2, live_at_start2 = analyze_liveness(body)
        need_promotion2 = need_saving(liveness2)

        # Sanity check: additional promotion
        if len(need_promotion2) > 0:
            # for s in liveness2:
            #     print(_Stmt_str(s))
            # print(f"need saving after one round: {need_promotion2}")
            raise Exception(f"More than one round of promotion needed. Need promotion: {need_promotion2}; in {ast.name}()")
        if len(live_at_start2) > 0:
            raise Exception(f"Uninitialized locals: {live_at_start2}")

        local_sets = color_locals(liveness2)

        if len(local_sets) > len(registers):
            unallocatable_sets = local_sets[len(registers):]

            print(f"Unable to fit local variables in {len(registers)} registers; no space for {[ {l.name for l in s} for s in unallocatable_sets]}")

            body = promote_locals(body, { l: next_location(l) for s in unallocatable_sets for l in s }, "q_")

        else:
            reg_map = {
                l: registers[i]._replace(name=l.name)
                for i, ls in enumerate(local_sets)
                for l in ls
            }

            reg_pressure = 0 if reg_map == {} else max(r.idx+1 for r in reg_map.values())
            # print(f"Registers allocated in {ast.name}: {reg_pressure} ({100*reg_pressure/reg_count:.1f}%)")

            reg_body = lock_down_locals(body, reg_map)

            return Subroutine(ast.name, ast.num_args, promoted_count, ast.leaf, reg_body)


class Compiler:
    def __init__(self):
        self.registers = [Reg(i+5, "R", "?") for i in range(8)]

    def __call__(self, ast: jack_ast.Class) -> Class:
        """Analyze syntax, flatten expressions, allocate registers, and convert to the register-based IR."""

        flat_class = flatten_class(ast)

        # print(flat_class)

        reg_class = Class(
            flat_class.name,
            flat_class.num_statics,
            [phase_two(s, self.registers) for s in flat_class.subroutines])

        # print(reg_class)

        return reg_class



#
# Translate from the IR to assembly:
#

RETURN_ADDRESS = "R4"  # Note: have to avoid using the "temp" registers if this is going to be left in place in leaf functions.
RESULT = "R12" # for now, just use one of the registers also used for local variables.

class Translator(solved_07.Translator):
    def __init__(self):
        self.asm = AssemblySource()
        solved_07.Translator.__init__(self, self.asm)

        # self.preamble()  # called by the loader, apparently

    def handle(self, op):
        """Override for compatibility: an "op" in this context is an entire Class in the IR form."""
        self.translate_class(op)

    def translate_class(self, class_ast: Class):
        for s in class_ast.subroutines:
            self.translate_subroutine(s, class_ast.name)

    def translate_subroutine(self, subroutine_ast: Subroutine, class_name: str):
        # print(subroutine_ast)

        # if self.last_function_start is not None:
        #     instrs = self.asm.instruction_count - self.last_function_start
        #     print(f"  {self.function_namespace} instructions: {instrs}")
        self.last_function_start = self.asm.instruction_count

        self.defined_functions.append(f"{class_name}.{subroutine_ast.name}")

        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{subroutine_ast.name}"

        instr_count_before = self.asm.instruction_count

        self.asm.start(f"function {class_name}.{subroutine_ast.name} {subroutine_ast.num_vars}")
        self.asm.label(f"{self.function_namespace}")

        # Note: this could be done with a common sequence in the preamble, but jumping there and
        # back would cost at least 6 cycles or so, and the goal here is to get small by generating
        # tighter code, not save space in ROM by adding runtime overhead.
        # TODO: avoid this overhead entirely for leaf functions, by just not adjusting the stack
        # at all.
        self.asm.comment("push the return address, then LCL and ARG")
        self.asm.instr(f"@{RETURN_ADDRESS}")
        self.asm.instr("D=M")
        self._push_d()
        self.asm.instr("@LCL")
        self.asm.instr("D=M")
        self._push_d()
        self.asm.instr("@ARG")
        self.asm.instr("D=M")
        self._push_d()

        self.asm.comment("LCL = SP")
        self.asm.instr("@SP")
        self.asm.instr("D=M")
        self.asm.instr("@LCL")
        self.asm.instr("M=D")

        self.asm.comment("ARG = SP - (num_args + 3)")
        self.asm.instr(f"@{subroutine_ast.num_args + 3}")
        self.asm.instr("D=A")
        self.asm.instr("@SP")
        self.asm.instr("D=M-D")
        self.asm.instr("@ARG")
        self.asm.instr("M=D")

        if subroutine_ast.num_vars > 0:
            self.asm.comment(f"space for locals ({subroutine_ast.num_vars})")
            self.reserve_local_space(subroutine_ast.num_vars)

        # Now the body:
        for s in subroutine_ast.body:
            self._handle(s)
        self.asm.blank()

        instr_count_after = self.asm.instruction_count

        # print(f"Translated {class_name}.{subroutine_ast.name}; instructions: {instr_count_after - instr_count_before:,d}")


    # Statements:

    def handle_Eval(self, ast: Eval):
        assert isinstance(ast.dest, Reg)

        if not isinstance(ast.expr, CallSub):
            self.asm.start(f"eval-{self.describe_expr(ast.expr)} {_Stmt_str(ast)}")

        # Do the update in-place if possible:
        if isinstance(ast.expr, Binary) and isinstance(ast.expr.left, Reg) and ast.dest.idx == ast.expr.left.idx:
            op = self.binary_op_alu(ast.expr.op)
            if op is not None:
                right_imm = self.immediate(ast.expr.right)
                if op == "+" and right_imm is not None:
                    if right_imm == 0:
                        pass  # nothing to do: rX = rX + 0
                    else:
                        self.asm.instr(f"@R{ast.dest.idx}")
                        self.asm.instr(f"M=M{right_imm:+}")
                elif op == "-" and right_imm is not None:
                    if right_imm == 0:
                        pass  # nothing to do: rX = rX - 0
                    else:
                        self.asm.instr(f"@R{ast.dest.idx}")
                        self.asm.instr(f"M=M{-right_imm:+}")
                else:
                    self._handle(ast.expr.right)  # D = right
                    self.asm.instr(f"@R{ast.dest.idx}")
                    self.asm.instr(f"M=M{op}D")
                return
        elif isinstance(ast.expr, Binary) and isinstance(ast.expr.right, Reg) and ast.dest.idx == ast.expr.right.idx:
            op = self.binary_op_alu(ast.expr.op)
            if op is not None:
                self._handle(ast.expr.left)  # D = left
                self.asm.instr(f"@R{ast.dest.idx}")
                self.asm.instr(f"M=D{op}M")
                return
        elif isinstance(ast.expr, Unary) and ast.dest == ast.expr:
            self.asm.instr(f"@R{ast.dest.idx}")
            self.asm.instr(f"M={self.unary_op(ast.expr.op)}M")
            return

        imm = self.immediate(ast.expr)
        if imm is not None:
            self.asm.instr(f"@R{ast.dest.idx}")
            self.asm.instr(f"M={imm}")
        else:
            self._handle(ast.expr)

            if isinstance(ast.expr, CallSub):
                self.asm.start(f"eval-result {_Expr_str(ast.dest)} = <result>")

            self.asm.instr(f"@R{ast.dest.idx}")
            self.asm.instr("M=D")

    def handle_IndirectWrite(self, ast: IndirectWrite):
        self.asm.start(f"write {_Stmt_str(ast)}")

        imm = self.immediate(ast.value)
        if imm is not None:
            self.value_to_a(ast.address)
            self.asm.instr(f"M={imm}")
        else:
            self._handle(ast.value)
            self.value_to_a(ast.address)
            self.asm.instr("M=D")

    def handle_Store(self, ast: Store):
        self.asm.start(f"store {_Stmt_str(ast)}")

        imm = self.immediate(ast.value)

        kind, index = ast.location.kind, ast.location.idx
        if kind == "static":
            if imm is not None:
                self.asm.instr(f"@{self.class_namespace}.static{index}")
                self.asm.instr(f"M={imm}")
            else:
                self._handle(ast.value)
                self.asm.instr(f"@{self.class_namespace}.static{index}")
                self.asm.instr("M=D")

        elif kind == "field":
            raise Exception(f"should have been rewritten: {ast}")

        else:
            if kind == "argument":
                segment_ptr = "ARG"
            elif kind == "local":
                segment_ptr = "LCL"
            else:
                raise Exception(f"Unknown location: {ast}")

            # Super common case: initialize a var to 0 or 1 (or -1):
            if imm is not None:
                if index == 0:
                    self.asm.instr(f"@{segment_ptr}")
                    self.asm.instr("A=M")
                    self.asm.instr(f"M={imm}")
                elif index == 1:
                    self.asm.instr(f"@{segment_ptr}")
                    self.asm.instr("A=M+1")
                    self.asm.instr(f"M={imm}")
                else:
                    self.asm.instr(f"@{index}")
                    self.asm.instr("D=A")
                    self.asm.instr(f"@{segment_ptr}")
                    self.asm.instr("A=M+D")
                    self.asm.instr(f"M={imm}")

            else:
                if index <= 6:
                    self._handle(ast.value)
                    self.asm.instr(f"@{segment_ptr}")
                    if index == 0:
                        self.asm.instr("A=M")
                    else:
                        self.asm.instr("A=M+1")
                        for _ in range(index-1):
                            self.asm.instr("A=A+1")
                    self.asm.instr("M=D")

                else:
                    self.asm.instr(f"@{index}")
                    self.asm.instr("D=A")
                    self.asm.instr(f"@{segment_ptr}")
                    self.asm.instr("D=M+D")
                    self.asm.instr("@R15")  # code smell: needing R15 shows that this isn't actually atomic
                    self.asm.instr("M=D")
                    self._handle(ast.value)
                    self.asm.instr("@R15")
                    self.asm.instr("A=M")
                    self.asm.instr("M=D")

    def handle_If(self, ast: If):
        self.asm.comment("if...")

        if ast.when_false is None:
            # Awesome: when there's no else, and the condition is simple, it turns into a single branch.
            # TODO: to avoid constructing boolean values, probably want to put left _and_ right values
            # into the node and compare them directly.

            end_label = self.asm.next_label("end")

            self.asm.start(f"if {_Expr_str(ast.value)} {ast.cmp} 0?")
            self._handle(ast.value)
            self.asm.instr(f"@{end_label}")
            self.asm.instr(f"D;J{self.compare_op_neg(ast.cmp)}")

            for s in ast.when_true:
                self._handle(s)

            self.asm.label(end_label)

        else:
            end_label = self.asm.next_label("end")
            false_label = self.asm.next_label("false")

            self.asm.start(f"if/else {_Expr_str(ast.value)} {ast.cmp} 0?")
            self._handle(ast.value)
            self.asm.instr(f"@{false_label}")
            self.asm.instr(f"D;J{self.compare_op_neg(ast.cmp)}")

            for s in ast.when_true:
                self._handle(s)

            if isinstance(ast.when_true[-1], Return):
                self.asm.comment("end of body unreachable)")
            else:
                self.asm.instr(f"@{end_label}")
                self.asm.instr(f"0;JMP")

            self.asm.label(false_label)
            for s in ast.when_false:
                self._handle(s)

            self.asm.label(end_label)

    def handle_While(self, ast):
        # Note: putting the test at the bottom of the loop means one jmp to start,
        # then a single (conditional) jump per iteration. That's cheaper as long
        # as the average loop does more than one iteration.

        body_label = self.asm.next_label("loop_body")
        test_label = self.asm.next_label("loop_test")

        self.asm.start("while-start")
        self.asm.instr(f"@{test_label}")
        self.asm.instr(f"0;JMP")

        self.asm.label(body_label)
        for s in ast.body:
            self._handle(s)

        self.asm.label(test_label)
        for s in ast.test:
            self._handle(s)

        self.asm.start(f"while-test {_Expr_str(ast.value)} {ast.cmp} 0?")
        self._handle(ast.value)
        self.asm.instr(f"@{body_label}")
        self.asm.instr(f"D;J{self.compare_op_pos(ast.cmp)}")

    def handle_Return(self, ast: Return):
        if isinstance(ast.expr, CallSub):
            self.handle_CallSub(ast.expr)
            self.asm.comment(f"leave the result in {RESULT}")

        else:
            self.asm.start(f"eval-{self.describe_expr(ast.expr)} {_Expr_str(ast.expr)} (for return)")

            # Save a cycle for "return 0":
            imm = self.immediate(ast.expr)
            if imm is not None:
                self.asm.instr(f"@{RESULT}")
                self.asm.instr(f"M={imm}")
            else:
                self._handle(ast.expr)
                self.asm.instr(f"@{RESULT}")
                self.asm.instr("M=D")

        self.return_op()

    def handle_Push(self, ast):
        if not isinstance(ast.expr, CallSub):
            self.asm.start(f"push-{self.describe_expr(ast.expr)} {_Expr_str(ast.expr)}")

        # Save a cycle for "push 0/1":
        imm = self.immediate(ast.expr)
        if imm is not None:
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("A=M-1")
            self.asm.instr(f"M={imm}")
        else:
            self._handle(ast.expr)

            if isinstance(ast.expr, CallSub):
                self.asm.start(f"push-result {_Expr_str(ast.expr)}")

            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("A=M-1")
            self.asm.instr("M=D")

    def handle_Discard(self, ast: Discard):
        # Note: now that results are passed in a register, there's no cleanup to do when
        # the result is not used.
        self.call(ast.expr)

        self.asm.comment(f"ignore the result")

    def compare_op_neg(self, cmp: Cmp):
        return {
            "=": "NE",
            "<": "GE",
            ">": "LE",
            "!=": "EQ",
            "<=": "GT",
            ">=": "LT",
         }[cmp]

    def compare_op_pos(self, cmp: Cmp):
        return {
            "=": "EQ",
            "<": "LT",
            ">": "GT",
            "!=": "NE",
            "<=": "LE",
            ">=": "GE",
         }[cmp]


    # Expressions:

    def handle_CallSub(self, ast: CallSub):
        self.call(ast)

        # Move the result to D
        self.asm.instr(f"@{RESULT}")
        self.asm.instr("D=M")

    def call(self, ast: CallSub):
        self.referenced_functions.append(f"{ast.class_name}.{ast.sub_name}")

        return_label = self.asm.next_label("return_address")

        self.asm.start(f"call {ast.class_name}.{ast.sub_name} {ast.num_args}")

        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{RETURN_ADDRESS}")
        self.asm.instr("M=D")

        self.asm.instr(f"@{ast.class_name.lower()}.{ast.sub_name}")
        self.asm.instr("0;JMP")

        self.asm.label(return_label)


    def handle_Const(self, ast: Const):
        if -1 <= ast.value <= 1:
            self.asm.instr(f"D={ast.value}")
        elif ast.value >= 0:
            self.asm.instr(f"@{ast.value}")
            self.asm.instr("D=A")
        else:
            self.asm.instr(f"@{-ast.value}")
            self.asm.instr("D=-A")

    def handle_Location(self, ast: Location):
        kind, index = ast.kind, ast.idx
        if ast.kind == "static":
            self.asm.instr(f"@{self.class_namespace}.static{ast.idx}")
            self.asm.instr("D=M")
        elif ast.kind == "field":
            raise Exception(f"should have been rewritten: {ast}")
        else:
            if ast.kind == "argument":
               segment_ptr = "ARG"
            elif ast.kind == "local":
                segment_ptr = "LCL"
            else:
                raise Exception(f"Unknown location: {ast}")

            if index == 0:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M")
            elif index == 1:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M+1")
            elif index == 2:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M+1")
                self.asm.instr("A=A+1")
            else:
                self.asm.instr(f"@{index}")
                self.asm.instr("D=A")
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=D+M")
            self.asm.instr("D=M")

    def handle_Reg(self, ast: Reg):
        self.asm.instr(f"@R{ast.idx}")
        self.asm.instr("D=M")

    def handle_Binary(self, ast: Binary):
        left_imm = self.immediate(ast.left)
        alu_op = self.binary_op_alu(ast.op)
        right_imm = self.immediate(ast.right)

        if alu_op == "+" and isinstance(ast.left, Reg) and right_imm is not None:
            # e.g. $0 + 1  ->  @R5; D=M+1
            self.asm.instr(f"@R{ast.left.idx}")
            self.asm.instr(f"D=M{right_imm:+}")
            return
        elif alu_op == "-" and isinstance(ast.left, Reg) and right_imm is not None:
            # e.g. $0 - 1  ->  @R5; D=M-1
            self.asm.instr(f"@R{ast.left.idx}")
            self.asm.instr(f"D=M{-right_imm:+}")
            return
        elif alu_op is not None:
            self._handle(ast.left)     # D = left
            self.value_to_a(ast.right) # A = right
            self.asm.instr(f"D=D{alu_op}A")
            return

        cmp_op = self.binary_op_cmp(ast.op)
        if cmp_op is not None:
            # Massive savings here for this compiler; by pushing the comparison all the way into
            # the ALU, this is one branch, with a specific condition code, to pick the right result.
            # But having to leave the result in D kind of spoils the party; for one thing, have to
            # branch again to skip the no-taken branch, which would have written the other result.

            # TODO: this is almost certainly wrong for signed values where the difference overflows, though:
            #    -30,000 > 30,000
            #    30,000 - (-30,000) = 60,000 = -whatever, which is less than 0

            true_label = self.asm.next_label("compare_true")
            end_label = self.asm.next_label("compare_end")

            # Note: if the right operand is -1,0,1, we shave a few cycles. An earlier phase should
            # take care of rewriting conditions into that form where possible.

            self._handle(ast.left)          # D = left
            if right_imm == 0:
                pass                        # comparing with zero, so D already has left - 0, effectively
            elif right_imm is not None and -1 <= right_imm <= 1:
                self.asm.instr(f"D=D{-right_imm:+d}")     # D = left - right (so, positive if left > right)
            else:
                self.value_to_a(ast.right)  # A = right
                self.asm.instr("D=D-A")     # D = left - right (so, positive if left > right)

            self.asm.instr(f"@{true_label}")
            self.asm.instr(f"D;J{cmp_op}")

            self.asm.instr("D=0")           #  D = false
            self.asm.instr(f"@{end_label}")
            self.asm.instr("0;JMP")

            self.asm.label(true_label)
            self.asm.instr("D=-1")          #  D = true
            self.asm.label(end_label)
            return

        raise Exception(f"TODO: {ast}")

    def binary_op_alu(self, op: jack_ast.Op) -> Optional[str]:
        return {
            "+": "+",
            "-": "-",
            "&": "&",
            "|": "|",
        }.get(op.symbol)

    def binary_op_cmp(self, op: jack_ast.Op) -> Optional[str]:
        return {
            "<": "LT",
            ">": "GT",
            "=": "EQ",
        }.get(op.symbol)

    def handle_Unary(self, ast: Unary):
        if isinstance(ast.value, Reg):
            self.asm.instr(f"@R{ast.value.idx}")
            self.asm.instr(f"D={self.unary_op(ast.op)}M")
        else:
            # Note: ~(Const) isn't being evaluated in the compiler yet, but should be.
            self._handle(ast.value)
            self.asm.instr(f"D={self.unary_op(ast.op)}D")

    def unary_op(self, op: jack_ast.Op) -> str:
        return {"-": "-", "~": "!"}[op.symbol]

    def handle_IndirectRead(self, ast: IndirectRead):
        self.value_to_a(ast.address)
        self.asm.instr("D=M")

    def immediate(self, ast: Expr) -> Optional[int]:
        """If the expression is a constant which the ALU can take as an "immediate" operand
        (i.e. -1, 0, or 1), then unpack it.
        """
        if isinstance(ast, Const) and -1 <= ast.value <= 1:
            return ast.value
        else:
            return None

    def describe_expr(self, expr) -> str:
        """A short suffix categorizing the type of expression, for example 'const'.

        Added to "opcode" tags in the instruction stream, these separate descriptions might be
        helpful for readers; mainly they improve profiling.
        """

        if isinstance(expr, CallSub):
            return "call"
        elif isinstance(expr, Const):
            return "const"
        elif isinstance(expr, Location):
            return "load"
        elif isinstance(expr, Reg):
            return "copy"
        elif isinstance(expr, Binary):
            return "binary"
        elif isinstance(expr, Unary):
            return "unary"
        elif isinstance(expr, IndirectRead):
            return "read"
        else:
            raise Exception(f"Unknown expr: {expr}")


    # Helpers:

    def value_to_a(self, ast: Value):
        """Load a register or constant value into A, without overwriting D, and in one less cycle,
        in some cases."""

        if isinstance(ast, Reg):
            self.asm.instr(f"@R{ast.idx}")
            self.asm.instr("A=M")
        elif isinstance(ast, Const):
            if -1 <= ast.value <= 1:
                self.asm.instr(f"A={ast.value}")
            elif ast.value >= 0:
                self.asm.instr(f"@{ast.value}")
            else:
                self.asm.instr(f"@{-ast.value}")
                self.asm.instr("A=-A")
        elif isinstance(ast, Local):
            raise Exception(f"Local should have been rewritten to Reg or Location: {ast}")
        else:
            raise Exception(f"Unknown Value: {ast}")

    def _handle(self, ast):
        self.__getattribute__(f"handle_{ast.__class__.__name__}")(ast)


    # Override common bits:

    def preamble(self):
        self.asm.start("VM initialization")
        self.asm.instr("@256")
        self.asm.instr("D=A")
        self.asm.instr("@SP")
        self.asm.instr("M=D")

        # Note: this call will never return, so no need to set up a return address, or
        # even initialize ARG/LCL.
        self.asm.start("call Sys.init 0")
        self.asm.instr("@sys.init")
        self.asm.instr("0;JMP")


    # Override some unused bits and pieces to save space:

    def _call(self):
        # not used
        return "_call_common_unused"

    def _compare(self, op):
        # This common sequence isn't used; each comparison is compiled to a custom
        # test/branch sequence.
        return f"_compare_{op}_unused"

    def _return(self):
        "Override the normal sequence; much less stack adjustment required."
        # TODO: use this only for non-leaf subroutines

        label = self.asm.next_label("return_common")

        self.asm.comment(f"common return sequence")
        self.asm.label(label)

        self.asm.comment("SP = LCL")
        self.asm.instr("@LCL")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("M=D")

        self.asm.comment("R15 = ARG (previous SP)")
        self.asm.instr("@ARG")
        self.asm.instr("D=M")
        self.asm.instr("@R15")
        self.asm.instr("M=D")

        self.asm.comment("restore segment pointers from stack (ARG, LCL)")
        self._pop_d()
        self.asm.instr("@ARG")
        self.asm.instr("M=D")
        self._pop_d()
        self.asm.instr("@LCL")
        self.asm.instr("M=D")

        self.asm.comment("R14 = saved return address from the stack")
        self._pop_d()
        self.asm.instr("@R14")
        self.asm.instr("M=D")

        self.asm.comment("SP = R15 (saved ARG)")
        self.asm.instr("@R15")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("M=D")

        self.asm.comment("jmp to R14 (saved return address)")
        self.asm.instr("@R14")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")

        return label


# Hackish pretty-printing:
def _Class_str(self: Class) -> str:
    return "\n".join([f"class {self.name}"]
                     + [jack_ast._indent(str(s)) for s in self.subroutines])
Class.__str__ = _Class_str  # type: ignore

def _Subroutine_str(self: Subroutine) -> str:
    return "\n".join([f"function {self.name} {self.num_vars} (args: {self.num_args}; leaf: {self.leaf})"]
                     + [jack_ast._indent(_Stmt_str(s)) for s in self.body])
Subroutine.__str__ = _Subroutine_str  # type: ignore

def _Stmt_str(stmt: Stmt) -> str:
    if isinstance(stmt, Eval):
        return f"{_Expr_str(stmt.dest)} = {_Expr_str(stmt.expr)}"
    elif isinstance(stmt, IndirectWrite):
        return f"mem[{_Expr_str(stmt.address)}] = {_Expr_str(stmt.value)}"
    elif isinstance(stmt, Store):
        return f"{_Expr_str(stmt.location)} = {_Expr_str(stmt.value)}"
    elif isinstance(stmt, If):
        return "\n".join([
            f"if ({_Expr_str(stmt.value)} {stmt.cmp} zero)",
            jack_ast._indent("\n".join(_Stmt_str(s) for s in stmt.when_true)),
        ]
        + ([] if stmt.when_false is None else [
            f"else",
            jack_ast._indent("\n".join(_Stmt_str(s) for s in stmt.when_false)),
        ]))
    elif isinstance(stmt, While):
        return f"while ({'; '.join(_Stmt_str(s) for s in stmt.test)}; {_Expr_str(stmt.value)} {stmt.cmp} zero)\n" + jack_ast._indent("\n".join(_Stmt_str(s) for s in stmt.body))
    elif isinstance(stmt, Return):
        return f"return {_Expr_str(stmt.expr)}"
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
        return f"call {expr.class_name}.{expr.sub_name} {expr.num_args}"
    elif isinstance(expr, Const):
        return f"{expr.value}"
    elif isinstance(expr, Local):
        return f"{expr.name}"
    elif isinstance(expr, Location):
        return f"{expr.name} ({expr.kind} {expr.idx})"
    elif isinstance(expr, Reg):
        return f"{expr.name} ({expr.kind}{expr.idx})"
    elif isinstance(expr, Binary):
        return f"{_Expr_str(expr.left)} {expr.op.symbol} {_Expr_str(expr.right)}"
    elif isinstance(expr, Unary):
        return f"{expr.op.symbol} {_Expr_str(expr.value)}"
    elif isinstance(expr, IndirectRead):
        return f"mem[{_Expr_str(expr.address)}]"
    else:
        raise Exception(f"Unknown Expr: {expr}")


#
# Platform:
#

def compile_compatible(ast, asm):
    """Wrap the compiler to simulate the sequence the other platforms go through.
    In this case, this phase doesn't generate VM opcodes, but instead just records
    each Class to the stream as a unit.
    """

    ir = Compiler()(ast)

    # Giant hack: write each class to the AssemblySource as if it was an instruction
    asm.add_line_raw(ir)


def parse_line_compatible(line):
    """Phony VM opcode parsing, to simulate the sequence the other platforms go through.
    These "lines" aren't really lines, and just need to get passed through to the next
    step (the translator.)
    """

    return line


REG_PLATFORM = BUNDLED_PLATFORM._replace(
    parse_line=parse_line_compatible,
    translator=Translator,
    compiler=compile_compatible)

if __name__ == "__main__":
    # Note: this import requires pygame; putting it here allows the tests to import the module
    import computer

    computer.main(REG_PLATFORM)
