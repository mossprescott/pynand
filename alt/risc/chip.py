"""Sequential implementation of the RiSC-16 CPU, with the HACK memory system.

"""

from nand import *
from nand.component import Const
from nand.solutions.solved_01 import And, DMux8Way, Mux, Mux8Way16, Mux16, Not, Or, Xor
from nand.solutions.solved_02 import Add16, HalfAdder, FullAdder
from nand.solutions.solved_03 import Register
from nand.solutions.solved_05 import MemorySystem, PC


@chip
def Mux3(inputs, outputs):
    not_sel = Not(in_=inputs.sel).out
    for i in range(3):
        fromAneg = Nand(a=inputs.a[i], b=not_sel).out
        fromBneg = Nand(a=inputs.b[i], b=inputs.sel).out
        outputs.out[i] = Nand(a=fromAneg, b=fromBneg).out


@chip
def Nand16(inputs, outputs):
    for i in range(16):
        outputs.out[i] = Nand(a=inputs.a[i], b=inputs.b[i]).out


# Copied from threaded.py (which has some commentary on it)
@chip
def Eq16(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # 5 gates for this. Can that be improved?
    @chip
    def Eq(inputs, outputs):
        outputs.out = Not(in_=Xor(a=inputs.a, b=inputs.b).out).out

    # Obviously in hardware you can do many-way And, but we don't simulate fan-in.
    outputs.out = And(
        a=And(a=And(a=And(a=Eq(a=a[15], b=b[15]).out,
                          b=Eq(a=a[14], b=b[14]).out).out,
                    b=And(a=Eq(a=a[13], b=b[13]).out,
                          b=Eq(a=a[12], b=b[12]).out).out).out,
              b=And(a=And(a=Eq(a=a[11], b=b[11]).out,
                          b=Eq(a=a[10], b=b[10]).out).out,
                    b=And(a=Eq(a=a[ 9], b=b[ 9]).out,
                          b=Eq(a=a[ 8], b=b[ 8]).out).out).out).out,
        b=And(a=And(a=And(a=Eq(a=a[ 7], b=b[ 7]).out,
                          b=Eq(a=a[ 6], b=b[ 6]).out).out,
                    b=And(a=Eq(a=a[ 5], b=b[ 5]).out,
                          b=Eq(a=a[ 4], b=b[ 4]).out).out).out,
              b=And(a=And(a=Eq(a=a[ 3], b=b[ 3]).out,
                          b=Eq(a=a[ 2], b=b[ 2]).out).out,
                    b=And(a=Eq(a=a[ 1], b=b[ 1]).out,
                          b=Eq(a=a[ 0], b=b[ 0]).out).out).out).out).out


# @chip
# def Mux8Way(inputs, outputs):
#     # Share not_sel to save a total of 4 gates:
#     @chip
#     def MuxPlus(inputs, outputs):
#         fromAneg = Nand(a=inputs.a, b=inputs.not_sel).out
#         fromBneg = Nand(a=inputs.b, b=inputs.sel).out
#         outputs.out = Nand(a=fromAneg, b=fromBneg).out

#     not_sel0 = Not(in_=inputs.sel[0]).out
#     ab = MuxPlus(a=inputs.a, b=inputs.b, not_sel=not_sel0, sel=inputs.sel[0]).out
#     cd = MuxPlus(a=inputs.c, b=inputs.d, not_sel=not_sel0, sel=inputs.sel[0]).out
#     ef = MuxPlus(a=inputs.e, b=inputs.f, not_sel=not_sel0, sel=inputs.sel[0]).out
#     gh = MuxPlus(a=inputs.g, b=inputs.h, not_sel=not_sel0, sel=inputs.sel[0]).out
#     not_sel1 = Not(in_=inputs.sel[1]).out
#     abcd = MuxPlus(a=ab, b=cd, not_sel=not_sel1, sel=inputs.sel[1]).out
#     efgh = MuxPlus(a=ef, b=gh, not_sel=not_sel1, sel=inputs.sel[1]).out
#     outputs.out = Mux(a=abcd, b=efgh, sel=inputs.sel[2]).out


@chip
def ALU(inputs, outputs):
    src1 = inputs.src1
    src2 = inputs.src2
    op = inputs.op  # 0 = ADD, 1 = NAND, 2 = PASS1, 3 = EQ?

    outputs.out = Mux16(
                    a=Mux16(
                        a=Add16(a=src1, b=src2).out,   # 00: ADD
                        b=Nand16(a=src1, b=src2).out,  # 01: NAND
                        sel=op[0]).out,
                    b=Mux16(
                        a=src1,  # 10: PASS1
                        b=0,     # 11: EQ? (result not used)
                        sel=op[0]).out,
                    sel=op[1]).out
    outputs.eq = Eq16(a=src1, b=src2).out


@chip
def RegisterFile(inputs, outputs):
    """Not much to look at, but an awful lot of gates to route signals for three (3-bit)
    addresses inputs, one 16-bit data input, and two (16-bit) data outputs, plus the 7
    Registers themselves. In fact, this is something like half of the gates. However,
    that's probably not quite realistic; more specialized layout for a register file
    would do better.
    """

    address1 = inputs.address1
    address2 = inputs.address2

    in_ = inputs.in_
    load = inputs.load
    target = inputs.target

    loadSel = DMux8Way(in_=load, sel=target)

    reg1 = Register(in_=in_, load=loadSel.b)
    reg2 = Register(in_=in_, load=loadSel.c)
    reg3 = Register(in_=in_, load=loadSel.d)
    reg4 = Register(in_=in_, load=loadSel.e)
    reg5 = Register(in_=in_, load=loadSel.f)
    reg6 = Register(in_=in_, load=loadSel.g)
    reg7 = Register(in_=in_, load=loadSel.h)

    outputs.out1 = Mux8Way16(
        a=0,
        b=reg1.out,
        c=reg2.out,
        d=reg3.out,
        e=reg4.out,
        f=reg5.out,
        g=reg6.out,
        h=reg7.out,
        sel=address1).out
    outputs.out2 = Mux8Way16(
        a=0,
        b=reg1.out,
        c=reg2.out,
        d=reg3.out,
        e=reg4.out,
        f=reg5.out,
        g=reg6.out,
        h=reg7.out,
        sel=address2).out

    # Note: exposed so the CPU and Computer can expose SP, which is used by some tests.
    outputs.reg1 = reg1.out


@chip
def Shift6(inputs, outputs):
    """
    >>> run(Shift6, in_=1).out
    64
    >>> run(Shift6, in_=-123).out
    -7872
    """
    for i in range(16):
        if i < 6:
            outputs.out[i] = 0
        else:
            outputs.out[i] = inputs.in_[i-6]

@chip
def Extend7(inputs, outputs):
    """
    >>> run(Extend7, in_=1).out
    1
    >>> run(Extend7, in_=-64).out
    -64
    """
    for i in range(16):
        if i < 7:
            outputs.out[i] = inputs.in_[i]
        else:
            outputs.out[i] = inputs.in_[6]

@chip
def Bus3(inputs, outputs):
    """Wiring only: assemble three signals into a 3-bit bus."""
    outputs.out[0] = inputs.in0
    outputs.out[1] = inputs.in1
    outputs.out[2] = inputs.in2

@chip
def Control(inputs, outputs):
    op = inputs.op

    # TODO: just write down the table and synthesize an implementation, either with a custom
    # PLA component (for efficient simulation), or just as a big DAG.

    # def switch(*output_bits):
    #     return Mux8Way(
    #         a=output_bits[0],
    #         b=output_bits[1],
    #         c=output_bits[2],
    #         d=output_bits[3],
    #         e=output_bits[4],
    #         f=output_bits[5],
    #         g=output_bits[6],
    #         h=output_bits[7],
    #         sel=op).out

    # Just to signify cases where the signal is expected to have no effect, mostly
    # because the ALU op will be PASS1, so src2 is ignored.
    # na = 0

    t0 = inputs.op[0]
    f0 = Not(in_=t0).out
    t1 = inputs.op[1]
    f1 = Not(in_=t1).out
    t2 = inputs.op[2]
    f2 = Not(in_=t2).out

    @chip
    def And3(inputs, outputs):
        outputs.out = And(a=inputs.a, b=And(a=inputs.b, b=inputs.c).out).out

    #  add,  addi, nand, lui,  lw,   sw,   beq,  jalr
    # outputs.registerLoad = switch(
    #     1,    1,    1,    1,    1,    0,    0,   1)
    # outputs.registerLoad = Nand(a=t2, b=Or(a=And(a=t1, b=f0).out, b=And(a=f1, b=t0).out).out).out
    outputs.registerLoad = Nand(a=t2, b=Nand(a=Nand(a=t1, b=f0).out, b=Nand(a=f1, b=t0).out).out).out
    # outputs.registerAddress2Sel = switch(              # 0 = regA, 1 = regC
    #     1,    na,   1,    na,   na,   0,    0,   na)
    outputs.registerAddress2Sel = f2
    # outputs.aluSrc1Sel = switch(                       # 0 = rf1, 1 = shifted 10-bit immediate
    #     0,    0,    0,    1,    0,    0,    0,   0)
    outputs.aluSrc1Sel = And3(a=f2, b=t1, c=t0).out
    # outputs.aluSrc2Sel = switch(                       # 0 = rf2, 1 = sign-extended 7-bit immediate
    #     0,    1,    0,    na,   1,    1,    0,   na)
    # outputs.aluSrc2Sel = Or(a=And(a=f1, b=t0).out, b=And(a=t2, b=f1).out).out
    outputs.aluSrc2Sel = Nand(a=Nand(a=f1, b=t0).out, b=Nand(a=t2, b=f1).out).out
    # outputs.aluOp[0] = switch(                         # 00 = ADD, 01 = NAND, 10 = PASS1, 11 = EQ?
    #     0,    0,    1,    0,    0,    0,    1,   0)
    outputs.aluOp[0] = And(a=t1, b=f0).out
    # outputs.aluOp[1] = switch(
    #     0,    0,    0,    1,    0,    0,    1,   1)
    # outputs.aluOp[1] = Or(a=And(a=t1, b=t0).out, b=And(a=t2, b=t1).out).out
    outputs.aluOp[1] = Nand(a=Nand(a=t1, b=t0).out, b=Nand(a=t2, b=t1).out).out
    # outputs.memLoad = switch(
    #     0,    0,    0,    0,    0,    1,    0,   0)  # write value from the ALU to memory
    outputs.memLoad = And3(a=t2, b=f1, c=t0).out
    # outputs.loadMem = switch(
    #     0,    0,    0,    0,    1,    0,    0,   0)  # write value from memory to the register file
    outputs.loadMem = And3(a=t2, b=f1, c=f0).out
    # outputs.isJump = switch(
    #     0,    0,    0,    0,    0,    0,    0,   1)
    outputs.isJump = And3(a=t2, b=t1, c=t0).out
    # outputs.isBranch = switch(
    #     0,    0,    0,    0,    0,    0,    1,   0)
    outputs.isBranch = And3(a=t2, b=t1, c=f0).out


# @chip
# def Add16_7(inputs, outputs):
#     """Add a (16 bits) and b (7 bits), treating the high bit of b as a sign bit."""
#     a = inputs.a
#     b = inputs.b

#     add0 = HalfAdder(a=a[0], b=b[0])
#     outputs.out[0] = add0.sum
#     carry = add0.carry

#     for i in range(1, 7):
#         addi = FullAdder(a=a[i], b=b[i], c=carry)
#         outputs.out[i] = addi.sum
#         carry = addi.carry

#     for i in range(7, 16):
#         addi = FullAdder(a=a[i], b=b[6], c=carry)
#         outputs.out[i] = 0
#         carry = addi.carry

@chip
def CPU(inputs, outputs):
    inM = inputs.inM                 # Contents of RAM[addressM]
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).

    registers = lazy()
    pc = lazy()

    op =   Bus3(in0=instruction[13], in1=instruction[14], in2=instruction[15]).out
    regA = Bus3(in0=instruction[10], in1=instruction[11], in2=instruction[12]).out
    regB = Bus3(in0=instruction[ 7], in1=instruction[ 8], in2=instruction[ 9]).out
    regC = Bus3(in0=instruction[ 0], in1=instruction[ 1], in2=instruction[ 2]).out

    imm10 = Shift6(in_=instruction).out
    imm7 = Extend7(in_=instruction).out

    # Note: not including the logic that needs alu.eq
    control = Control(op=op)

    alu = ALU(
        src1=Mux16(a=registers.out1, b=imm10, sel=control.aluSrc1Sel).out,
        src2=Mux16(a=registers.out2, b=imm7, sel=control.aluSrc2Sel).out,
        op=control.aluOp)

    registers.set(RegisterFile(
        address1=regB,
        address2=Mux3(a=regA, b=regC, sel=control.registerAddress2Sel).out,
        load=control.registerLoad,
        target=regA,
        in_=Mux16(
            a=Mux16(
                a=alu.out,
                b=inM,
                sel=control.loadMem).out,
            b=pc.nxt,
            sel=control.isJump).out))


    # Yikes! This is a second adder just for branch targets, because the ALU is busy,
    # but this is faithful to the original design. Note: it's still a full 16-bit adder,
    # even though one of the operands is nominally only 7 bits, because it gets
    # sign extended to a 16-bit value (that is, the upper 9 bits aren't actually
    # constant.)
    # Alternatively, could pull EQ? out of the ALU (with some additional logic.)
    branch_target = Add16(a=pc.nxt, b=imm7).out

    pc.set(PC(
        in_=Mux16(a=branch_target, b=alu.out, sel=control.isJump).out,
        load=Or(a=And(a=control.isBranch, b=alu.eq).out, b=control.isJump).out,
        inc=1,
        reset=reset))

    outputs.outM = registers.out2            # Value to write
    outputs.writeM = control.memLoad         # Write to M?
    outputs.addressM = alu.out               # Address in data memory (latched)  !!! no it isn't
    outputs.pc = pc.out                      # Address of next instruction (latched)
    outputs.sp = registers.reg1


@chip
def RiSCComputer(inputs, outputs):
    """This is the same as regular Computer, except using the RiSC CPU, plus exposing reg1 as sp."""

    reset = inputs.reset

    cpu = lazy()

    rom = ROM(15)(address=cpu.pc)

    mem = MemorySystem(in_=cpu.outM, load=cpu.writeM, address=cpu.addressM)

    cpu.set(CPU(inM=mem.out, instruction=rom.out, reset=reset))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc
    outputs.tty_ready = mem.tty_ready

    outputs.sp = cpu.sp  # This is inspected by some tests (and the debugger)


# print("ALU", gate_count(ALU))
# print("RegisterFile", gate_count(RegisterFile))
# print("CPU", gate_count(CPU))
# print("Computer", gate_count(RiSCComputer))
