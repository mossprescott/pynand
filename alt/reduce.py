#! /usr/bin/env python3

"""Enhance the compiler to reduce the complexity of the generated code by transforming certain
patterns at the AST level.

In other words, add a high-level, "front-end", compiler optimization pass. This allows the
programmer to write idiomatic, understandable code, leaving certain optimization tricks
to the compiler.

Note: this can be combined with any compiler that consumes the standard Jack AST; the
`REDUCE_PLATFORM` defined here uses the standard bundled compiler.

Specifically:
- `let x = Math.abs(y)`: substitute a simple if or if/else.
- multiplication by a constant: instead of calling Math.multiply, substitute a series of add ops,
    collecting the result in a new temporary variable.
- division by a constant 2^n: instead of calling Math.divide, substitute a call to `Math.shiftr`,
    which does `16-n` bit tests (and no multiply() or recursive calls).
- TODO: calls to Memory.peek() and .poke() are rewritten as direct read/writes using a local Array var.

Note: all these transformations increase code size and introduce additional local variables, so
this may not work well with very simple compiler/translators that struggle to fit programs in ROM.
But they address patterns of code for which it is hard to generate compact and efficient code
(notably, function calls.)

TODO: also do some simple compile-time evaluation:
- evaluate constant expressions (e.g. 512/16)
- simplify trivial patterns (e.g. x*1, y + 0, ~(z = 0))
- remove dead code (e.g. if (false) { ... })
"""

from typing import Generic, List, Optional, Sequence, Tuple, TypeVar

from nand import jack_ast
from nand.platform import BUNDLED_PLATFORM
from alt.reg import REG_PLATFORM
from alt.risc.reg import RiSC_REG_PLATFORM

Context = TypeVar("Context")

