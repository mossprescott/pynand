"""An alternative CPU which enables _much_ smaller binaries, and therefore much larger programs, by 
making a simple non-recursive call/return cost only one instruction in ROM per occurrence. With that,
a "threaded" interpreter is much more compact (and readable).

A register is added to hold the return address, leaving D and A available for arguments.

CALL [symbol]
- bit pattern: 10xx_xxxx_xxxx_xxxx
- symbol is resolved to a location in ROM, which must be non-zero and fit in 14 bits (the first half of ROM).
- RA <- the address of the next instruction (i.e. PC+1)
- PC <- the resolved address for symbol from instr[0..14]

RTN
- bit pattern: 1000_0000_0000_0000
- PC <- RA

Typical use:
  @10
  CALL VM.push_constant
  @3
  CALL VM.push_local
  CALL VM.add
  CALL VM.pop_local_0  # Probably special-case some common arguments

Interpreter example:
(VM.push_constant)
  // move arg to D
  D=A
  // familiar push_d sequence:
  @SP
  M=M+1
  A=M-1
  M=D
  // return
  RTN

That's 2 instructions in ROM and 8 at runtime for pushing a large constant. Compare to 6 each in the standard VM.
For small values, down to 1 (6 at runtime) from 4.

Other opcodes:
- gotos don't return, so only one instruction in ROM and one added at runtime.
- call needs an address and arg count, so two or three more instructions to setup, total of 4 or 5 (compare to 13.)
"""

import re

from nand import *
from nand.translate import AssemblySource, translate_dir

from nand.solutions.solved_01 import And, Or, Not, Xor, Not16, Mux16
from nand.solutions.solved_02 import Inc16, ALU
from nand.solutions.solved_02 import Zero16  # HACK: should be defined in project_02?
from nand.solutions.solved_03 import Register
from nand.solutions.solved_05 import MemorySystem, PC
from nand.solutions import solved_06
from nand.solutions import solved_07


# Compare two 16-bit values. Another thing that's easy to simulate in codegen, and seems like it 
# _should_ have a reasonably efficient representation in Nands, even if this isn't it.
# Note: this simplifies to Zero16, if one of the inputs is 0, so maybe should just implement this 
# in project_02 instead.
def mkEq16(inputs, outputs):
    a = inputs.a
    b = inputs.b

    outputs.out = And(
        a=And(a=And(a=And(a=Not(in_=Xor(a=a[15], b=b[15]).out).out,
                          b=Not(in_=Xor(a=a[14], b=b[14]).out).out).out,
                    b=And(a=Not(in_=Xor(a=a[13], b=b[13]).out).out,
                          b=Not(in_=Xor(a=a[12], b=b[12]).out).out).out).out,
              b=And(a=And(a=Not(in_=Xor(a=a[11], b=b[11]).out).out,
                          b=Not(in_=Xor(a=a[10], b=b[10]).out).out).out,
                    b=And(a=Not(in_=Xor(a=a[ 9], b=b[ 9]).out).out,
                          b=Not(in_=Xor(a=a[ 8], b=b[ 8]).out).out).out).out).out,
        b=And(a=And(a=And(a=Not(in_=Xor(a=a[ 7], b=b[ 7]).out).out,
                          b=Not(in_=Xor(a=a[ 6], b=b[ 6]).out).out).out,
                    b=And(a=Not(in_=Xor(a=a[ 5], b=b[ 5]).out).out,
                          b=Not(in_=Xor(a=a[ 4], b=b[ 4]).out).out).out).out,
              b=And(a=And(a=Not(in_=Xor(a=a[ 3], b=b[ 3]).out).out,
                          b=Not(in_=Xor(a=a[ 2], b=b[ 2]).out).out).out,
                    b=And(a=Not(in_=Xor(a=a[ 1], b=b[ 1]).out).out,
                          b=Not(in_=Xor(a=a[ 0], b=b[ 0]).out).out).out).out).out).out
Eq16 = build(mkEq16)


def mkMask15(inputs, outputs):
    for i in range(15):
        outputs.out[i] = inputs.in_[i]
    outputs.out[15] = Not(in_=1).out  # HACK: syntax not working for output bit, apparently

Mask15 = build(mkMask15)


def mkThreadedCPU(inputs, outputs):
    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, ncr, _, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out

    call_rtn = And(a=i, b=Not(in_=ncr).out).out
    rtn = Eq16(a=instruction, b=0x8000).out
    call = And(a=call_rtn, b=Not(in_=rtn).out).out
    call_target = Mask15(in_=instruction).out
    
    alu = lazy()
    pc = lazy()
    a_reg = Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=da).out)
    d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    ra_reg = Register(in_=pc.nxt, load=call)

    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
              
    next_pc = Mux16(
                a=Mux16(
                    a=a_reg.out, 
                    b=ra_reg.out,
                    sel=rtn).out,
                b=call_target, 
                sel=call).out
    
    pc.set(PC(in_=next_pc, load=Or(a=jump, b=call_rtn).out, inc=1, reset=reset))
    alu.set(ALU(x=d_reg.out, y=Mux16(a=a_reg.out, b=inM, sel=a).out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))


    outputs.outM = alu.out                   # M value output
    outputs.writeM = And(a=dm, b=And(a=i, b=ncr).out).out      # Write to M?
    outputs.addressM = a_reg.out             # Address in data memory (of M) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)

    # HACK
    outputs.ra = ra_reg.out
    outputs.rtn = rtn
    outputs.call = call

ThreadedCPU = build(mkThreadedCPU)


