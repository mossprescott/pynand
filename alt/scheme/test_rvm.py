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

    symbols_by_addr = { addr: name for (name, addr) in symbols.items() }

    for addr, name in symbols_by_addr.items():
        print(f"{addr}: {name}")

    def show_addr(addr):
        # addr = unsigned
        if addr in symbols_by_addr:
            return f"{symbols_by_addr[addr]} (@{addr})"
        else:
            return f"@{addr}"


    computer = nand.syntax.run(big.BigComputer, simulator="vector")

    computer.init_rom(instrs)

    # Jump over low memory that we might be using for debugging:
    computer.poke(0, big.ROM_BASE)
    computer.poke(1, big.parse_op("0;JMP"))

    cycles = 0
    output = []

    while (not computer.fetch or computer.pc != symbols["halt_loop"]) and cycles <= max_cycles:
        computer.ticktock()
        cycles += 1

        tty_char = computer.get_tty()
        if tty_char:
            output.append(tty_char)

        if computer.fetch:
            print(f"pc: {show_addr(computer.pc)}; PC: {show_addr(computer.peek(1))}")

    inspect = Inspector(computer, symbols)

    return (inspect, output)
