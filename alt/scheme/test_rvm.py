#! /usr/bin/env pytest

import pytest

from alt import big
from alt.scheme import rvm
from alt.scheme.inspector import Inspector
import nand
from nand.translate import AssemblySource
from nand.vector import unsigned

def test_trivial():
    program = "42"

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [42]
    assert output == []


def test_string():
    program = '"abc"'

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == ["abc"]
    assert output == []


def test_lt():
    program = """
    (define (cons x y) (rib x y 0))
    (cons (< 1 2)
    (cons (< 1 1)
    (cons (< 2 1)
        '())))
    """

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [[True, False, False]]
    assert output == []


def test_add():
    program = "(+ 1 2)"

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [3]
    assert output == []


def test_sub():
    program = "(- 123 234)"

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [-111]
    assert output == []



def test_quote():
    program = "'()"

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [[]]
    assert output == []


def test_lambda():
    program = """
    ((lambda (x y) (+ x y))
        14 28)
    """

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [42]
    assert output == []


def test_define():
    program = """
    (define (cons x y) (rib x y 0))

    (cons 1 '(2))
    """

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [[1, 2]]
    assert output == []


def test_draw():
    program = """
    (define poke (rib 21 0 1))
    (define screen 1024)
    (poke screen 65)
    """

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [65]
    assert output == []


def test_tty():
    program = """
    (define poke (rib 21 0 1))
    (define keyboard 2047)
    (poke keyboard 48)
    """

    inspect, output = run_to_halt(program, max_cycles=20000)

    assert inspect.stack() == [48]
    assert output == [ord('0')]


def run_to_halt(program, max_cycles=5000):
    """Compile and run a Scheme program, then return a function for inspecting the RAM, and a
    list of words that were written to the TTY port.
    """

    encoded = rvm.compile(program)
    # print(f"encoded program: {repr(encoded)}")

    asm = AssemblySource()

    rvm.interpreter(asm)

    rvm.decode(encoded, asm)

    instrs, symbols, _ = big.assemble(asm.lines, min_static=None, builtins=rvm.BUILTINS)

    computer = nand.syntax.run(big.BigComputer, simulator="vector")

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
