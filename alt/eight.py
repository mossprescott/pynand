"""An attempt at a _smaller_ CPU, by reducing the ALU and data paths to only 8 bits, and taking 
two cycles for every instruction. This is the classic "low-cost" CPU move (examples include the 
Motorola 68000, and various 4/8- and 8/16-bit CPUs before that), promising compatibility with 
fancier architectures, and then delivering seriously compromised performance, or conversely, 
locking users into an architecture so they can later be upsold to more expensive models.

To that end, 8-bit versions of all the components are defined, plus components to pack/unpack 
them into 16-bit values for communication with the ROM and memory (which are shared with the 
normal chip.) Some of the 8-bit components have additional inputs and outputs to allow for 
propagating carry bits from one word the the next.

In a real design, the memory bus, etc. would also be reduced in width since there is now only 
one address/data word to move every two cycles, but to keep things simple the idea here is that
the chip has exactly the same external interface.

The question is: how close can this get to 50% smaller? No doubt there will be some overhead to
keep track of half-cycles, and to propagate carries, etc.

Note: this implementation defines _only_ a new CPU/Computer, which implements exactly the same 
instruction set as the standard Hack CPU, so the same assembler and VM translator can be used. 
The only way to tell them apart from the outside is to notice that each cycle makes half as 
much progress.
"""

import re

from nand import *
from nand.translate import AssemblySource, translate_dir

from nand.solutions.solved_01 import And, Or, Not, Xor, Mux, Mux16
from nand.solutions.solved_02 import HalfAdder, FullAdder
from nand.solutions.solved_03 import Bit
from nand.solutions.solved_05 import MemorySystem, PC
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
    """Eight-bit ALU, with one addition:
    
    The single low bit carry_in is added along with x and y, and the carry_out from that operation
    is exposed. Note that carry_out reflects the result of addition, whether or not the sum is used 
    (f) and whether or not the result is negated (no).
    """

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
    outputs.carry_out = added.carry_out

EightALU = build(mkEightALU)


# Project 03:

def mkRegister8(inputs, outputs):
    for i in range(8):
        outputs.out[i] = Bit(in_=inputs.in_[i], load=inputs.load).out

Register8 = build(mkRegister8)