class JackTransform(Generic[Context]):
    """Encapsulate a set of transformations that can be applied to rewrite the expressions and
    statements of a Class."""

    def subroutineDec(self, ast: jack_ast.SubroutineDec, context: Context) -> Optional[jack_ast.SubroutineDec]:
        """If the subroutine should be rewritten, construct a new subroutine."""
        return None

    def statement(self, ast: jack_ast.Statement, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement]]]:
        """If the statement should be rewritten, construct a new sequence of statements, plus any new VarDecs."""
        return None

    # TODO: probably break this out as one method for each expression type, so its cleaner
    # to override just one at a time.
    def expression(self, ast: jack_ast.Expression, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]]:
        """If the expression should be rewritten, construct a new expression, plus any new
        VarDecs and preceding Statements."""
        return None

    #@final  # requires 3.8
    def __or__(self, other: "JackTransform") -> "JackTransform":
        """Compose two transforms, applying them from left to right and taking the first result."""
        return Composed(self, other)

    #@final  # requires 3.8
    def transform(self, class_ast: jack_ast.Class, context: Context) -> jack_ast.Class:

        def rewrite_subroutineDec(ast: jack_ast.SubroutineDec) -> jack_ast.SubroutineDec:
            # TODO: try the transform

            extra_varDecs, stmts = rewrite_statements(ast.body.statements)

            sd = jack_ast.SubroutineDec(
                kind=ast.kind,
                result=ast.result,
                name=ast.name,
                params=ast.params,
                body=jack_ast.SubroutineBody(varDecs=ast.body.varDecs + extra_varDecs, statements=stmts))
            # print(ast)
            # print(sd)
            # if repr(ast) != repr(sd):
            #     print("=== Mismatch! ===")
            # print()
            return sd

        def rewrite_statements(asts: Sequence[jack_ast.Statement]) -> Tuple[List[jack_ast.VarDec], List[jack_ast.Statement]]:
            varDecs: List[jack_ast.VarDec] = []
            stmts: List[jack_ast.Statement] = []
            for s in asts:
                vds, ss = rewrite_statement(s)
                # if vds != []:
                #     print(f"rewrote: {s} -> {vds}; {ss}")
                varDecs.extend(vds)
                stmts.extend(ss)
                # print(f"varDecs: {varDecs}")
                # print(f"stmts: {stmts}")
            return (varDecs, stmts)

        def rewrite_statement(ast: jack_ast.Statement) -> Tuple[List[jack_ast.VarDec], List[jack_ast.Statement]]:
            r = self.statement(ast, context)
            if r is not None:
                vars, stmts = r

                # print(f"rewrote: {ast}\n-> {vars}; {stmts}")
                # print()

                # Yikes, what about all the ways this can not terminate?
                next_vars, next_stmts = rewrite_statements(stmts)
                return (vars + next_vars, next_stmts)

            if isinstance(ast, jack_ast.LetStatement):
                expr_vars, expr_stmts, expr_expr = rewrite_expression(ast.expr)
                if ast.array_index is not None:
                    idx_vars, idx_stmts, idx_expr = rewrite_expression(ast.array_index)
                else:
                    idx_vars, idx_stmts, idx_expr = [], [], None
                return (expr_vars + idx_vars,
                    expr_stmts + idx_stmts +
                        [jack_ast.LetStatement(name=ast.name, array_index=idx_expr, expr=expr_expr)])
            elif isinstance(ast, jack_ast.IfStatement):
                cond_vars, cond_stmts, cond_expr = rewrite_expression(ast.cond)
                true_vars, true_stmts = rewrite_statements(ast.when_true)
                if ast.when_false is not None:
                    false_vars, false_stmts = rewrite_statements(ast.when_false)
                else:
                    false_vars, false_stmts = [], None
                return (cond_vars + true_vars + false_vars,
                        cond_stmts +
                        [jack_ast.IfStatement(cond=cond_expr, when_true=true_stmts, when_false=false_stmts)])
            # TODO: While, Do, Return
            else:
                return [], [ast]

        def rewrite_expression(ast: jack_ast.Expression) -> Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]:
            r = self.expression(ast, context)
            if r is not None:
                vars, stmts, expr = r

                # print(f"rewrote: {ast}\n-> {vars}; {stmts}; {expr}")
                # print()

                # Yikes, what about all the ways this can not terminate?
                next_vars, next_stmts, next_expr = rewrite_expression(expr)
                return (vars + next_vars, stmts + next_stmts, next_expr)

            # print(f"expr: {ast}")
            if isinstance(ast, jack_ast.BinaryExpression):
                left_vars, left_stmts, left_expr = rewrite_expression(ast.left)
                right_vars, right_stmts, right_expr = rewrite_expression(ast.right)

                return (left_vars + right_vars,
                        left_stmts + right_stmts,
                        jack_ast.BinaryExpression(left_expr, ast.op, right_expr))

            # TODO: the rest
            else:
                return [], [], ast

        cl = jack_ast.Class(
            name=class_ast.name,
            varDecs=class_ast.varDecs,
            subroutineDecs=[rewrite_subroutineDec(sd) for sd in class_ast.subroutineDecs])
        return cl

class Composed(JackTransform[Context]):
    def __init__(self, t1: JackTransform[Context], t2: JackTransform[Context]):
        self.t1 = t1
        self.t2 = t2

    def subroutineDec(self, ast: jack_ast.SubroutineDec, context: Context) -> Optional[jack_ast.SubroutineDec]:
        r = self.t1.subroutineDec(ast, context)
        if r is None:
            r = self.t2.subroutineDec(ast, context)
        return r

    def statement(self, ast: jack_ast.Statement, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement]]]:
        r = self.t1.statement(ast, context)
        if r is None:
            r = self.t2.statement(ast, context)
        return r

    def expression(self, ast: jack_ast.Expression, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]]:
        r = self.t1.expression(ast, context)
        if r is None:
            r = self.t2.expression(ast, context)
        return r


class NameGen:
    def __init__(self, prefix: str):
        self.next_id = 0
        self.prefix = prefix

    def next_name(self):
        result = f"${self.prefix}{self.next_id}"
        self.next_id += 1
        return result


