import itertools

from nand import run
from project_05 import Computer
from project_06 import assemble

from project_07 import *



def test_simple_add():
    translate = Translator()
    
    # Pushes and adds two constants
    SIMPLE_ADD = list(itertools.chain(
        translate.push_constant(7),
        translate.push_constant(8),
        translate.add(),
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
    translate = Translator()
    
    STACK_TEST = list(itertools.chain(
        translate.push_constant(17),
        translate.push_constant(17),
        translate.eq(),
        
        translate.push_constant(17),
        translate.push_constant(16),
        translate.eq(),
        
        translate.push_constant(16),
        translate.push_constant(17),
        translate.eq(),
        
        translate.push_constant(892),
        translate.push_constant(891),
        translate.lt(),
        
        translate.push_constant(891),
        translate.push_constant(892),
        translate.lt(),
        
        translate.push_constant(891),
        translate.push_constant(891),
        translate.lt(),
        
        translate.push_constant(32767),
        translate.push_constant(32766),
        translate.gt(),
        
        translate.push_constant(32766),
        translate.push_constant(32767),
        translate.gt(),
        
        translate.push_constant(32766),
        translate.push_constant(32766),
        translate.gt(),
        
        translate.push_constant(57),
        translate.push_constant(31),
        translate.push_constant(53),
        translate.add(),
        translate.push_constant(112),
        translate.sub(),
        translate.neg(),
        translate.and_op(),
        translate.push_constant(82),
        translate.or_op(),
        translate.not_op(),
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
