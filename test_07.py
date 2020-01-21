import itertools

from nand import run
from project_05 import Computer
from project_06 import assemble

from project_07 import *

from nand.solutions.solved_07 import print_vm_state


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
    for _ in range(len(pgm)):
        computer.ticktock()

    assert computer.peek(0) == 257
    assert computer.peek(256) == 15


def test_stack_ops():
    translate = Translator()
    
    # Executes a sequence of arithmetic and logical operations
    # on the stack. 
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
    for _ in range(len(pgm)):
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


def test_memory_access_basic():
    translate = Translator()
    
    # Executes pop and push commands using the virtual memory segments.
    BASIC_TEST = list(itertools.chain(
        translate.push_constant(10),
        translate.pop_local(0),
        translate.push_constant(21),
        translate.push_constant(22),
        translate.pop_argument(2),
        translate.pop_argument(1),
        translate.push_constant(36),
        translate.pop_this(6),
        translate.push_constant(42),
        translate.push_constant(45),
        translate.pop_that(5),
        translate.pop_that(2),
        translate.push_constant(510),
        translate.pop_temp(6),
        translate.push_local(0),
        translate.push_that(5),
        translate.add(),
        translate.push_argument(1),
        translate.sub(),
        translate.push_this(6),
        translate.push_this(6),
        translate.add(),
        translate.sub(),
        translate.push_temp(6),
        translate.add(),
    ))

    pgm = assemble(BASIC_TEST)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)   # stack pointer
    computer.poke(1, 300)   # base address of the local segment
    computer.poke(2, 400)   # base address of the argument segment
    computer.poke(3, 3000)  # base address of the this segment
    computer.poke(4, 3010)  # base address of the that segment

    computer.init_rom(pgm)
    for _ in range(len(pgm)):
        computer.ticktock()

    assert computer.peek(256) == 472
    assert computer.peek(300) == 10
    assert computer.peek(401) == 21
    assert computer.peek(402) == 22
    assert computer.peek(3006) == 36
    assert computer.peek(3012) == 42
    assert computer.peek(3015) == 45
    assert computer.peek(11) == 510


def test_memory_access_pointer():
    translate = Translator()
    
    # Executes pop and push commands using the
    # pointer, this, and that segments.
    POINTER_TEST = list(itertools.chain(
        translate.push_constant(3030),
        translate.pop_pointer(0),
        translate.push_constant(3040),
        translate.pop_pointer(1),
        translate.push_constant(32),
        translate.pop_this(2),
        translate.push_constant(46),
        translate.pop_that(6),
        translate.push_pointer(0),
        translate.push_pointer(1),
        translate.add(),
        translate.push_this(2),
        translate.sub(),
        translate.push_that(6),
        translate.add(),
    ))
    
    pgm = assemble(POINTER_TEST)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)   # stack pointer

    computer.init_rom(pgm)
    for _ in range(len(pgm)):
        computer.ticktock()

    assert computer.peek(256) == 6084
    assert computer.peek(3) == 3030
    assert computer.peek(4) == 3040
    assert computer.peek(3032) == 32
    assert computer.peek(3046) == 46
    
    
def test_memory_access_static():
    translate = Translator()
    
    # Executes pop and push commands using the static segment.
    STATIC_TEST = list(itertools.chain(
        translate.push_constant(111),
        translate.push_constant(333),
        translate.push_constant(888),
        translate.pop_static(8),
        translate.pop_static(3),
        translate.pop_static(1),
        translate.push_static(3),
        translate.push_static(1),
        translate.sub(),
        translate.push_static(8),
        translate.add(),
    ))

    pgm = assemble(STATIC_TEST)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)   # stack pointer

    computer.init_rom(pgm)
    for _ in range(len(pgm)):
        computer.ticktock()

    assert computer.peek(256) == 1110
