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


def test_fibonacci_series():
    translate = Translator()
    
    # Puts the first argument[0] elements of the Fibonacci series
    # in the memory, starting in the address given in argument[1].
    # Argument[0] and argument[1] are initialized by the test script 
    # before this code starts running.
    FIBONACCI_SERIES = list(itertools.chain(
        translate.push_argument(1),
        translate.pop_pointer(1),           # that = argument[1]
        
        translate.push_constant(0),
        translate.pop_that(0),              # first element in the series = 0
        translate.push_constant(1),
        translate.pop_that(1),              # second element in the series = 1
        
        translate.push_argument(0),
        translate.push_constant(2),
        translate.sub(),
        translate.pop_argument(0),          # num_of_elements -= 2 (first 2 elements are set)
        
        translate.label("MAIN_LOOP_START"),
        
        translate.push_argument(0),
        translate.if_goto("COMPUTE_ELEMENT"), # if num_of_elements > 0, goto COMPUTE_ELEMENT
        translate.goto("END_PROGRAM"),        # otherwise, goto END_PROGRAM
        
        translate.label("COMPUTE_ELEMENT"),
        
        translate.push_that(0),
        translate.push_that(1),
        translate.add(),
        translate.pop_that(2),              # that[2] = that[0] + that[1]
        
        translate.push_pointer(1),
        translate.push_constant(1),
        translate.add(),
        translate.pop_pointer(1),           # that += 1
        
        translate.push_argument(0),
        translate.push_constant(1),
        translate.sub(),
        translate.pop_argument(0),          # num_of_elements--
        
        translate.goto("MAIN_LOOP_START"),
        
        translate.label("END_PROGRAM"),
    ))

    pgm = assemble(FIBONACCI_SERIES)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)
    computer.poke(1, 300)
    computer.poke(2, 400)
    computer.poke(400, 6)
    computer.poke(401, 3000)

    computer.init_rom(pgm)
    for _ in range(1100):
        computer.ticktock()

    assert computer.peek(3000) == 0
    assert computer.peek(3001) == 1
    assert computer.peek(3002) == 1
    assert computer.peek(3003) == 2
    assert computer.peek(3004) == 3
    assert computer.peek(3005) == 5


def test_simple_function():
    translate = Translator()

    # Performs a simple calculation and returns the result.
    SIMPLE_FUNCTION = list(itertools.chain(
        translate.function("SimpleFunction", "test", 2),
        translate.push_local(0),
        translate.push_local(1),
        translate.add(),
        translate.not_op(),
        translate.push_argument(0),
        translate.add(),
        translate.push_argument(1),
        translate.sub(),
        translate.return_op(),
    ))

    pgm = assemble(SIMPLE_FUNCTION)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 317)
    computer.poke(1, 317)
    computer.poke(2, 310)
    computer.poke(3, 3000)
    computer.poke(4, 4000)
    computer.poke(310, 1234)
    computer.poke(311, 37)
    computer.poke(312, 1000)
    computer.poke(313, 305)
    computer.poke(314, 300)
    computer.poke(315, 3010)
    computer.poke(316, 4010)

    computer.init_rom(pgm)
    for _ in range(len(pgm)):
        computer.ticktock()

    assert computer.peek(0) == 311
    assert computer.peek(1) == 305
    assert computer.peek(2) == 300
    assert computer.peek(3) == 3010
    assert computer.peek(4) == 4010
    assert computer.peek(310) == 1196