class FlattenNeg(JackTransform[Context]):
    """Flatten negative integer constants (which are parsed as UnaryOp("-", IntegerConstant(...)).
    This makes the constant value available for subsequent transformations.
    Note: this means the compiler in the next step has to be prepared to deal with negative integer
    constants, which wouldn't otherwise appear.
    """
    # TODO: similary flatten "~"? That will usually also result in a negative value, effectively.

    def expression(self, ast: jack_ast.Expression, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]]:
        if isinstance(ast, jack_ast.UnaryExpression) and ast.op.symbol == "-" and isinstance(ast.expr, jack_ast.IntegerConstant):
            return ([], [], jack_ast.IntegerConstant(-ast.expr.value))
        else:
            return None


class MultiplyByConstant(JackTransform[NameGen]):
    def expression(self, ast: jack_ast.Expression, context: NameGen) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]]:
        if isinstance(ast, jack_ast.BinaryExpression) and ast.op.symbol == "*":
            if isinstance(ast.left, jack_ast.IntegerConstant):
                return self.inline(ast.right, ast.left, context)
            elif isinstance(ast.right, jack_ast.IntegerConstant):
                return self.inline(ast.left, ast.right, context)

        return None

    def inline(self, expr: jack_ast.Expression, const: jack_ast.IntegerConstant, name_gen: NameGen) -> Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]:
        def plus(l, r):
            return jack_ast.BinaryExpression(l, jack_ast.Op("+"), r)
        def minus(x):
            return jack_ast.UnaryExpression(jack_ast.Op("-"), x)
        def fix_sign(x):
            if const.value < 0:
                return minus(x)
            else:
                return x

        # First, handle all the simple cases so the "general" case always has at least 3 bits to work with.
        if const.value == 0:
            # Note: this means the expression is never evaluated, but then this is dumb anyway.
            return ([], [], jack_ast.IntegerConstant(0))
        elif abs(const.value) == 1:
            return ([], [], fix_sign(expr))
        elif abs(const.value) == 2:
            if isinstance(expr, jack_ast.VarRef):
                # Easy case: x*2 = x+x; no need for temporaries
                return ([], [], fix_sign(plus(expr, expr)))
            else:
                tmp = name_gen.next_name()
                tmp_ref = jack_ast.VarRef(tmp)
                return ([jack_ast.VarDec(type="int", names=[tmp])],
                        [jack_ast.LetStatement(name=tmp, array_index=None, expr=expr)],
                        fix_sign(plus(tmp_ref, tmp_ref)))
        elif abs(const.value) == 3:
            # Note: separating this case makes it easier to generalize all the others below.
            tmp = name_gen.next_name()
            tmp_x = f"{tmp}_x"
            tmp_acc = f"{tmp}_acc"
            x_ref = jack_ast.VarRef(tmp_x)
            acc_ref = jack_ast.VarRef(tmp_acc)
            return ([jack_ast.VarDec(type="int", names=[tmp_x, tmp_acc])],
                    [jack_ast.LetStatement(name=tmp_x, array_index=None, expr=expr),
                     jack_ast.LetStatement(name=tmp_acc, array_index=None, expr=plus(x_ref, x_ref))
                    ],
                    fix_sign(plus(acc_ref, x_ref)))
        else:
            # If we get this far, the constant is not trivial, and the expression may not be a simple VarRef.
            # We want to unroll the multiplication using a pair of temporaries.
            tmp = name_gen.next_name()
            tmp_x = f"{tmp}_x"
            tmp_acc = f"{tmp}_acc"

            x_ref = jack_ast.VarRef(tmp_x)
            acc_ref = jack_ast.VarRef(tmp_acc)
            def shift_add(bit, arg_ref):
                """Shift the accumulated result to the left, and add another x in if the
                current bit is set."""
                if bit:
                    rhs = plus(x_ref, plus(arg_ref, arg_ref))
                else:
                    rhs = plus(arg_ref, arg_ref)
                return jack_ast.LetStatement(name=tmp_acc, array_index=None, expr=rhs)

            const_bits = bits(const.value)
            assert len(const_bits) >= 3, f"Need at least 3 bits; value: {const.value}"

            return ([jack_ast.VarDec(type="int", names=[tmp_x, tmp_acc])],
                    [
                        # Evaluate the non-constant operand (which could be non-trivial) and store it:
                        jack_ast.LetStatement(name=tmp_x, array_index=None, expr=expr),
                        # The first shift gets the value directly from "tmp_x":
                        shift_add(const_bits[1], x_ref),
                    ]
                    # The middle shifts all copy from "tmp_acc":
                    + [shift_add(b, acc_ref) for b in const_bits[2:-1]],

                    # The final shift is embedded in the result expression:
                    fix_sign(shift_add(const_bits[-1], acc_ref).expr))

