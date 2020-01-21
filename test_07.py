import itertools

from nand import run
from project_05 import Computer
from project_06 import assemble

from project_07 import *

from nand.solutions.solved_07 import make_label_gen


label_gen = make_label_gen()


def test_simple_add():
    # Pushes and adds two constants
    SIMPLE_ADD = list(itertools.chain(
        translate_push_constant(label_gen, 7),
        translate_push_constant(label_gen, 8),
        translate_add(label_gen),
    ))

    pgm = assemble(SIMPLE_ADD)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)  # initializes the stack pointer

    computer.init_rom(pgm)
    for _ in range(60):
        computer.ticktock()
        # print(f"PC: {computer.pc}; SP: {computer.peek(0)}; RAM[256]: {computer.peek(256)}")

    assert computer.peek(0) == 257
    assert computer.peek(256) == 15


def test_stack_ops():
    STACK_TEST = list(itertools.chain(
        translate_push_constant(label_gen, 17),
        translate_push_constant(label_gen, 17),
        translate_eq(label_gen),
        
        translate_push_constant(label_gen, 17),
        translate_push_constant(label_gen, 16),
        translate_eq(label_gen),
        
        translate_push_constant(label_gen, 16),
        translate_push_constant(label_gen, 17),
        translate_eq(label_gen),
        
        translate_push_constant(label_gen, 892),
        translate_push_constant(label_gen, 891),
        translate_lt(label_gen),
        
        translate_push_constant(label_gen, 891),
        translate_push_constant(label_gen, 892),
        translate_lt(label_gen),
        
        translate_push_constant(label_gen, 891),
        translate_push_constant(label_gen, 891),
        translate_lt(label_gen),
        
        translate_push_constant(label_gen, 32767),
        translate_push_constant(label_gen, 32766),
        translate_gt(label_gen),
        
        translate_push_constant(label_gen, 32766),
        translate_push_constant(label_gen, 32767),
        translate_gt(label_gen),
        
        translate_push_constant(label_gen, 32766),
        translate_push_constant(label_gen, 32766),
        translate_gt(label_gen),
        
        translate_push_constant(label_gen, 57),
        translate_push_constant(label_gen, 31),
        translate_push_constant(label_gen, 53),
        translate_add(label_gen),
        translate_push_constant(label_gen, 112),
        translate_sub(label_gen),
        translate_neg(label_gen),
        translate_and(label_gen),
        translate_push_constant(label_gen, 82),
        translate_or(label_gen),
        translate_not(label_gen),
    ))

    pgm = assemble(STACK_TEST)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)  # initializes the stack pointer

    computer.init_rom(pgm)
    for _ in range(1000):
        computer.ticktock()

    assert computer.peek(0) == 266
    assert computer.peek(256) == -1
    assert computer.peek(257) == 0
    assert computer.peek(258) == 0
    assert computer.peek(259) == 0
    assert computer.peek(260) == -1
    assert computer.peek(261) == 0
    assert computer.peek(262) == -1
    assert computer.peek(263) == 0
    assert computer.peek(264) == 0
    assert computer.peek(265) == -91
