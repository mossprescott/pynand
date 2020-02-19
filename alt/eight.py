"""An attempt at a _smaller_ CPU, by reducing the ALU and data paths to only 8 bits, and taking 
two cycles for every instruction. This is the classic "low-cost" CPU move (examples include the 
Motorola 68000), promising compatibility with fancier architectures, and then delivering 
seriously compromised performance, or conversely, locking users into an architecture so they can
later be upsold to more expensive models.

To that end, 8-bit versions of all the components are defined, plus components to pack/unpack 
them into 16-bit values for communication with the ROM and memory (which are shared with the 
normal chip.) Some of the 8-bit components have additional inputs and outputs to allow for 
propagating carry bits from one word the the next.
"""

import re

from nand import *
from nand.translate import AssemblySource, translate_dir

from nand.solutions.solved_01 import And, Or, Not, Xor
from nand.solutions.solved_02 import HalfAdder, FullAdder
from nand.solutions.solved_03 import Bit
from nand.solutions.solved_05 import MemorySystem
from nand.solutions import solved_06
from nand.solutions import solved_07


# Project 01:

def mkNot8(inputs, outputs):
    in_ = inputs.in_
    for i in range(8):
        outputs.out[i] = Not(in_=in_[i]).out

Not8 = build(mkNot8)
        

def mkAnd8(inputs, outputs):
    for i in range(8):
        outputs.out[i] = And(a=inputs.a[i], b=inputs.b[i]).out

And8 = build(mkAnd8)


def mkMux8(inputs, outputs):
    not_sel = Not(in_=inputs.sel).out
    for i in range(8):
        fromAneg = Nand(a=inputs.a[i], b=not_sel).out
        fromBneg = Nand(a=inputs.b[i], b=inputs.sel).out
        outputs.out[i] = Nand(a=fromAneg, b=fromBneg).out

Mux8 = build(mkMux8)


# Project 02:

def mkInc8(inputs, outputs):
    """Note: this is subtly different than Inc16 in that it may or may not actually increment
    the value, under the control of carry_in. This allows the carry to propagate from the low 
    word to the high word.
    """
    carry = inputs.carry_in
    for i in range(8):
        tmp = HalfAdder(a=carry, b=inputs.in_[i])
        outputs.out[i] = tmp.sum
        carry = tmp.carry
    outputs.carry_out = carry

Inc8 = build(mkInc8)


def mkAdd8(inputs, outputs):
    carry = inputs.carry_in
    for i in range(8):
        tmp = FullAdder(a=inputs.a[i], b=inputs.b[i], c=carry)
        outputs.out[i] = tmp.sum
        carry = tmp.carry
    outputs.carry_out = carry

Add8 = build(mkAdd8)


def mkZero8(inputs, outputs):
    in_ = inputs.in_
    outputs.out = And(
        a=And(a=And(a=Not(in_=in_[ 7]).out,
                    b=Not(in_=in_[ 6]).out).out,
              b=And(a=Not(in_=in_[ 5]).out,
                    b=Not(in_=in_[ 4]).out).out).out,
        b=And(a=And(a=Not(in_=in_[ 3]).out,
                    b=Not(in_=in_[ 2]).out).out,
              b=And(a=Not(in_=in_[ 1]).out,
                    b=Not(in_=in_[ 0]).out).out).out).out
Zero8 = build(mkZero8)


def mkNeg8(inputs, outputs):
    outputs.out = inputs.in_[7]

Neg8 = build(mkNeg8)


def mkEightALU(inputs, outputs):
    x = inputs.x
    y = inputs.y
    carry_in = inputs.carry_in
    
    zx = inputs.zx
    nx = inputs.nx
    zy = inputs.zy
    ny = inputs.ny
    f  = inputs.f
    no = inputs.no
    
    x_zeroed = Mux8(a=x, b=0, sel=zx).out
    y_zeroed = Mux8(a=y, b=0, sel=zy).out

    x_inverted = Mux8(a=x_zeroed, b=Not8(in_=x_zeroed).out, sel=nx).out
    y_inverted = Mux8(a=y_zeroed, b=Not8(in_=y_zeroed).out, sel=ny).out
    
    anded = And8(a=x_inverted, b=y_inverted)
    added = Add8(a=x_inverted, b=y_inverted, carry_in=carry_in)
    
    result = Mux8(a=anded.out, b=added.out, sel=f).out
    result_inverted = Not8(in_=result).out
    
    out = Mux8(a=result, b=result_inverted, sel=no).out
    
    outputs.out = out
    outputs.zr = Zero8(in_=out).out
    outputs.ng = Neg8(in_=out).out
    
    # Note: need one more output to track overflow from the low half-word.
    outputs.carry_out = And(a=f, b=added.carry_out).out

