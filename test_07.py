import itertools

from nand import run
from project_05 import Computer
from project_06 import assemble

from project_07 import *

def test_simple_add():
    # Pushes and adds two constants
    ADD = list(itertools.chain(
        translate_push_constant(7),
        translate_push_constant(8),
        translate_add(),
    ))

    pgm = assemble(ADD)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)  # initializes the stack pointer

    computer.init_rom(pgm)
    for _ in range(60):
        computer.ticktock()
        # print(f"PC: {computer.pc}; SP: {computer.peek(0)}; RAM[256]: {computer.peek(256)}")

    assert computer.peek(0) == 257
    assert computer.peek(256) == 15
