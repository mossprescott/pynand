from nand import RAM, ROM, Input, build, lazy
from project_01 import *
from project_02 import *
from project_03 import *

# SOLVERS: remove this import to get started
from nand.solutions import solved_05


def mkMemorySystem(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: you'll need a RAM(14), a RAM(13), and an Input.
    n1 = solved_05.MemorySystem(in_=in_, load=load, address=address)

    outputs.out = n1.out

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


def mkComputer(inputs, outputs):
    reset = inputs.reset
    
    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_05.Computer(reset=reset)

    outputs.pc = n1.pc

Computer = build(mkComputer)
