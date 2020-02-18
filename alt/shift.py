"""An alternative CPU which is backward compatible with the Nand to Tetris design, adding the ability to 
shift the ALU's result to the right by one bit.

This is pretty cheap: about 50 additional gates to check a bit and select the shifted or un-shifted result.

The VM translator rewrites division by a constant power of 2 to a (series of) "shiftr" opcode(s), and substitutes
a more efficient implementation of Math.multiply that uses it.

The result is about 40% few cycles to run the Pong game loop, and essentially no difference in simulation speed, 
since the only change is a single, conditional `>> 1` expression.

"""

import re

from nand import *
from nand.component import Const
from nand.translate import AssemblySource, translate_dir

from nand.solutions.solved_01 import And, Or, Xor, Not, Not16, Mux16
from nand.solutions.solved_02 import Inc16, Zero16, ALU
from nand.solutions.solved_03 import Register
from nand.solutions.solved_05 import MemorySystem, PC
from nand.solutions import solved_06
from nand.solutions import solved_07


def mkShiftR16(inputs, outputs):
    """Sign-extending right shift."""
    
    for i in range(15):
        outputs.out[i] = inputs.in_[i+1]
    outputs.out[15] = inputs.in_[15]
    
ShiftR16 = build(mkShiftR16)


def mkShiftCPU(inputs, outputs):
    """Implements the Hack architecture, plus a single extra bit of ALU control:
    
    If bit 13 is not set, the result from the ALU is shifted one bit to the right before being 
    written to M, A, or D. The sign bit is retained (so, sign extension).
    
    Condition codes (and therefore, JMPs) are not affected by any shifting, so probably don't use them
    together.
    """

    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    i, _, ns, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out

    alu = lazy()
    alu_result = Mux16(a=ShiftR16(in_=alu.out).out, b=alu.out, sel=ns).out

    a_reg = Register(in_=Mux16(a=instruction, b=alu_result, sel=i).out, load=Or(a=not_i, b=da).out)
    d_reg = Register(in_=alu_result, load=And(a=i, b=dd).out)
    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
    pc = PC(in_=a_reg.out, load=jump, inc=1, reset=reset)
    alu.set(ALU(x=d_reg.out, y=Mux16(a=a_reg.out, b=inM, sel=a).out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))

    outputs.outM = alu_result                # M value output
    outputs.writeM = And(a=dm, b=i).out      # Write to M?
    outputs.addressM = a_reg.out             # Address in data memory (of M) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)

ShiftCPU = build(mkShiftCPU)


def mkShiftComputer(inputs, outputs):
    """This is the same as regular Computer, except using ShiftCPU."""
    
    reset = inputs.reset
    
    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(ShiftCPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc

ShiftComputer = build(mkShiftComputer)


def parse_op(string, symbols={}):
    m = re.match(r"(.+)>>1", string)
    if m:
        return 0xdfff & solved_06.parse_op(m.group(1), symbols)
    
    return solved_06.parse_op(string, symbols)


def assemble(lines):
    return solved_06.assemble(lines, parse_op)


# Math.multiply from the included library, rewritten to use shiftr to rotate the bits of y into the 
# low bit, rather than using a table and a separate local variable to tell when to stop.
FAST_MULTIPLY = """
    function Math.multiply 5
    // local 0: acc/result
    // local 1: tmp for swapping x/y
    // local 2: negate result?

    push argument 0
    push constant 0
    lt
    push argument 1
    push constant 0
    gt
    and
    push argument 0
    push constant 0
    gt
    push argument 1
    push constant 0
    lt
    and
    or
    pop local 2  // (x < 0 and y > 0) or (x > 0 and y < 0)

    push argument 0
    call Math.abs 1
    pop argument 0  // x = abs(x)
    push argument 1
    call Math.abs 1
    pop argument 1  // y = abs(y)

    push argument 0
    push argument 1
    lt
    if-goto IF_TRUE0
    goto IF_FALSE0
    label IF_TRUE0  // x < y
    push argument 0
    pop local 1
    push argument 1
    pop argument 0
    push local 1
    pop argument 1  // swap x and y

    label IF_FALSE0  // x > y
    label WHILE_EXP0
    push argument 1
    push constant 0
    eq
    if-goto WHILE_END0   // y == 0  -> exit
    push argument 1
    push constant 1
    and
    if-goto IF_TRUE1  // (y & 0x0001) != 0
    goto IF_FALSE1
    label IF_TRUE1
    push local 0
    push argument 0
    add
    pop local 0  // a = a + x

    label IF_FALSE1
    push argument 0
    push argument 0
    add
    pop argument 0  // x = x + x
    push argument 1
    shiftr
    pop argument 1  // y = y/2
    goto WHILE_EXP0

    label WHILE_END0
    push local 2
    if-goto IF_TRUE2
    goto IF_FALSE2

    label IF_TRUE2
    push local 0
    neg
    pop local 0
    label IF_FALSE2
    push local 0
    return
""".split('\n')

INFINITE_LOOP = """
    // Included for the sake of tests that want to run off the end.
    label SHIFT_VM_HALT
    goto SHIFT_VM_HALT
""".split('\n')


class Translator(solved_07.Translator):
    """Re-use the standard translator, adding a single new opcode: "shiftr".
    """
    
    def __init__(self):
        self.asm = AssemblySource()
        solved_07.Translator.__init__(self, self.asm)

    def shiftr(self):
        self._unary("shiftr", "M>>1")

    def finish(self):
        for line in INFINITE_LOOP + FAST_MULTIPLY:
            t = solved_07.parse_line(line)
            if t:
                op, args = t
                self.__getattribute__(op)(*args)
        
    def rewrite_ops(self, ops):
        result = []
        while ops:
            # TODO: the same for other powers of two
            if len(ops) >= 2 and ops[0] == ('push_constant', (16,)) and ops[1] == ('call', ("Math", "divide", 2)):
                result.append(("shiftr", ()))
                result.append(("shiftr", ()))
                result.append(("shiftr", ()))
                result.append(("shiftr", ()))
                ops = ops[2:]
                # print("rewrote divide by 16")
            # TODO: similar for multiply, but use "pop temp 1"; "push temp 1" "push temp 1" "add"?
            else:
                result.append(ops[0])
                ops = ops[1:]
        return result


import computer

SHIFT_PLATFORM = computer.Platform(
    chip=ShiftComputer,
    assemble=assemble,
    parse_line=solved_07.parse_line,
    translator=Translator)

if __name__ == "__main__":
    computer.main(SHIFT_PLATFORM)
