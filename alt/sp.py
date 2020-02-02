from nand import *

from project_01 import And, Or, Not, Not16, Mux16
from project_02 import Inc16, ALU
from nand.solutions.solved_02 import Zero16  # HACK: should be defined in project_02?
from project_03 import Register
from project_05 import MemorySystem, PC


def mkDec16(inputs, outputs):
    """Decrement for 16-bit values, by inverting and incrementing.
    """
    outputs.out = Not16(in_=Inc16(in_=Not16(in_=inputs.in_).out).out).out
    
Dec16 = build(mkDec16)


def mkSPCPU(inputs, outputs):
    """Implements the Hack architecture, plus two extra instructions:

    Pop to register:
      [AD]=--SP
      0b100_0_000000_AD0_000
      Bits A and/or D give the destination(s). Note: cannot pop to M, since the single-ported RAM 
      is busy reading the popped value.
    
    Push from ALU:
      SP++=[expr]
      bit pattern 0b100_0_xxxxxx_000_000
      Note: cannot refer to M, since the single-ported RAM is busy writing the pushed value.
    
    It is assumed that bits 13 and 14 of the instruction are always set for all other non-@ instructions.
    
    Location 0 in the RAM is never written or read; SP is stored in a register. Ordinary reads and 
    writes to location 0 are intercepted for backward compatibility with Hack programs (as long as they 
    set bits 13 and 14 as expected).
    """
    
    inM = inputs.inM                 # Value from the memory (M or top of stack)
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, x1, x0, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out

    is_sp = And(a=Not(in_=x1).out, b=Not(in_=x0).out).out
    is_push = And(a=Not(in_=da).out, b=Not(in_=dd).out).out

    sp_reg = lazy()
    next_sp = Inc16(in_=sp_reg.out).out
    prev_sp = Dec16(in_=sp_reg.out).out  # TODO: would it be more efficient to re-use the same Inc16, by switching the input/output?
    
    alu = lazy()
    
    a_reg = Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=da).out)
    d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    sp_reg.set(Register(in_=Mux16(a=prev_sp, b=next_sp, sel=is_push).out, load=is_sp))
    
    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
    pc = PC(in_=a_reg.out, load=jump, inc=1, reset=reset)
    alu.set(ALU(x=d_reg.out, y=Mux16(a=a_reg.out, b=inM, sel=a).out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))


    outputs.outM = alu.out                   # output value to memory (to M or top of stack)
    outputs.writeM = And(a=dm, b=i).out      # write to memory?
    outputs.addressM = a_reg.out             # Address in data memory (of M or top of stack) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)

    outputs.sp = sp_reg.out                  # expose SP for debugging purposes (since it's no longer found in the RAM)

SPCPU = build(mkSPCPU)


def mkSPComputer(inputs, outputs):
    reset = inputs.reset
    
    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(SPCPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc
    outputs.sp = cpu.sp

SPComputer = build(mkSPComputer)