EightALU = build(mkEightALU)


# Project 03:

def mkRegister8(inputs, outputs):
    for i in range(8):
        outputs.out[i] = Bit(in_=inputs.in_[i], load=inputs.load).out

Register8 = build(mkRegister8)


def mkPC8(inputs, outputs):
    """15-bit PC, built from two 8-bit registers and a single Inc8.
    
    On the first half-cycle, the low half-word is incremented, but the output 
    is not yet updated. On the second half-cycle, the high half-word is 
    incremented, and then the two half-words appear together at the same time.
    
    That way, the address presented to the ROM is consistently correct, and the 
    instruction word can be read in both half-cycles.
    """

    top_half = inputs.top_half
    bottom_half = inputs.bottom_half

    in_ = inputs.in_
    load = inputs.load
    reset = inputs.reset
    
    in_split = Split(in_=in_)
    in_lo = in_split.lo
    in_hi = in_split.hi
    
    reseted = lazy()

    pc_lo_next = Register8(in_=reseted.out, load=top_half)
    pc_lo = Register8(in_=pc_lo_next.out, load=bottom_half)
    pc_hi = Register8(in_=reseted.out, load=bottom_half)

    # Clever? Can tell if overflow happened by inspecting the high bits of the old and new low words.
    carry_in = And(a=pc_lo.out[7], b=Not(in_=pc_lo_next.out[7]).out).out
    
    inced =     Inc8(in_=Mux8(a=pc_lo.out, b=pc_hi.out, sel=bottom_half).out, carry_in=Or(a=top_half, b=carry_in).out)
    loaded =    Mux8(a=inced.out, b=Mux8(a=in_lo, b=in_hi, sel=bottom_half).out, sel=load)
    reseted.set(Mux8(a=loaded.out, b=0, sel=reset))

    outputs.out = Splice(lo=pc_lo.out, hi=pc_hi.out).out  # 16 bits

PC8 = build(mkPC8)


# Project 05:



def mkEightCPU(inputs, outputs):
    """Implement the 16-bit Hack instruction set using a single 8-bit ALU and 8-bit 
    """
    
    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, _, _, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    # not_i = Not(in_=i).out
   
    alu = lazy()
    # a_reg = Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=da).out)
    # d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    # jump_lt = And(a=alu.ng, b=jlt).out
    # jump_eq = And(a=alu.zr, b=jeq).out
    # jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    # jump = And(a=i,
    #            b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
    #           ).out
    # pc = PC(in_=a_reg.out, load=jump, inc=1, reset=reset)
    a_lo_reg = Register8(in_=0, load=0)
    a_hi_reg = Register8(in_=0, load=0)
    d_lo_reg = Register8(in_=0, load=0)
    d_hi_reg = Register8(in_=0, load=0)
    
    alu.set(ALU(x=d_reg.out, y=Mux16(a=a_reg.out, b=inM, sel=a).out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))


    outputs.outM = alu.out                   # M value output
    outputs.writeM = And(a=dm, b=i).out      # Write to M?
    outputs.addressM = a_reg.out             # Address in data memory (of M) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)
    
EightCPU = build(mkEightCPU)


def mkEightComputer(inputs, outputs):
    reset = inputs.reset
    
    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(EightCPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc
    
EightComputer = build(mkEightComputer)


# 8-bit adapters:

def mkSplice(inputs, outputs):
    for i in range(8):
        outputs.out[i] = inputs.lo[i]
        outputs.out[i+8] = inputs.hi[i]
Splice = build(mkSplice)

def mkSplit(inputs, outputs):
    for i in range(8):
        outputs.lo[i] = inputs.in_[i]
        outputs.hi[i] = inputs.in_[i+8]
Split = build(mkSplit)


# Main:

import computer

EIGHT_PLATFORM = computer.Platform(
    chip=EightComputer,
    assemble=solved_06.assemble,
    parse_line=solved_07.parse_line,
    translator=solved_07.Translator)

if __name__ == "__main__":
    computer.main(EIGHT_PLATFORM)
