#! /usr/bin/env pytest

import pytest

from alt import big
from alt.scheme import rvm
from alt.scheme.inspector import Inspector
import nand
from nand.translate import AssemblySource
from nand.vector import unsigned


SHOW_ALL_LABELS = False

def run_vector(program, **args):
    return run_to_halt(program, simulator="vector", interpreter="jack", **args)
def run_codegen(program, **args):
    return run_to_halt(program, simulator="codegen", interpreter="jack", **args)
# Assembly is completely broken now (doesn't handle tagged objects)
# def assembly(program, **args):
#     return run_to_halt(program, simulator="codegen", interpreter="assembly", **args)

def parameterize_both(f):
    return pytest.mark.parametrize("run", [run_vector, run_codegen])(f)

def parameterize(f):
    # vector is just too darn slow
    return pytest.mark.parametrize("run", [run_codegen])(f)


def run_jack(program):
    return run_to_halt(program=program, simulator="codegen", interpreter="jack")


@parameterize
def test_trivial(run):
    program = "42"

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize
def test_string(run):
    program = '"abc"'

    inspect, output = run(program)

    assert inspect.stack() == ["abc"]
    assert output == []


@parameterize
def test_lt(run):
    program = several("(< 1 2)", "(< 1 1)", "(< 2 1)")

    inspect, output = run(program)

    assert inspect.stack() == [[True, False, False]]
    assert output == []

@parameterize
def test_lt_negative(run):
    program = several("(< 1 -2)", "(< -2 1)", "(< -10000 10000)")

    inspect, output = run(program)

    assert inspect.stack() == [[False, True, True]]
    assert output == []


@parameterize
def test_add(run):
    program = "(+ 1 2)"

    inspect, output = run(program)

    assert inspect.stack() == [3]
    assert output == []

@parameterize
def test_add_negative(run):
    program = "(+ 1 -2)"

    inspect, output = run(program)

    assert inspect.stack() == [-1]
    assert output == []

@parameterize
def test_add_soft_overflow(run):
    """A sum between 16k and 32k takes 15 bits and ends up as a negative tagged value."""

    program = "(+ 10000 10000)"

    inspect, output = run(program)

    assert inspect.stack() == [-12768]
    assert output == []


@parameterize
def test_add_hard_overflow(run):
    """A sum between -16k and -32k takes 16 bits and needs to be re-tagged to be a valid int."""

    program = "(+ -10000 -10000)"

    inspect, output = run(program)

    assert inspect.stack() == [12768]
    assert output == []


@parameterize
def test_sub(run):
    program = "(- 123 234)"

    inspect, output = run(program)

    assert inspect.stack() == [-111]
    assert output == []


@parameterize
def test_mul(run):
    program = "(* 6 7)"

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize
def test_mul_mixed_signs(run):
    program = several("(* 6 -7)", "(* -14 -3)", "(* 2 -21)")

    inspect, output = run(program)

    assert inspect.stack() == [[-42, 42, -42]]
    assert output == []


# Note: not implemented in assembly
def test_quotient():
    program = "(quotient 123 10)"

    inspect, output = run_jack(program)

    assert inspect.stack() == [12]
    assert output == []


# Note: not implemented in assembly
def test_quotient_mixed_signs():
    program = several("(quotient 6 -3)", "(quotient -14 -3)", "(quotient 21 -2)")

    inspect, output = run_jack(program)

    assert inspect.stack() == [[-2, 4, -10]]
    assert output == []


@parameterize
def test_if(run):
    program = "(if #t 42 '())"

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize
def test_quote(run):
    program = "'(1 2 3)"

    inspect, output = run(program)

    assert inspect.stack() == [[1, 2, 3]]
    assert output == []


@parameterize
def test_lambda(run):
    program = """
    ((lambda (x y) (+ x y))
        14 28)
    """

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize
def test_define(run):
    program = """
    (define (cons x y) (rib x y 0))

    (cons 1 '(2))
    """

    inspect, output = run(program)

    assert inspect.stack() == [[1, 2]]
    assert output == []


# Just run this one on the slow simulator as a sanity check:
@parameterize_both
def test_fact(run):
    program = """
    (define (fact n)
        (if (< n 2) 1
            (* n (fact (- n 1)))))

    (fact 5)
    """

    inspect, output = run(program)

    assert inspect.stack() == [120]
    assert output == []


@parameterize
def test_capture(run):
    program = """
    (define (add x) (lambda (y) (+ x y)))
    ((add 1) 2)
    """

    inspect, output = run(program)

    assert inspect.stack() == [3]
    assert output == []


@parameterize
def test_draw(run):
    program = """
    (define poke (rib 21 0 1))
    (define screen 1024)
    (poke screen 65)
    """

    inspect, output = run(program)

    assert inspect.stack() == [65]
    assert output == []


@parameterize
def test_tty(run):
    program = """
    (define poke (rib 21 0 1))
    (define keyboard 4095)
    (poke keyboard 48)
    """

    inspect, output = run(program)

    assert inspect.stack() == [48]
    assert output == [ord('0')]


@parameterize
def test_eval(run):
    with open("alt/scheme/ribbit/min.scm") as f:
        lib = f.readlines()

    program = "\n".join(lib + ["""(eval '(+ 1 2))"""])

    inspect, output = run(program, max_cycles=1_000_000)

    assert inspect.stack() == [3]
    assert output == []