def bits(word: int) -> List[int]:
    """List of bits, from most- to least-significant, without leading zeros (except [0]),
    and ignoring the sign.

    >>> bits(0)
    [0]
    >>> bits(1)
    [1]
    >>> bits(10)
    [1, 0, 1, 0]
    >>> bits(-10)
    [1, 0, 1, 0]
    """
    return [int(c) for c in bin(abs(word))[2:]]


class DivideByConstant(JackTransform[Context]):
    """Actually, this only reduces division by (positive) 2^n, replacing it with a right-shift
    by the corresponding number of bits.

    Here, that shift is done by an added library function with a couple of loops to inspect
    each bit. That doesn't add much to overall code size, but it also means that shiftr()
    is still consuming +50% of the cycles in Screen.drawLine (as opposed to divide() using
    ~70%; overall still 2x faster.)
    """
    def expression(self, ast: jack_ast.Expression, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]]:
        if (isinstance(ast, jack_ast.BinaryExpression)
                and ast.op.symbol == "/"):
            if isinstance(ast.right, jack_ast.IntegerConstant):
                for n in range(15):
                    if ast.right.value == 2**n:
                        return ([], [], jack_ast.SubroutineCall(
                                            class_name="Math", var_name=None, sub_name="shiftr",
                                            args=[ast.left, jack_ast.IntegerConstant(n)]))

        return None

# Note: this could be inlined at each point of use, but it's always 16-n conditionals, so you end
# up with a fair amount of additional code. This flat loop means one function call instead
# of O(log y) recursive calls, so that should already be a big improvement.
EXTRA_MATH = BUNDLED_PLATFORM.parser("""
class Math {
    /*
     Shift the bits of `x` to the right by `n` positions, effectively dividing x by 2^n.
     `n` is assumed to be positive.
     */
    function int shiftr(int x, int n) {
        var int r, b, x_bit, r_bit, sign_bit;

        // First, shift over to construct the mask for the first bit we need to look at:
        let b = 0;
        let x_bit = 1;
        while (b < n) {
            let x_bit = x_bit+x_bit;  // shift left one bit
            let b = b+1;
        }

        // Now, test each bit and set the corresponding bits in the result:
        let b = 16 - n;
        let r = 0;
        let r_bit = 1;
        while (b > 0) {
            if (x & x_bit) {
                let r = r | r_bit;
            }
            let x_bit = x_bit+x_bit;
            let r_bit = r_bit+r_bit;
            let b = b-1;
        }

        // Now check the sign bit and fill the remaining bits if it was set.
        // This is expected to be uncommon. If it happens a lot, this could
        // be done more efficiently by building a mask as the other bits are
        // checked.
        let sign_bit = 32767+1;  // i.e. INT_MIN: 0x8000
        if (x & sign_bit) {
            while (r_bit > 0) {
                let r = r | r_bit;
                let r_bit = r_bit+r_bit;
            }
            let r = (r | sign_bit) + 1;
        }

        return r;
    }
}
""")

