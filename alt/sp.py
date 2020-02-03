import re

from nand import *
from nand.translate import AssemblySource

from nand.solutions.solved_01 import And, Or, Not, Not16, Mux16
from nand.solutions.solved_02 import Inc16, ALU
from nand.solutions.solved_02 import Zero16  # HACK: should be defined in project_02?
from nand.solutions.solved_03 import Register
from nand.solutions.solved_05 import MemorySystem, PC
from nand.solutions import solved_06
from nand.solutions import solved_07

def mkDec16(inputs, outputs):
    """Decrement for 16-bit values, by inverting and incrementing.
    """
    outputs.out = Not16(in_=Inc16(in_=Not16(in_=inputs.in_).out).out).out
    
Dec16 = build(mkDec16)


def mkSPCPU(inputs, outputs):
    """Implements the Hack architecture, plus two extra instructions:

    Pop to register:
      [AD]=--SP
      0b100_1_110000_AD0_000
      Bits A and/or D give the destination(s). Note: cannot pop to M, since the single-ported RAM 
      is busy reading the popped value. Also: for now, the ALU control bits must be set to the "M"
      pattern, to load the value from memory; any other pattern may or may not do anything useful.
    
    Push from ALU:
      SP++=<expr>
      bit pattern 0b100_0_XXXXXX_000_000
      Note: cannot refer to M, since the single-ported RAM is busy writing the pushed value.
    
    It is assumed that bits 13 and 14 of the instruction are always set for all other non-@ instructions.

    Note: the bit pattern corresponding to SP++=<expr>;<jmp> should be considered unsupported (and isn't 
    currently generated by parse_op).
    
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

    is_sp = And(a=i, b=And(a=Not(in_=x1).out, b=Not(in_=x0).out).out).out
    push_bits = And(a=Not(in_=da).out, b=Not(in_=dd).out).out
    is_push = And(a=is_sp, b=push_bits).out
    is_pop = And(a=is_sp, b=Not(in_=push_bits).out).out

    is_write = And(a=dm, b=i).out  # The instruction writes to M

    a_reg = lazy()
    sp_reg = lazy()
    next_sp = Inc16(in_=sp_reg.out).out
    prev_sp = Dec16(in_=sp_reg.out).out  # TODO: would it be more efficient to re-use the same Inc16, by switching the input/output?
    
    a_zero = Zero16(in_=a_reg.out).out  # Meaning that M refers to SP
    
    is_sp_write = And(a=is_write, b=a_zero).out

    alu = lazy()
    
    a_reg.set(Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=da).out))
    d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    sp_reg.set(Register(in_=Mux16(
                            a=alu.out,
                            b=Mux16(a=prev_sp, b=next_sp, sel=is_push).out,
                            sel=is_sp).out, 
                        load=Or(a=is_sp, b=is_sp_write).out))
    
    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
    pc = PC(in_=a_reg.out, load=jump, inc=1, reset=reset)
    
    # The Y input to the ALU:
    # is SP if expr refers to M and A is 0,
    # is from the RAM if the expr is --SP or refers to M,
    # otherwise it is A.
    alu_y = Mux16(
        a=Mux16(
            a=a_reg.out, 
            b=Mux16(
                a=inM, 
                b=sp_reg.out, 
                sel=a_zero).out, 
            sel=a).out,
        b=inM,
        sel=is_pop).out
    alu.set(ALU(x=d_reg.out, y=alu_y, zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))

    # HACK: for debugging
    outputs.is_sp = is_sp
    outputs.is_sp_write = is_sp_write

    # output value to memory (to M or top of stack)
    outputs.outM = alu.out
    
    # write to memory?
    outputs.writeM = Or(a=And(a=is_write, b=Not(in_=a_zero).out).out, b=is_push).out
    
    # Address in data memory (of M or top of stack) (latched)
    outputs.addressM = Mux16(a=Mux16(a=a_reg.out, b=prev_sp, sel=is_pop).out, b=sp_reg.out, sel=is_push).out
    
    # address of next instruction (latched)
    outputs.pc = pc.out

    # expose SP for debugging purposes (since it's no longer found in the RAM)
    outputs.sp = sp_reg.out

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


def parse_op(string):
    m = re.match(r"([ADM]+)=--SP", string)
    if m:
        dest_a = 'A' in m.group(1)
        dest_d = 'D' in m.group(1)
        if 'M' in m.group(1):
            raise SyntaxError(f"M not allowed as a destination for pop: {string}")
        return (1 << 15) | (0b1_110000 << 6) | (dest_a << 5) | (dest_d << 4)
    
    m = re.match(r"SP\+\+=([^;]+)", string)
    if m:
        alu = solved_06.ALU_CONTROL.get(m.group(1))
        if alu is not None:
            return (1 << 15) | (alu << 6)
    
    return solved_06.parse_op(string)


def assemble(lines):
    return solved_06.assemble(lines, parse_op)


class Translator(solved_07.Translator):
    def __init__(self):
        self.asm = AssemblySource()
        solved_07.Translator.__init__(self, self.asm)

    def push_constant(self, value):
        self.asm.start(f"push constant {value}")
        if value <= 1:
            self.asm.instr(f"SP++={value}")
        else:
            self.asm.instr(f"@{value}")
            self.asm.instr(f"SP++=A")

    def _pop_segment(self, segment_ptr, index):
        # Since pop doesn't overwrite A, a much simpler sequence works:
        if index == 0:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M")
        elif index == 1:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M+1")
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr("D=A")
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=D+M")
        self.asm.instr("D=--SP")
        self.asm.instr("M=D")

    def _push_d(self):
        # TODO: no need for this as soon as everything's switched to use SP++ directly
        self.asm.instr("SP++=D")

    def _pop_d(self):
        # TODO: no need for this as soon as everything's switched to use SP++ directly?
        self.asm.instr("D=--SP")

    def _binary(self, op):
        self.asm.instr("D=--SP")
        self.asm.instr("A=--SP")
        self.asm.instr(f"SP++={op.replace('M', 'A')}")

    def _unary(self, op):
        self.asm.instr("D=--SP")
        self.asm.instr(f"SP++={op.replace('M', 'D')}")

