#! /usr/bin/env python3

"""An alternative CPU which enables _much_ smaller binaries, and therefore much larger programs, by 
making a simple non-recursive call/return cost only one instruction in ROM per occurrence. With that,
a "threaded" interpreter is much more compact (and readable).

Essentially the binary consists of two parts: a fixed "library" of opcode handlers written using the 
usual Hack machine instructions, and the actual program which is now just a sequence of CALLs into 
the opcode handlers. Most of these calls are just a single instruction, so the overall size of the 
binary is roughly the number of opcodes in the VM source, plus the fixed library (roughly 1k).

A register is added to hold the return address, leaving D and A available for arguments, although 
practically speaking the handler always needs to clobber one register or the other.

The result is dramatically smaller executables, which run slower:
- gates: about 1,550 (+23% from 1,262), but could probably be improved
- instruction count for Pong: 8.7k (-70% from 29.5k)
- cycles in Sys.init: 5.1m (+28% from 3.97m)

That means some very large demos can now run. These are programs whose authors probably only ever ran them on the 
VM-level simulator.
"""

import re

from nand import *
from nand.translate import AssemblySource, translate_dir

from nand.solutions.solved_01 import And, Or, Not, Xor, Not16, Mux16
from nand.solutions.solved_02 import Inc16, Zero16, ALU
from nand.solutions.solved_03 import Register
from nand.solutions.solved_05 import MemorySystem, PC
from nand.solutions import solved_06
from nand.solutions import solved_07


