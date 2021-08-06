# Computer Architecture
#
# See https://www.nand2tetris.org/project05

from nand import RAM, ROM, Input, build, lazy
from project_01 import *
from project_02 import *
from project_03 import *

# SOLVERS: remove this import to get started
from nand.solutions import solved_05


# Note: there is one additional required feature of the MemorySystem, compared to
# the original design according to From Nand To Tetris.
#
# When a value is written to the memory at address 0x6000, the value is stored in
# a special Output component, from which it can be accessed from the "outside".
# Together with the previously expected behavior when *reading* from that address,
# this makes it simple to hook a Computer up to something that looks like a terminal
# with both input (i.e the keyboard) and output (i.e. the "print" head.)
#
# If you want to think of the computer as small PC from the 80s, you can imagine
# that it provides a serial port to connect to a TTY. You would be really happy to
# have that if it was your job to debug the OS code for writing to the screen (and it
# will be — see project 12.)

def mkMemorySystem(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: you'll need a RAM(14), a RAM(13), an Input, and an Output.
    n1 = solved_05.MemorySystem(in_=in_, load=load, address=address)

    outputs.out = n1.out
    outputs.tty_ready = n1.tty_ready  # Wire this up to your Output component's "ready" signal.

MemorySystem = build(mkMemorySystem)


def mkCPU(inputs, outputs):
    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_05.CPU(inM=inM, instruction=instruction, reset=reset)

    outputs.outM = n1.outM           # M value output
    outputs.writeM = n1.writeM       # Write to M?
    outputs.addressM = n1.addressM   # Address in data memory (of M) (latched)
    outputs.pc = n1.pc               # address of next instruction (latched)

CPU = build(mkCPU)


# Note: there are a couple of required outputs for Computer, which aren't seen in
# the original design according to From Nand To Tetris.
#
# Fundamentally these are required just because of the way our simulators work;
# basically there has to be some output from each component or it will be
# "optimized" away when the chip is synthesized.
#
# "pc" is just the output from the CPU, and is sometimes useful for testing.
# "tty_ready" is the output from the MemorySystem, and it's not really useful
#    but it's the only available output so there you go.


def mkComputer(inputs, outputs):
    reset = inputs.reset

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_05.Computer(reset=reset)

    outputs.pc = n1.pc
    outputs.tty_ready = n1.tty_ready  # Note: wire this the output from MemorySystem

Computer = build(mkComputer)
