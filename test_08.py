import itertools

from nand import run
from project_05 import Computer
from project_06 import assemble

from project_08 import *


def test_basic_loop():
    translate = Translator()
    
    # Computes the sum 1 + 2 + ... + argument[0] and pushes the 
    # result onto the stack. Argument[0] is initialized by the test 
    # script before this code starts running.
    translate.push_constant(0)
    translate.pop_local(0)           # initializes sum = 0
    translate.label("LOOP_START")
    translate.push_argument(0)
    translate.push_local(0)
    translate.add()
    translate.pop_local(0)           # sum = sum + counter
    translate.push_argument(0)
    translate.push_constant(1)
    translate.sub()
    translate.pop_argument(0)        # counter--
    translate.push_argument(0)
    translate.if_goto("LOOP_START")  # If counter > 0, goto LOOP_START
    translate.push_local(0)

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)
    computer.poke(1, 300)
    computer.poke(2, 400)
    computer.poke(400, 3)

    translate.asm.run(assemble, computer, stop_cycles=600, debug=True)

    assert computer.peek(0) == 257
    assert computer.peek(256) == 6


def test_fibonacci_series():
    translate = Translator()
    
    # Puts the first argument[0] elements of the Fibonacci series
    # in the memory, starting in the address given in argument[1].
    # Argument[0] and argument[1] are initialized by the test script 
    # before this code starts running.
    translate.push_argument(1)
    translate.pop_pointer(1)           # that = argument[1]
    
    translate.push_constant(0)
    translate.pop_that(0)              # first element in the series = 0
    translate.push_constant(1)
    translate.pop_that(1)              # second element in the series = 1
    
    translate.push_argument(0)
    translate.push_constant(2)
    translate.sub()
    translate.pop_argument(0)          # num_of_elements -= 2 (first 2 elements are set)
    
    translate.label("MAIN_LOOP_START")
    
    translate.push_argument(0)
    translate.if_goto("COMPUTE_ELEMENT") # if num_of_elements > 0, goto COMPUTE_ELEMENT
    translate.goto("END_PROGRAM")        # otherwise, goto END_PROGRAM
    
    translate.label("COMPUTE_ELEMENT")
    
    translate.push_that(0)
    translate.push_that(1)
    translate.add()
    translate.pop_that(2)              # that[2] = that[0] + that[1]
    
    translate.push_pointer(1)
    translate.push_constant(1)
    translate.add()
    translate.pop_pointer(1)           # that += 1
    
    translate.push_argument(0)
    translate.push_constant(1)
    translate.sub()
    translate.pop_argument(0)          # num_of_elements--
    
    translate.goto("MAIN_LOOP_START")
    
    translate.label("END_PROGRAM")

    computer = run(Computer, simulator='codegen')

    computer.poke(0, 256)
    computer.poke(1, 300)
    computer.poke(2, 400)
    computer.poke(400, 6)
    computer.poke(401, 3000)

    translate.asm.run(assemble, computer, stop_cycles=1100, debug=True)

    assert computer.peek(3000) == 0
    assert computer.peek(3001) == 1
    assert computer.peek(3002) == 1
    assert computer.peek(3003) == 2
    assert computer.peek(3004) == 3
    assert computer.peek(3005) == 5


def test_simple_function():
    translate = Translator()

    # Performs a simple calculation and returns the result.
    translate.function("SimpleFunction", "test", 2)
    translate.push_local(0)
    translate.push_local(1)
    translate.add()
    translate.not_op()
    translate.push_argument(0)
    translate.add()
    translate.push_argument(1)
    translate.sub()
    translate.return_op()

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

    translate.asm.run(assemble, computer, debug=True)

    assert computer.peek(0) == 311
    assert computer.peek(1) == 305
    assert computer.peek(2) == 300
    assert computer.peek(3) == 3010
    assert computer.peek(4) == 4010
    assert computer.peek(310) == 1196