def mkThreadedComputer(inputs, outputs):
    reset = inputs.reset
    
    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(ThreadedCPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc

ThreadedComputer = build(mkThreadedComputer)


def parse_op(string, symbols={}):
    m = re.match(r"CALL ([^ ]+)", string)
    if m:
        return 0b1000_0000_0000_0000 | symbols[m.group(1)]

    if string == "RTN":
        return 0b1000_0000_0000_0000

    return solved_06.parse_op(string, symbols)


def assemble(lines):
    return solved_06.assemble(lines, parse_op)




class Translator:
    """Can't really re-use anything from the standard translator. 
    """
    
    def __init__(self):
        self.asm = AssemblySource()

        # Parameters controlling how many specialized opcode variants are emitted.
        # May be manually tweaked. A smart translator would inspect the source and choose them 
        # to optimize for size/speed.
        self.SPECIALIZED_MAX_PUSH_CONSTANT = 3
        self.SPECIALIZED_MAX_CALL_NUM_ARGS = 2

        start = self.asm.next_label("start")
        self.asm.instr(f"@{start}")
        self.asm.instr("0;JMP")
        
        # "Microcoded" instructions, which for this translator basically includes _all_ opcodes,
        # plus many special-cases:
        # If there's a single argument, it's passed in A. If more than one, additional args are 
        # passed in R13-R15. See each implementation for specifics.
        self._library()
        
        # Early check that the library of opcodes fits in the first half of the ROM, as required.
        # Practically speaking, probably want it to be _much_ smaller than that.
        assert self.asm.instruction_count <= 2**14
        
        self.asm.label(start)

    def preamble(self):
        self.asm.start("VM initialization")
        self.asm.instr("@256")
        self.asm.instr("D=A")
        self.asm.instr("@SP")
        self.asm.instr("M=D")

        self.call("Sys", "init", 0)
    
    def push_constant(self, value):
        """Value to push in A if not specialized.
        """

        assert 0 <= value < 2**15
        
        self.asm.start(f"push constant {value}")
        
        if value <= self.SPECIALIZED_MAX_PUSH_CONSTANT:
            self.asm.instr(f"CALL VM.push_constant_{value}")
        else:
            self.asm.instr(f"@{value}")
            self.asm.instr(f"CALL VM.push_constant")

    def add(self):
        self.asm.start(f"add")
        self.asm.instr(f"CALL VM.add")
    
    def call(self, class_name, function_name, num_args):
        """Callee address in A. num_args in R13 if not specialized.
        """

        self.asm.start(f"call {class_name}.{function_name} {num_args}")

        if num_args <= self.SPECIALIZED_MAX_CALL_NUM_ARGS:
            self.asm.instr(f"@{class_name}.{function_name}")
            self.asm.instr(f"CALL VM.call_{num_args}")
        else:
            self.asm.instr(f"@{num_args}")
            self.asm.instr(f"D=A")
            self.asm.instr(f"@R13")
            self.asm.instr(f"M=D")
        
            self.asm.instr(f"@{class_name}.{function_name}")
            self.asm.instr(f"CALL VM.call")

    def _library(self):

        # push from D and return:
        self.asm.label(f"VM._push_d")
        self.asm.instr("@SP")
        self.asm.instr("M=M+1")
        self.asm.instr("A=M-1")
        self.asm.instr("M=D")
        self.asm.instr("RTN")

        
        # push constant
        for value in (0, 1):
            self.asm.label(f"VM.push_constant_{value}")
            self.asm.instr(f"D={value}")
            self.asm.instr("@VM._push_d")
            self.asm.instr(f"0;JMP")
        
        for value in range(2, self.SPECIALIZED_MAX_PUSH_CONSTANT+1):
            self.asm.label(f"VM.push_constant_{value}")
            self.asm.instr(f"@{value}")
            self.asm.instr("D=A")
            self.asm.instr("@VM._push_d")
            self.asm.instr(f"0;JMP")

        self.asm.label("VM.push_constant")
        self.asm.instr("D=A")
        self.asm.instr("@VM._push_d")
        self.asm.instr("0;JMP")


        
        # add
        
        self.asm.label("VM.add")
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")  # update SP
        self.asm.instr("D=M")     # D = top
        self.asm.instr("A=A-1")   # Don't update SP again
        self.asm.instr("M=D+M")
        self.asm.instr("RTN")

        
        # call
        
        for num_args in range(self.SPECIALIZED_MAX_CALL_NUM_ARGS+1):
            self.asm.label(f"VM.call_{num_args}")
            self.asm.instr(f"D=A")
            self.asm.instr(f"@R14")
            self.asm.instr(f"M=D")
            self.asm.instr(f"@{num_args}")
            self.asm.instr(f"D=A")
            self.asm.instr(f"@R13")
            self.asm.instr(f"M=D")
            self.asm.instr(f"@VM.call_common")
            self.asm.instr(f"0;JMP")

        self.asm.label(f"VM.call")
        # R14 = callee address
        self.asm.instr(f"D=A")
        self.asm.instr(f"@R14")
        self.asm.instr(f"M=D")
        # fall through to the common impl:

        self.asm.label(f"VM.call_common")
        # TODO...
        self.asm.instr(f"@R14")
        self.asm.instr(f"A=M")
        self.asm.instr(f"0;JMP")


if __name__ == "__main__":
    TRACE = False

    import sys
    import computer

    translate = Translator()
    
    translate.preamble()
    
    translate_dir(translate, solved_07.parse_line, sys.argv[1])
    translate_dir(translate, solved_07.parse_line, "nand2tetris/tools/OS")  # HACK not committed
    
    # if TRACE:
    if True:
        for instr in translate.asm:
            print(instr)

    computer.run(assemble(translate.asm), chip=ThreadedComputer, src_map=translate.asm.src_map if TRACE else None)
