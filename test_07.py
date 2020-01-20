from nand import run
from project_05 import Computer
from project_06 import assemble

from project_07 import *

def test_simple_add():
    ADD = """
        // Pushes and adds two constants.
        push constant 7
        push constant 8
        add
        """.split('\n')

    asm = translate(ADD)
    print('\n'.join(asm))

    pgm = assemble(asm)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)  # initializes the stack pointer

    computer.init_rom(pgm)
    for _ in range(60):
        computer.ticktock()

    assert computer.peek(0) == 257
    assert computer.peek(256) == 15
