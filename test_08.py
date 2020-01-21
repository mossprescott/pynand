import itertools

from nand import run
from project_05 import Computer
from project_06 import assemble

from project_08 import *

from nand.solutions.solved_07 import print_vm_state


def test_basic_loop():
    translate = Translator()
    
    # Computes the sum 1 + 2 + ... + argument[0] and pushes the 
    # result onto the stack. Argument[0] is initialized by the test 
    # script before this code starts running.
    BASIC_LOOP = list(itertools.chain(
        translate.push_constant(0),
        translate.pop_local(0),           # initializes sum = 0
        translate.label("LOOP_START"),
        translate.push_argument(0),
        translate.push_local(0),
        translate.add(),
        translate.pop_local(0),           # sum = sum + counter
        translate.push_argument(0),
        translate.push_constant(1),
        translate.sub(),
        translate.pop_argument(0),        # counter--
        translate.push_argument(0),
        translate.if_goto("LOOP_START"),  # If counter > 0, goto LOOP_START
        translate.push_local(0),
    ))

    pgm = assemble(BASIC_LOOP)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)
    computer.poke(1, 300)
    computer.poke(2, 400)
    computer.poke(400, 3)

    computer.init_rom(pgm)
    for _ in range(600):
        computer.ticktock()

    assert computer.peek(0) == 257
    assert computer.peek(256) == 6
