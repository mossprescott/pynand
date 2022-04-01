"""Solutions for project 05.

SPOILER ALERT: this files contains complete and optimal solutions for all the exercises.
If you want to solve them on your own, stop reading now!
"""

from nand.component import Const
from nand import RAM, ROM, Input, Output, chip, lazy
from nand.solutions.solved_01 import *
from nand.solutions.solved_02 import *
from nand.solutions.solved_03 import *


@chip
def MemorySystem(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    @chip
    def Shift13(inputs, outputs):
        outputs.out[0] = inputs.in_[13]
        outputs.out[1] = inputs.in_[14]

    @chip
    def Mask14(inputs, outputs):
        for i in range(14):
            outputs.out[i] = inputs.in_[i]

    bank = Shift13(in_=address).out
    load_bank = DMux4Way(in_=load, sel=bank)
    address14 = Mask14(in_=address).out

    # addresses 0x0000 to 0x3FFF
    ram = RAM(14)(in_=in_, load=Or(a=load_bank.a, b=load_bank.b).out, address=address14)

    # addresses 0x4000 to 0x5FFFF
    # note: bit 13 is definitely zero, so address[0..13] == address[0..12]
    screen = RAM(13)(in_=in_, load=load_bank.c, address=address14)

    # address 0x6000
    keyboard = Input()
    tty = Output(in_=in_, load=load_bank.d)

    # Note: this is mapping keyboard/input to _all_ high addresses, which definitely seems like
    # cheating.
    outputs.out = Mux4Way16(a=ram.out, b=ram.out, c=screen.out, d=keyboard.out, sel=bank).out

    # Tricky: need to expose some "output" from the Output component in order for the component
    # to be included in the synthesized IC. This ready bit might or might not be useful, but it
    # gets the job done.
    outputs.tty_ready = tty.ready


@chip
def CPU(inputs, outputs):
    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, _, _, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out

    alu = lazy()

    a_in = Mux16(a=instruction, b=alu.out, sel=i).out
    a_load = Or(a=not_i, b=da).out

    a_reg = Register(in_=a_in, load=a_load)
    d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
    pc = PC(in_=a_reg.out, load=jump, inc=1, reset=reset)
    alu.set(ALU(x=d_reg.out, y=Mux16(a=a_reg.out, b=inM, sel=a).out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))

    # Tricky: the memory now requires the address to be presented one-cycle ahead, so "pipeline"
    # it from the instruction/alu which is being written to A in this cycle.
    addr = Mux16(a=a_reg.out, b=a_in, sel=a_load).out

    outputs.outM = alu.out                   # M value output
    outputs.writeM = And(a=dm, b=i).out      # Write to M?
    outputs.addressM = addr                  # Address in data memory (of M) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)


@chip
def Computer(inputs, outputs):
    reset = inputs.reset

    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(CPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc

    # HACK: similar issues, but in this case it's just the particular component that
    # needs to be forced to be included.
    outputs.tty_ready = mem.tty_ready

    # TODO: would it be simpler to just wire up keyboard and tty as an ordinary
    # input and output of Computer? That's effectively the situation, and it's
    # currently just being handled in a sneakier way. Not sure how much mayhem that
    # would create.
    # keyboard = inputs.keyboard
    # outputs.tty = mem.tty