def test_nested_call():
    """Multiple function calls, with and without arguments.
    """
    
    translate = Translator()

    # Performs a simple calculation and returns the result.
    # Sys.init()
    #
    # Calls Sys.main() and stores return value in temp 1.
    # Does not return.  (Enters infinite loop.)

    translate.function("Sys", "init", 0)
    translate.push_constant(4000)	# test THIS and THAT context save
    translate.pop_pointer(0)
    translate.push_constant(5000)
    translate.pop_pointer(1)
    translate.call("Sys", "main", 0)
    translate.pop_temp(1)
    translate.label("LOOP")
    translate.goto("LOOP")

    # Sys.main()
    #
    # Sets locals 1, 2 and 3, leaving locals 0 and 4 unchanged to test
    # default local initialization to 0.  (RAM set to -1 by test setup.)
    # Calls Sys.add12(123) and stores return value (135) in temp 0.
    # Returns local 0 + local 1 + local 2 + local 3 + local 4 (456) to confirm
    # that locals were not mangled by function call.

    translate.function("Sys", "main", 5)
    translate.push_constant(4001)
    translate.pop_pointer(0)
    translate.push_constant(5001)
    translate.pop_pointer(1)
    translate.push_constant(200)
    translate.pop_local(1)
    translate.push_constant(40)
    translate.pop_local(2)
    translate.push_constant(6)
    translate.pop_local(3)
    translate.push_constant(123)
    translate.call("Sys", "add12", 1)
    translate.pop_temp(0)
    translate.push_local(0)
    translate.push_local(1)
    translate.push_local(2)
    translate.push_local(3)
    translate.push_local(4)
    translate.add()
    translate.add()
    translate.add()
    translate.add()
    translate.return_op()

    # Sys.add12(int n)
    #
    # Returns n+12.

    translate.function("Sys", "add12", 0)
    translate.push_constant(4002)
    translate.pop_pointer(0)
    translate.push_constant(5002)
    translate.pop_pointer(1)
    translate.push_argument(0)
    translate.push_constant(12)
    translate.add()
    translate.return_op()


    computer = run(Computer, simulator='codegen')

    computer.poke(0, 261)
    computer.poke(1, 261)
    computer.poke(2, 256)
    computer.poke(3, -3)
    computer.poke(4, -4)
    computer.poke(5, -1)  # test results
    computer.poke(6, -1)
    computer.poke(256, 1234) # fake stack frame from call Sys.init
    computer.poke(257, -1)
    computer.poke(258, -2)
    computer.poke(259, -3)
    computer.poke(260, -4)
    # Initialize stack to check for local segment
    # being cleared to zero.
    for i in range(261, 300):
        computer.poke(i, -1)

    translate.asm.run(assemble, computer, stop_cycles=4000, debug=True)

    assert computer.peek(0) == 261
    assert computer.peek(1) == 261
    assert computer.peek(2) == 256
    assert computer.peek(3) == 4000
    assert computer.peek(4) == 5000
    assert computer.peek(5) == 135
    assert computer.peek(6) == 246


def test_fibonacci_element():
    """Sys.init, declared out of sequence, requiring the translator to supply initialization and then 
    call Sys.init. This is finally a fully legitimate VM program, executed in the normal way.
    """
    
    translate = Translator()
  
    # Note: seems like this should just happen, but the previous tests actually require it _not_ to.
    translate.preamble()
    
    # Main.vm:
    # Computes the n'th element of the Fibonacci series, recursively.
    # n is given in argument[0].  Called by the Sys.init function 
    # (part of the Sys.vm file), which also pushes the argument[0] 
    # parameter before this code starts running.
    translate.function("Main", "fibonacci", 0)
    translate.push_argument(0)
    translate.push_constant(2)
    translate.lt()                          # checks if n<2
    translate.if_goto("IF_TRUE")
    translate.goto("IF_FALSE")
    translate.label("IF_TRUE")              # if n<2, return n
    translate.push_argument(0)        
    translate.return_op()
    translate.label("IF_FALSE")             # if n>=2, returns fib(n-2)+fib(n-1)
    translate.push_argument(0)
    translate.push_constant(2)
    translate.sub()
    translate.call("Main", "fibonacci", 1)  # computes fib(n-2)
    translate.push_argument(0)
    translate.push_constant(1)
    translate.sub()
    translate.call("Main", "fibonacci", 1)  # computes fib(n-1)
    translate.add()                         # returns fib(n-1) + fib(n-2)
    translate.return_op()
  
    # Sys.vm:
    # Pushes a constant, say n, onto the stack, and calls the Main.fibonacci
    # function, which computes the n'th element of the Fibonacci series.
    # Note that by convention, the Sys.init function is called "automatically" 
    # by the bootstrap code.
    translate.function("Sys", "init", 0)
    translate.push_constant(4)
    translate.call("Main", "fibonacci", 1)   # computes the 4'th fibonacci element
    translate.label("WHILE")
    translate.goto("WHILE")                  # loops infinitely


    computer = run(Computer, simulator='codegen')

    # Note: no initialization this time
    
    translate.asm.run(assemble, computer, stop_cycles=2000, debug=True)

    assert computer.peek(0) == 262
    assert computer.peek(261) == 3


def test_statics_multiple_files():
    """Tests that different functions, stored in two different classes, manipulate the static 
    segment correctly. 
    
    Note: the original materials actually refer to _files_ not _classes_, but I think in the context
    of this language there's a one-to-one correspondence.
    """
    
    translate = Translator()
  
    # Note: seems like this should just happen, but the previous tests actually require it _not_ to.
    translate.preamble()
    
    # Sys.vm:
    translate.function("Sys", "init", 0)
    translate.push_constant(6)
    translate.push_constant(8)
    translate.call("Class1", "set", 2)
    translate.pop_temp(0) # Dumps the return value
    translate.push_constant(23)
    translate.push_constant(15)
    translate.call("Class2", "set", 2)
    translate.pop_temp(0) # Dumps the return value
    translate.call("Class1", "get", 0)
    translate.call("Class2", "get", 0)
    translate.label("WHILE")
    translate.goto("WHILE")

    for class_name in ["Class1", "Class2"]:
        # Stores two supplied arguments in static[0] and static[1].
        translate.function(class_name, "set", 0)
        translate.push_argument(0)
        translate.pop_static(0)
        translate.push_argument(1)
        translate.pop_static(1)
        translate.push_constant(0)
        translate.return_op()
        # Returns static[0] - static[1].
        translate.function(class_name, "get", 0)
        translate.push_static(0)
        translate.push_static(1)
        translate.sub()
        translate.return_op()


    computer = run(Computer, simulator='codegen')

    # Note: no initialization this time

    translate.asm.run(assemble, computer, stop_cycles=2500, debug=True)

    assert computer.peek(0) == 263
    assert computer.peek(261) == -2
    assert computer.peek(262) == 8