#
# Tests for specific primitives:
#

@parameterize
def test_field0(run):
    program = """
    (define field0 (rib 6 0 1))

    (field0 '(7 8 9))
    """

    inspect, output = run(program)

    assert inspect.stack() == [7]  # car
    assert output == []


@parameterize
def test_field1(run):
    program = """
    (define field1 (rib 7 0 1))

    (field1 '(7 8 9))
    """

    inspect, output = run(program)

    assert inspect.stack() == [[8, 9]]  # cdr
    assert output == []

@parameterize
def test_field2(run):
    program = """
    (define field2 (rib 8 0 1))

    (field2 '(7 8 9))
    """

    inspect, output = run(program)

    assert inspect.stack() == [0]  # pair-type
    assert output == []


@parameterize
def test_field0_set(run):
    program = """
    (define field0-set! (rib 9 0 1))
    (define (pair x y) (rib x y 0))

    (define foo '(7 8 9))

    ;; Leave both the modified-in-place cons cell and the value on the stack for inspection:
    (pair foo (field0-set! foo 10))
    """

    inspect, output = run(program)

    assert inspect.stack() == [([10, 8, 9], 10, 0)]
    assert output == []


@parameterize
def test_field1_set(run):
    program = """
    (define field1-set! (rib 10 0 1))
    (define (pair x y) (rib x y 0))

    (define foo '(7 8 9))

    ;; Leave both the modified-in-place cons cell and the value on the stack for inspection:
    (pair foo (field1-set! foo '(10 11)))
    """

    inspect, output = run(program)

    # Note: here the cdr is acually a list, so it gets interpreted that way
    assert inspect.stack() == [[[7, 10, 11], 10, 11]]
    assert output == []


@parameterize
def test_field2_set(run):
    program = """
    (define field2-set! (rib 11 0 1))
    (define (pair x y) (rib x y 0))

    (define foo '(7 8 9))

    ;; Hard to make a legit value by changing the type, so just update it and then pull it back out
    (pair (field2-set! foo 11) (field2 foo))
    """

    inspect, output = run(program)

    assert inspect.stack() == [(11, 11, 0)]
    assert output == []


@parameterize
def test_eqv_simple(run):
    program = """
    (define eqv? (rib 12 0 1))

    (define x 42)
    (define y 42)  ;; same value means same object
    (define z 11)

    """ + several("(eqv? x x)", "(eqv? x y)", "(eqv? x z)")

    inspect, output = run(program)

    assert inspect.stack() == [[True, True, False]]
    assert output == []


@parameterize
def test_eqv_ribs(run):
    program = """
    (define eqv? (rib 12 0 1))

    (define x '(1 2 3))
    (define y '(1 2 3))  ;; not the same object, despite same contents
    (define z '(3 4 5))

    """ + several("(eqv? x x)", "(eqv? x y)", "(eqv? x z)")

    inspect, output = run(program)

    assert inspect.stack() == [[True, False, False]]
    assert output == []


@parameterize
def test_ribq(run):
    program = """
    (define rib? (rib 5 0 1))

    """ + several("(rib? 123)", "(rib? -345)", "(rib? #t)", '(rib? "abc")')

    inspect, output = run(program)

    assert inspect.stack() == [[False, False, True, True]]
    assert output == []


#
# Helpers
#

def several(*exprs):
    """Make a program that evaluates several expressions and constructs a list with each result."""
    def go(xs):
        # print(xs)
        if xs == []:
            return "  '()"
        else:
            return f"(cons {xs[0]}\n{go(xs[1:])})"
    return "(define (cons $$x $$y) (rib $$x $$y 0))\n" + go(list(exprs))


def run_to_halt(program, interpreter, max_cycles=250000, simulator="codegen"):
    """Compile and run a Scheme program, then return a function for inspecting the RAM, and a
    list of words that were written to the TTY port.
    """

    encoded = rvm.compile(program)
    # print(f"encoded program: {repr(encoded)}")

    instrs, symbols, stack_loc, pc_loc, next_rib_loc, interp_loop_addr, halt_loop_addr = rvm.assemble(encoded, interpreter, True)

    computer = nand.syntax.run(big.BigComputer, simulator=simulator)

    computer.init_rom(instrs)

    # Jump over low memory that we might be using for debugging:
    computer.poke(0, big.ROM_BASE)
    computer.poke(1, big.parse_op("0;JMP"))

    cycles = 0
    output = []

    inspect = Inspector(computer, symbols, stack_loc)

    while not (computer.fetch and computer.pc == halt_loop_addr):
        if cycles > max_cycles:
            raise Exception(f"exceeded max_cycles: {max_cycles:,d}")

        computer.ticktock()
        cycles += 1

        tty_char = computer.get_tty()
        if tty_char:
            print(f"tty: {tty_char}")
            output.append(tty_char)

        if computer.fetch and inspect.is_labeled(computer.pc):
            if SHOW_ALL_LABELS:
                print(f"{inspect.show_addr(computer.pc)}")
            if computer.pc == interp_loop_addr:
                print(f"{cycles:,d}")
                stack = ", ".join(str(x) for x in inspect.stack())
                print(f"  stack: {stack}")
                pc = inspect.peek(pc_loc)
                print(f"  pc: {inspect.show_addr(pc)}")
                print(f"  {inspect.show_instr(pc)}")

    print(f"cycles: {cycles}")

    return (inspect, output)