def mkPC8(inputs, outputs):
    """16-bit PC, built from two 8-bit registers and a single Inc8.

    On the first half-cycle, the low half-word is incremented but not yet stored.
    On the second half-cycle, the high half-word is incremented, and then the two half-words 
    appear together at the same time.

    That way, the address presented to the ROM is consistently correct, and the instruction word 
    can be read in both half-cycles.
    
    Note: all that fanciness means that this component doesn't save much compared to the normal 
    PC. It might be better to just use that and only increment it on every other cycle.
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
    # Note: want reset to happen immediately, but this way probably means some duplication
    pc_lo = Register8(in_=Mux8(a=Mux8(a=pc_lo_next.out, b=in_lo, sel=load).out, b=0, sel=reset).out, load=Or_(bottom_half, reset, load))
    pc_hi = Register8(in_=reseted.out, load=bottom_half)

    # Clever? Can tell if overflow happened by inspecting the high bits of the old and new low words.
    carry_in = And(a=pc_lo.out[7], b=Not(in_=pc_lo_next.out[7]).out).out

    inced =     Inc8(in_=Mux8(a=pc_lo.out, b=pc_hi.out, sel=bottom_half).out, carry_in=Or(a=top_half, b=carry_in).out)
    loaded =    Mux8(a=inced.out, b=Mux8(a=in_lo, b=in_hi, sel=bottom_half).out, sel=load)
    reseted.set(Mux8(a=loaded.out, b=0, sel=reset))

    outputs.out = Splice(lo=pc_lo.out, hi=pc_hi.out).out

PC8 = build(mkPC8)


# Project 05:

# TODO: move to nand.syntax? project_01?
def And_(x, *xs):
    if not xs:
        return x
    else :
        return And(a=x, b=And_(xs[0], *xs[1:])).out

# TODO: move to nand.syntax? project_01?
def Or_(x, *xs):
    if not xs:
        return x
    else:
        return Or(a=x, b=Or_(xs[0], *xs[1:])).out

# TODO: move to nand.syntax? project_01?
# Or just make it support this syntax somehow
def Not_(x):
    return Not(in_=x).out


def mkEightCPU(inputs, outputs):
    """Implement the 16-bit Hack instruction set using a single 8-bit ALU and a pair of 8-bit 
    registers for each architectural register, plus some extra flip-flops to keep track of state
    in between two "half"-cycles.
    
    In the first cycle, the low half-word of results is computed. In the second cycle, the high 
    word is computed, and when appropriate, the full word is presented to the memory. Note: on
    instructions that write to the memory, the address and data words may be only half-updated 
    on the first cycle (but writeM is not asserted then.)
    """

    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, _, _, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not_(i)

    split_instr = Split(in_=instruction)

    # A DFF to split each pair of cycles into two halves:
    # top_half is True in the first half-cycle, when the low half-words are being computed.
    # bottom_half is True in the second half-cycles, when the high half-words are in action
    #  and outputs are provided.
    # The DFF stores bottom_half (= !top_half), so that we start in top_half.
    half_cycle = lazy()
    top_half = Not_(half_cycle.out)
    half_cycle.set(DFF(in_=Mux(a=top_half, b=0, sel=reset).out))
    bottom_half = half_cycle.out

    alu = lazy()
    alu_saved = lazy()   # This is needed to be able to write a 16-bit ALU result to the memory, mainly.
    alu_zr_saved = lazy()
    alu_carry_saved = lazy()

    # For convenience, each half-word in a separate 8-bit register:
    load_a = And_(Or_(not_i, da), bottom_half)
    a_lo_reg = Register8(in_=Mux8(a=split_instr.lo, b=alu_saved.out, sel=i).out, 
                         load=load_a)
    a_hi_reg = Register8(in_=Mux8(a=split_instr.hi, b=alu.out, sel=i).out, 
                         load=load_a)
    a_both_reg = Splice(hi=a_hi_reg.out, lo=a_lo_reg.out).out

    load_d = And_(i, dd, bottom_half)
    d_lo_reg = Register8(in_=alu_saved.out, load=load_d)
    d_hi_reg = Register8(in_=alu.out, load=load_d)

    jump_lt = And_(alu.ng, jlt)
    not_alu_both_zr = Nand(a=alu.zr, b=alu_zr_saved.out).out
    jump_eq = And_(Not_(not_alu_both_zr), jeq)
    jump_gt = And_(Not_(alu.ng), not_alu_both_zr, jgt)
    jump = And_(i, Or_(jump_lt, jump_eq, jump_gt))
    # pc = PC8(top_half=top_half, bottom_half=bottom_half, in_=a_both_reg, load=jump, reset=reset)
    # TODO: get the split-cycle PC to do jumps
    pc = PC(in_=a_both_reg, load=And_(bottom_half, jump), reset=reset, inc=bottom_half)

    y_parts = Split(in_=Mux16(a=a_both_reg, b=inM, sel=a).out)
    alu.set(EightALU(x=Mux8(a=d_lo_reg.out, b=d_hi_reg.out, sel=bottom_half).out,
                     y=Mux8(a=y_parts.lo, b=y_parts.hi, sel=bottom_half).out,
                     zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0,
                     carry_in=And_(alu_carry_saved.out, bottom_half)))
    alu_saved.set(Register8(in_=alu.out, load=top_half))  # Note: 8 DFFs would do it, don't need the load logic
    alu_zr_saved.set(DFF(in_=alu.zr))
    alu_carry_saved.set(DFF(in_=alu.carry_out))

    outputs.outM = Splice(hi=alu.out, lo=alu_saved.out).out  # M value output
    outputs.writeM = And_(dm, i, bottom_half)                # Write to M?
    outputs.addressM = a_both_reg                            # Address in data memory (of M) (latched)
    outputs.pc = pc.out                                      # address of next instruction (latched)
    
    # HACK:
    outputs.top_half = top_half
    outputs.bottom_half = bottom_half
    outputs.i = i
    outputs.dm = dm

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
