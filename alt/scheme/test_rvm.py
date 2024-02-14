#! /usr/bin/env pytest

import pytest

from alt import big
from alt.scheme import rvm
from alt.scheme.inspector import Inspector
import nand
from nand.translate import AssemblySource
from nand.vector import unsigned

# TODO: put this somewhere common:
def parameterize_simulators(f):
    def vector(chip, **args):
        return run_to_halt(chip, simulator="vector", **args)
    def codegen(chip, **args):
        return run_to_halt(chip, simulator="codegen", **args)
    return pytest.mark.parametrize("run", [vector, codegen])(f)


@parameterize_simulators
def test_trivial(run):
    program = "42"

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize_simulators
def test_string(run):
    program = '"abc"'

    inspect, output = run(program)

    assert inspect.stack() == ["abc"]
    assert output == []


@parameterize_simulators
def test_lt(run):
    program = several("(< 1 2)", "(< 1 1)", "(< 2 1)")

    inspect, output = run(program)

    assert inspect.stack() == [[True, False, False]]
    assert output == []


@parameterize_simulators
def test_add(run):
    program = "(+ 1 2)"

    inspect, output = run(program)

    assert inspect.stack() == [3]
    assert output == []


@parameterize_simulators
def test_sub(run):
    program = "(- 123 234)"

    inspect, output = run(program)

    assert inspect.stack() == [-111]
    assert output == []


@parameterize_simulators
def test_mul(run):
    program = "(* 6 7)"

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize_simulators
def test_mul_mixed_signs(run):
    program = several("(* 6 -7)", "(* -14 -3)", "(* 2 -21)")

    inspect, output = run(program)

    assert inspect.stack() == [[-42, 42, -42]]
    assert output == []


@parameterize_simulators
def test_if(run):
    program = "(if #t 42 '())"

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize_simulators
def test_quote(run):
    program = "'()"

    inspect, output = run(program)

    assert inspect.stack() == [[]]
    assert output == []


@parameterize_simulators
def test_lambda(run):
    program = """
    ((lambda (x y) (+ x y))
        14 28)
    """

    inspect, output = run(program)

    assert inspect.stack() == [42]
    assert output == []


@parameterize_simulators
def test_define(run):
    program = """
    (define (cons x y) (rib x y 0))

    (cons 1 '(2))
    """

    inspect, output = run(program)

    assert inspect.stack() == [[1, 2]]
    assert output == []


@parameterize_simulators
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


@parameterize_simulators
def test_capture(run):
    program = """
    (define (add x) (lambda (y) (+ x y)))
    ((add 1) 2)
    """

    inspect, output = run(program)

    assert inspect.stack() == [3]
    assert output == []


@parameterize_simulators
def test_draw(run):
    program = """
    (define poke (rib 21 0 1))
    (define screen 1024)
    (poke screen 65)
    """

    inspect, output = run(program)

    assert inspect.stack() == [65]
    assert output == []


@parameterize_simulators
def test_tty(run):
    program = """
    (define poke (rib 21 0 1))
    (define keyboard 4095)
    (poke keyboard 48)
    """

    inspect, output = run(program)

    assert inspect.stack() == [48]
    assert output == [ord('0')]



#
# Tests for specific primitives:
#

@parameterize_simulators
def test_field0(run):
    program = """
    (define field0 (rib 6 0 1))

    (field0 '(7 8 9))
    """

    inspect, output = run(program)

    assert inspect.stack() == [7]  # car
    assert output == []


@parameterize_simulators
def test_field1(run):
    program = """
    (define field1 (rib 7 0 1))

    (field1 '(7 8 9))
    """

    inspect, output = run(program)

    assert inspect.stack() == [[8, 9]]  # cdr
    assert output == []

@parameterize_simulators
def test_field2(run):
    program = """
    (define field2 (rib 8 0 1))

    (field2 '(7 8 9))
    """

    inspect, output = run(program)

    assert inspect.stack() == [0]  # pair-type
    assert output == []


@parameterize_simulators
def test_field0_set(run):
    program = """
    (define field0-set! (rib 9 0 1))
    (define (pair x y) (rib x y 0))

    (define foo '(7 8 9))

    ;; Leave both the modified-in-place cons cell and the value on the stack for inspection:
    (pair foo (field0-set! foo 10))
    """

    inspect, output = run(program)

    assert inspect.stack() == [([10, 8, 9], 10)]
    assert output == []


@parameterize_simulators
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


@parameterize_simulators
def test_field2_set(run):
    program = """
    (define field2-set! (rib 11 0 1))
    (define (pair x y) (rib x y 0))

    (define foo '(7 8 9))

    ;; Hard to make a legit value by changing the type, so just update it and then pull it back out
    (pair (field2-set! foo 11) (field2 foo))
    """

    inspect, output = run(program)

    assert inspect.stack() == [(11, 11)]
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
    return "(define (cons x y) (rib x y 0))\n" + go(list(exprs))


def run_to_halt(program, max_cycles=20000, simulator="codegen"):
    """Compile and run a Scheme program, then return a function for inspecting the RAM, and a
    list of words that were written to the TTY port.
    """

    encoded = rvm.compile(program)
    # print(f"encoded program: {repr(encoded)}")

    asm = AssemblySource()

    rvm.interpreter(asm)

    rvm.decode(encoded, asm)

    instrs, symbols, _ = big.assemble(asm.lines, min_static=None, builtins=rvm.BUILTINS)

    computer = nand.syntax.run(big.BigComputer, simulator=simulator)

    computer.init_rom(instrs)

    # Jump over low memory that we might be using for debugging:
    computer.poke(0, big.ROM_BASE)
    computer.poke(1, big.parse_op("0;JMP"))

    cycles = 0
    output = []

    inspect = Inspector(computer, symbols)

    while (not computer.fetch or computer.pc != symbols["halt_loop"]) and cycles <= max_cycles:
        computer.ticktock()
        cycles += 1

        tty_char = computer.get_tty()
        if tty_char:
            output.append(tty_char)

        if computer.fetch and inspect.is_labeled(computer.pc):
            cpu_pc = inspect.show_addr(computer.pc)
            print(f"{cpu_pc}")
            if cpu_pc == "@exec_loop":
                stack = ", ".join(str(x) for x in inspect.stack())
                print(f"  stack: {stack}")
                pc = inspect.peek(1)
                print(f"  {inspect.show_addr(pc):<10} {inspect.show_instr(pc)}")

    return (inspect, output)
