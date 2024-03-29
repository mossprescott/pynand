#! /usr/bin/env pytest

from nand import run, unsigned
# Note: using the included implementations, so you can work on the projects in any order
from nand.solutions import solved_05, solved_06

from project_04 import *


def test_mult(Computer=solved_05.Computer, assemble=solved_06.assemble):
    computer = run(Computer)

    pgm, _, _ = assemble(MULT_ASM)
    computer.init_rom(pgm)

    computer.poke(2, -1)
    for _ in range(20):
        computer.ticktock()
    assert computer.peek(2) == 0

    computer.poke(0, 1)
    computer.poke(2, -1)
    computer.reset_program()
    for _ in range(50):
        computer.ticktock()
    assert computer.peek(2) == 0

    computer.poke(0, 0)
    computer.poke(1, 2)
    computer.poke(2, -1)
    computer.reset_program()
    for _ in range(80):
        computer.ticktock()
    assert computer.peek(2) == 0

    computer.poke(0, 3)
    computer.poke(1, 1)
    computer.poke(2, -1)
    computer.reset_program()
    for _ in range(120):
        computer.ticktock()
    assert computer.peek(2) == 3

    computer.poke(0, 2)
    computer.poke(1, 4)
    computer.poke(2, -1)
    computer.reset_program()
    for _ in range(150):
        computer.ticktock()
    assert computer.peek(2) == 8

    computer.poke(0, 6)
    computer.poke(1, 7)
    computer.poke(2, -1)
    computer.reset_program()
    for _ in range(210):
        computer.ticktock()
    assert computer.peek(2) == 42


def test_fill(Computer=solved_05.Computer, assemble=solved_06.assemble):
    # We're going to run a few million cycles, so the faster simulator is a better option:
    computer = run(Computer, simulator='codegen')

    pgm, _, _ = assemble(FILL_ASM)
    computer.init_rom(pgm)

    computer.set_keydown(0)  # the keyboard is untouched
    for _ in range(1_000_000):
        computer.ticktock()
    for i in range(256*512//16):
        assert unsigned(computer.peek_screen(i)) == 0x0000  # white

    computer.set_keydown(1)  # a keyboard key is pressed
    for _ in range(1_000_000):
        computer.ticktock()
    for i in range(256*512//16):
        assert unsigned(computer.peek_screen(i)) == 0xffff  # black

    computer.set_keydown(0)  # the keyboard is untouched
    for _ in range(1_000_000):
        computer.ticktock()
    for i in range(256*512//16):
        assert unsigned(computer.peek_screen(i)) == 0x0000  # white