class InlineAbs(JackTransform[Context]):
    """Matches `let x = Math.abs(y);`, substituting `if (y < 0) { let x = -y; } else { let x = y; }`,
    avoiding a function call. Probably increases code size significantly if the compiler/translator
    can't compile the branch compactly.

    Does *not* rewrite Math.abs if a call is nested in some expression, because that pattern doesn't
    occur, but it does print a warning just in case.
    """

    def statement(self, ast: jack_ast.Statement, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement]]]:
        if (isinstance(ast, jack_ast.LetStatement)
                and ast.array_index is None
                and isinstance(ast.expr, jack_ast.SubroutineCall)
                and ast.expr.class_name == "Math"
                and ast.expr.sub_name == "abs"
                and isinstance(ast.expr.args[0], jack_ast.VarRef)):
            arg = ast.expr.args[0]
            if ast.name == arg.name:
                inline_stmt = jack_ast.IfStatement(
                    cond=jack_ast.BinaryExpression(arg, jack_ast.Op("<"), jack_ast.IntegerConstant(0)),
                    when_true=[
                        jack_ast.LetStatement(ast.name, None, jack_ast.UnaryExpression(jack_ast.Op("-"), arg))
                    ],
                    when_false=None)
                return ([], [inline_stmt])
            else:
                inline_stmt = jack_ast.IfStatement(
                    cond=jack_ast.BinaryExpression(arg, jack_ast.Op("<"), jack_ast.IntegerConstant(0)),
                    when_true=[
                        jack_ast.LetStatement(ast.name, None, jack_ast.UnaryExpression(jack_ast.Op("-"), arg))
                    ],
                    when_false=[
                        jack_ast.LetStatement(ast.name, None, arg)
                    ])
                return ([], [inline_stmt])
        return None

    def expression(self, ast: jack_ast.Expression, context: Context) -> Optional[Tuple[List[jack_ast.VarDec], List[jack_ast.Statement], jack_ast.Expression]]:
        if (isinstance(ast, jack_ast.SubroutineCall)
                and ast.class_name == "Math"
                and ast.sub_name == "abs"
                and isinstance(ast.args[0], jack_ast.VarRef)):
            print(f"abs(expr) (not rewritten): {ast}")
            # This doesn't actually occur (in Pong), once the statement-level occurrences are rewritten.
        return None

# TODO: inline Math.max/min()? These get embedded in expressions more often in the OS.


all_transforms = FlattenNeg() | MultiplyByConstant() | DivideByConstant() | InlineAbs()

name_gen = NameGen("rdc")


def enhance_parser(parser, transform):
    """Compose `rewrite_class` with a parser, returning a new function which parses source code
    and then rewrites it in one step.

    This is what you need to make a Platform which does rewriting.
    """

    def go(src):
        ast = parser(src)
        return transform.transform(ast, name_gen)
    return go


def inject_defs(class_ast: jack_ast.Class, extra_defs: jack_ast.Class) -> jack_ast.Class:
    if class_ast.name == extra_defs.name:
        return jack_ast.Class(
            name=class_ast.name,
            varDecs=class_ast.varDecs + extra_defs.varDecs,
            subroutineDecs=class_ast.subroutineDecs + extra_defs.subroutineDecs)
    else:
        return class_ast


def enhance_platform(platform):
    """Derive a platform which """
    return platform._replace(
        parser=enhance_parser(platform.parser, all_transforms),
        library=[all_transforms.transform(inject_defs(ast, EXTRA_MATH), name_gen) for ast in platform.library])

# Note: the transformations all run here (over the library classes) when the module is imported.
REDUCE_PLATFORM = enhance_platform(BUNDLED_PLATFORM)

# Experimental: on top of alt/reg instead
REDUCE_REG_PLATFORM = enhance_platform(REG_PLATFORM)

# Experimental: on top of alt/risc/reg instead
REDUCE_RiSC_REG_PLATFORM = enhance_platform(RiSC_REG_PLATFORM)


if __name__ == "__main__":
    # Note: this import requires pygame; putting it here allows the tests to import the module
    import computer

    computer.main(REDUCE_PLATFORM)