# Compare two 16-bit values. Another thing that's easy to simulate in codegen, and seems like it 
# _should_ have a reasonably efficient representation in Nands, even if this isn't it (e.g. a couple 
# of many-input Nands.)
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
    """Backwards-compatible with the Hack CPU, with two additional instructions and a new register
    storing a return address written by CALL and read by RTN.
    
    CALL [symbol]
    - bit pattern: 10xx_xxxx_xxxx_xxxx
    - symbol is resolved to a location in ROM, which must be non-zero and fit in 14 bits (the first 
        half of ROM). Note: the translator actually only needs about 1,000 words for the library, so 
        10 or 11 bits would actually be sufficient.)
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
    """
    
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
    a_reg = Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=And(a=da, b=Not(in_=call_rtn).out).out).out)
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
        # Parameters controlling how many specialized opcode variants are emitted.
        # More specialization means a larger library, but smaller object code and 
        # fewer cycles, generally.
        # May be manually tweaked. A smart translator would inspect the source and choose them 
        # to optimize for size/speed.
        self.SPECIALIZED_MAX_PUSH_CONSTANT = 6  # TODO: 12?
        self.SPECIALIZED_MAX_POP_SEGMENT = 6  # TODO: 10?
        self.SPECIALIZED_MAX_PUSH_SEGMENT = 6
        self.SPECIALIZED_MAX_FUNCTION_NUM_LOCALS = 10  # TODO: ?
        self.SPECIALIZED_MAX_CALL_NUM_ARGS = 4  # TODO: ?

        self.asm = AssemblySource()

        self.class_namespace = "_"
        self.function_namespace = "_"

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

    def sub(self):
        self.asm.start(f"sub")
        self.asm.instr(f"CALL VM.sub")

    def neg(self):
        self.asm.start(f"neg")
        self.asm.instr(f"CALL VM.neg")

    def and_op(self):
        self.asm.start(f"and")
        self.asm.instr(f"CALL VM.and")

    def or_op(self):
        self.asm.start(f"or")
        self.asm.instr(f"CALL VM.or")

    def not_op(self):
        self.asm.start(f"not")
        self.asm.instr(f"CALL VM.not")

    def eq(self):
        self.asm.start(f"eq")
        self.asm.instr(f"CALL VM.eq")

    def lt(self):
        self.asm.start(f"lt")
        self.asm.instr(f"CALL VM.lt")

    def gt(self):
        self.asm.start(f"gt")
        self.asm.instr(f"CALL VM.gt")

    def pop_local(self, index):
        self.asm.start(f"pop local {index}")
        if index <= self.SPECIALIZED_MAX_POP_SEGMENT:
            self.asm.instr(f"CALL VM.pop_local_{index}")
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.pop_local")

    def pop_argument(self, index):
        self.asm.start(f"pop argument {index}")
        if index <= self.SPECIALIZED_MAX_POP_SEGMENT:
            self.asm.instr(f"CALL VM.pop_argument_{index}")
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.pop_argument")

    def pop_this(self, index):
        self.asm.start(f"pop this {index}")
        if index <= self.SPECIALIZED_MAX_POP_SEGMENT:
            self.asm.instr(f"CALL VM.pop_this_{index}")
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.pop_this")

    def pop_that(self, index):
        self.asm.start(f"pop that {index}")
        if index <= self.SPECIALIZED_MAX_POP_SEGMENT:
            self.asm.instr(f"CALL VM.pop_that_{index}")
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.pop_that")
        
    def pop_temp(self, index):
        self.asm.start(f"pop temp {index}")
        self.asm.instr(f"CALL VM.pop_temp_{index}")

    def pop_pointer(self, index):
        assert 0 <= index <= 1
        self.asm.start(f"pop pointer {index}")
        self.asm.instr(f"CALL VM.pop_pointer_{index}")

    def push_local(self, index):
        self.asm.start(f"push local {index}")
        if index <= self.SPECIALIZED_MAX_PUSH_SEGMENT:
            self.asm.instr(f"CALL VM.push_local_{index}")            
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.push_local")

    def push_argument(self, index):
        self.asm.start(f"push argument {index}")
        if index <= self.SPECIALIZED_MAX_PUSH_SEGMENT:
            self.asm.instr(f"CALL VM.push_argument_{index}")            
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.push_argument")

    def push_this(self, index):
        self.asm.start(f"push this {index}")
        if index <= self.SPECIALIZED_MAX_PUSH_SEGMENT:
            self.asm.instr(f"CALL VM.push_this_{index}")            
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.push_this")

    def push_that(self, index):
        self.asm.start(f"push that {index}")
        if index <= self.SPECIALIZED_MAX_PUSH_SEGMENT:
            self.asm.instr(f"CALL VM.push_that_{index}")            
        else:
            self.asm.instr(f"@{index}")
            self.asm.instr(f"CALL VM.push_that")

    def push_temp(self, index):
        assert 0 <= index < 8
        self.asm.start(f"push temp {index}")
        self.asm.instr(f"CALL VM.push_temp_{index}")
        
    def push_pointer(self, index):
        assert 0 <= index <= 1
        self.asm.start(f"push pointer {index}")
        self.asm.instr(f"CALL VM.push_pointer_{index}")

    def pop_static(self, index):
        self.asm.start(f"push static {index}")
        self.asm.instr(f"@{self.class_namespace}.static{index}")
        self.asm.instr(f"CALL VM.pop_static")
        
    def push_static(self, index):
        self.asm.start(f"pop static {index}")
        self.asm.instr(f"@{self.class_namespace}.static{index}")
        self.asm.instr(f"CALL VM.push_static")

    def label(self, name):
        self.asm.start(f"label {name}")
        self.asm.label(f"{self.function_namespace}${name}")
    
    def if_goto(self, name):
        self.asm.start(f"if-goto {name}")
        self.asm.instr(f"@{self.function_namespace}${name}")
        self.asm.instr(f"CALL VM.if_goto")

    def goto(self, name):
        self.asm.start(f"goto {name}")
        self.asm.instr(f"@{self.function_namespace}${name}")
        self.asm.instr("0;JMP")

    def function(self, class_name, function_name, num_vars):
        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{function_name}"

        self.asm.start(f"function {class_name}.{function_name} {num_vars}")
        self.asm.label(f"{self.function_namespace}")
        if num_vars <= self.SPECIALIZED_MAX_FUNCTION_NUM_LOCALS:
            self.asm.instr(f"CALL VM.function_{num_vars}")
        else:
            self.asm.instr(f"@{num_vars}")
            self.asm.instr(f"CALL VM.function")

    def return_op(self):
        # Note: not actually going to RTN from this, but using CALL still saves a word.
        self.asm.start("return")
        self.asm.instr("CALL VM.return")

    def call(self, class_name, function_name, num_args):
        """Callee address in A. num_args in R13 if not specialized.
        """

        return_label = self.asm.next_label("RET_ADDRESS_CALL")

        self.asm.start(f"call {class_name}.{function_name} {num_args}")

        self.asm.instr(f"@{return_label}")
        self.asm.instr("CALL VM._push_a")

        if num_args <= self.SPECIALIZED_MAX_CALL_NUM_ARGS:
            self.asm.instr(f"@{class_name.lower()}.{function_name}")
            self.asm.instr(f"CALL VM.call_{num_args}")
        else:
            self.asm.instr(f"@{num_args}")
            self.asm.instr(f"D=A")
            self.asm.instr(f"@R13")
            self.asm.instr(f"M=D")
        
            self.asm.instr(f"@{class_name.lower()}.{function_name}")
            self.asm.instr(f"CALL VM.call")

        self.asm.label(return_label)

    def rewrite_ops(self, ops):
        return ops

    def _library(self):

        # Push from D:
        def push_d():
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("A=M-1")
            self.asm.instr("M=D")

        # pop to D; has to be generated inline each time because it's never a tail call:
        def pop_d():
            self.asm.instr("@SP")
            self.asm.instr("AM=M-1")
            self.asm.instr("D=M")
        
        # push constant
        for value in (0, 1):
            self.asm.label(f"VM.push_constant_{value}")
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("A=M-1")
            self.asm.instr(f"M={value}")
            self.asm.instr("RTN")
        
        for value in range(2, self.SPECIALIZED_MAX_PUSH_CONSTANT+1):
            self.asm.label(f"VM.push_constant_{value}")
            self.asm.instr(f"@{value}")
            self.asm.instr("D=A")
            push_d()
            self.asm.instr("RTN")

        self.asm.label("VM.push_constant")
        self.asm.instr("D=A")
        push_d()
        self.asm.instr("RTN")


        # Push from one of the memory segments:
        def push_segment(segment_ptr, index):
            if index == 0:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M")
                self.asm.instr("D=M")
                push_d()
                self.asm.instr("RTN")
            elif index == 1:
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=M+1")
                self.asm.instr("D=M")
                push_d()
                self.asm.instr("RTN")
            else:
                self.asm.instr(f"@{index}")
                self.asm.instr("D=A")
                self.asm.instr(f"@{segment_ptr}")
                self.asm.instr("A=D+M")
                self.asm.instr("D=M")
                push_d()
                self.asm.instr("RTN")

        def push_segment_a(segment_ptr):
            self.asm.instr("D=A")
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=D+M")
            self.asm.instr("D=M")
            push_d()
            self.asm.instr("RTN")
        
        for index in range(self.SPECIALIZED_MAX_PUSH_SEGMENT+1):
            self.asm.label(f"VM.push_local_{index}")
            push_segment("LCL", index)
            self.asm.label(f"VM.push_argument_{index}")
            push_segment("ARG", index)
            self.asm.label(f"VM.push_this_{index}")
            push_segment("THIS", index)
            self.asm.label(f"VM.push_that_{index}")
            push_segment("THAT", index)

        self.asm.label("VM.push_local")
        push_segment_a("LCL")
        self.asm.label("VM.push_argument")
        push_segment_a("ARG")
        self.asm.label("VM.push_this")
        push_segment_a("THIS")
        self.asm.label("VM.push_that")
        push_segment_a("THAT")

            
        # Pop to one of the memory segments:
        def pop_segment(segment_ptr, index):
            # TODO: specialize 0 and 1 to save two instr.
            self.asm.instr(f"@{index}")
            pop_segment_a(segment_ptr)
        
        def pop_segment_a(segment_ptr):
            # R15 = ptr + index
            self.asm.instr("D=A")
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("D=D+M")
            self.asm.instr("@R15")
            self.asm.instr("M=D")
            # D = RAM[SP--]
            pop_d()
            # RAM[R15] = D
            self.asm.instr("@R15")
            self.asm.instr("A=M")
            self.asm.instr("M=D")
            self.asm.instr("RTN")

        for index in range(self.SPECIALIZED_MAX_POP_SEGMENT+1):
            self.asm.label(f"VM.pop_local_{index}")
            pop_segment("LCL", index)
            self.asm.label(f"VM.pop_argument_{index}")
            pop_segment("ARG", index)
            self.asm.label(f"VM.pop_this_{index}")
            pop_segment("THIS", index)
            self.asm.label(f"VM.pop_that_{index}")
            pop_segment("THAT", index)

        self.asm.label("VM.pop_local")
        pop_segment_a("LCL")
        self.asm.label("VM.pop_argument")
        pop_segment_a("ARG")
        self.asm.label("VM.pop_this")
        pop_segment_a("THIS")
        self.asm.label("VM.pop_that")
        pop_segment_a("THAT")


        # Push/pop temp:

        for index in range(8):
            self.asm.label(f"VM.push_temp_{index}")
            self.asm.instr(f"@R{5+index}")
            self.asm.instr("D=M")
            push_d()
            self.asm.instr("RTN")

        for index in range(8):
            self.asm.label(f"VM.pop_temp_{index}")
            pop_d()
            self.asm.instr(f"@R{5+index}")
            self.asm.instr("M=D")
            self.asm.instr("RTN")


        # Push/pop pointer:

        self.asm.label("VM.push_pointer_0")
        self.asm.instr("@THIS")
        self.asm.instr("D=M")
        push_d()
        self.asm.instr("RTN")

        self.asm.label("VM.push_pointer_1")
        self.asm.instr("@THAT")
        self.asm.instr("D=M")
        push_d()
        self.asm.instr("RTN")

        self.asm.label("VM.pop_pointer_0")
        pop_d()
        self.asm.instr("@THIS")
        self.asm.instr("M=D")
        self.asm.instr("RTN")

        self.asm.label("VM.pop_pointer_1")
        pop_d()
        self.asm.instr("@THAT")
        self.asm.instr("M=D")
        self.asm.instr("RTN")


        # Push/pop static:
        
        self.asm.label("VM.push_static")
        self.asm.instr("D=M")
        push_d()
        self.asm.instr("RTN")
        
        self.asm.label("VM.pop_static")
        self.asm.instr("D=A")
        self.asm.instr("@R15")  # R15 = target address
        self.asm.instr("M=D")
        pop_d()
        self.asm.instr("@R15")
        self.asm.instr("A=M")
        self.asm.instr("M=D")
        self.asm.instr("RTN")


        # Binary ops:

        def binary(op):
            self.asm.instr("@SP")
            self.asm.instr("AM=M-1")  # update SP
            self.asm.instr("D=M")     # D = top
            self.asm.instr("A=A-1")   # Don't update SP again
            self.asm.instr(f"M={op}")
            self.asm.instr("RTN")

        self.asm.label("VM.add")
        binary("D+M")
        self.asm.label("VM.sub")
        binary("M-D")
        self.asm.label("VM.and")
        binary("D&M")
        self.asm.label("VM.or")
        binary("D|M")


        # Unary ops:

        def unary(op):
            self.asm.instr("@SP")
            self.asm.instr("A=M-1")
            self.asm.instr(f"M={op}")
            self.asm.instr("RTN")

        self.asm.label("VM.neg")
        unary("-M")
        self.asm.label("VM.not")
        unary("!M")


        # comparisons:
        
        def compare(op):
            label = self.asm.next_label(f"VM._{op.lower()}")
            end_label = self.asm.next_label(f"VM._{op.lower()}$end")
        
            # D = top, M = second from top, SP -= 1 (not 2!)
            self.asm.instr("@SP")
            self.asm.instr("AM=M-1")
            self.asm.instr("D=M")
            self.asm.instr("A=A-1")

            # Compare
            self.asm.instr("D=M-D")
        
            # Set result True, optimistically (since A is already loaded with the destination)
            self.asm.instr("M=-1")
        
            self.asm.instr(f"@{end_label}")
            self.asm.instr(f"D;J{op}")
        
            # Set result False
            self.asm.instr("@SP")
            self.asm.instr("A=M-1")
            self.asm.instr("M=0")

            self.asm.label(end_label)
            self.asm.instr("RTN")
        
        self.asm.label(f"VM.eq")
        compare("EQ")
        self.asm.label(f"VM.lt")
        compare("LT")
        self.asm.label(f"VM.gt")
        compare("GT")
        
        
        # if-goto:
        not_taken_label = "VM.if_goto$not_taken"
        self.asm.label("VM.if_goto")
        self.asm.instr("D=A")
        self.asm.instr("@R15")  # R15 = target address
        self.asm.instr("M=D")
        pop_d()
        self.asm.instr(f"@{not_taken_label}")
        self.asm.instr("D;JEQ")
        
        self.asm.instr("@R15")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")
        
        self.asm.label(not_taken_label)
        self.asm.instr("RTN")


        # function:

        for num_vars in range(self.SPECIALIZED_MAX_FUNCTION_NUM_LOCALS+1):
            self.asm.label(f"VM.function_{num_vars}")
            self.asm.instr("@SP")
            self.asm.instr("A=M")
            for _ in range(num_vars):
                self.asm.instr("M=0")
                self.asm.instr("A=A+1")
            self.asm.instr("D=A")
            self.asm.instr("@SP")
            self.asm.instr("M=D")
            self.asm.instr("RTN")

        test_label = "VM.function$test"
        loop_label = "VM.function$loop"
        self.asm.label("VM.function")
        self.asm.instr("D=A")
        self.asm.instr(f"@{test_label}")
        self.asm.instr("0;JMP")
        
        self.asm.label(loop_label)
        self.asm.instr("@SP")
        self.asm.instr("M=M+1")
        self.asm.instr("A=M-1")  # TODO: save a few instr. by updating RAM[SP] after
        self.asm.instr("M=0")
        self.asm.instr("D=D-1")
        self.asm.label(test_label)
        self.asm.instr(f"@{loop_label}")
        self.asm.instr("D;JGT")

        self.asm.instr("RTN")


        # return:
        
        self.asm.label("VM.return")
        
        # R13 = result
        pop_d()
        self.asm.instr("@R13")
        self.asm.instr("M=D")
        
        # SP = LCL
        self.asm.instr("@LCL")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("M=D")
        # R15 = ARG
        self.asm.instr("@ARG")
        self.asm.instr("D=M")
        self.asm.instr("@R15")
        self.asm.instr("M=D")
        # restore segment pointers from stack:
        pop_d()
        self.asm.instr("@THAT")
        self.asm.instr("M=D")
        pop_d()
        self.asm.instr("@THIS")
        self.asm.instr("M=D")
        pop_d()
        self.asm.instr("@ARG")
        self.asm.instr("M=D")
        pop_d()
        self.asm.instr("@LCL")
        self.asm.instr("M=D")
        # R14 = return address
        pop_d()
        self.asm.instr("@R14")
        self.asm.instr("M=D")
        # SP = R15
        self.asm.instr("@R15")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("M=D")
        # Push R13 (result)
        self.asm.instr("@R13")
        self.asm.instr("D=M")
        push_d()
        # jmp to R14
        self.asm.instr("@R14")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")


        # call:

        for num_args in range(self.SPECIALIZED_MAX_CALL_NUM_ARGS+1):
            self.asm.label(f"VM.call_{num_args}")
            self.asm.instr(f"D=A")
            self.asm.instr(f"@R14")
            self.asm.instr(f"M=D")

            if num_args <= 1:
                self.asm.instr(f"@R13")
                self.asm.instr(f"M={num_args}")
            else:
                self.asm.instr(f"@{num_args}")
                self.asm.instr(f"D=A")
                self.asm.instr(f"@R13")
                self.asm.instr(f"M=D")

            self.asm.instr(f"@VM._call_common")
            self.asm.instr(f"0;JMP")

        self.asm.label(f"VM.call")
        # R14 = callee address
        self.asm.instr(f"D=A")
        self.asm.instr(f"@R14")
        self.asm.instr(f"M=D")
        # fall through to the common impl...


        self.asm.label(f"VM._call_common")

        # R15 = SP - (R13 + 1) (which will be the new ARG)
        self.asm.instr("@R13")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("D=M-D")
        self.asm.instr("D=D-1")
        self.asm.instr("@R15")
        self.asm.instr("M=D")

        # push four segment pointers:
        self.asm.instr("@LCL")
        self.asm.instr("D=M")
        push_d()
        self.asm.instr("@ARG")
        self.asm.instr("D=M")
        push_d()
        self.asm.instr("@THIS")
        self.asm.instr("D=M")
        push_d()
        self.asm.instr("@THAT")
        self.asm.instr("D=M")
        push_d()

        # LCL = SP
        # Note: setting LCL here (as opposed to in "function") feels wrong, but it makes the 
        # state of the segment pointers consistent after each opcode, so it's easier to debug.
        self.asm.instr("@SP")
        self.asm.instr("D=M")
        self.asm.instr("@LCL")
        self.asm.instr("M=D")

        # ARG = R15
        self.asm.instr("@R15")
        self.asm.instr("D=M")
        self.asm.instr("@ARG")
        self.asm.instr("M=D")

        # JMP to R14 (the callee)
        self.asm.instr("@R14")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")


        # Used to push the return address in call ops:
        
        self.asm.label("VM._push_a")
        self.asm.instr("D=A")
        self.asm.instr("@SP")
        self.asm.instr("M=M+1")
        self.asm.instr("A=M-1")
        self.asm.instr("M=D")
        self.asm.instr("RTN")


    def finish(self):
        pass


import computer

THREADED_PLATFORM = computer.Platform(
    chip=ThreadedComputer,
    assemble=assemble,
    parse_line=solved_07.parse_line,
    translator=Translator)

if __name__ == "__main__":
    computer.main(THREADED_PLATFORM)
