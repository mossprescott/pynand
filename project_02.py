from Nand import *
from project_01 import And, And16, Or, Mux16, Not, Not16, Xor

def mkHalfAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b
    
    nand = Nand(a=a, b=b).out

    # Xor:
    nandANand = Nand(a=a, b=nand).out
    nandBNand = Nand(a=nand, b=b).out
    outputs.sum = Nand(a=nandANand, b=nandBNand).out

    # And:
    outputs.carry = Not(in_=nand).out

HalfAdder = Component(mkHalfAdder)


def mkFullAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    ab = HalfAdder(a=a, b=b)

    absum_nand_c = Nand(a=ab.sum, b=c).out

    # Xor:
    nandSumNand = Nand(a=ab.sum, b=absum_nand_c).out
    nandCNand = Nand(a=absum_nand_c, b=c).out
    outputs.sum = Nand(a=nandSumNand, b=nandCNand).out

    # Or(ab.carry, Not(absum_nand_c))
    outputs.carry = Nand(a=Not(in_=ab.carry).out, b=absum_nand_c).out

FullAdder = Component(mkFullAdder)


def mkInc16(inputs, outputs):
    a = HalfAdder(a=inputs.in_[0], b=Const(1))
    outputs.out[0] = a.sum
    for i in range(1, 16):
        tmp = HalfAdder(a=inputs.in_[i], b=a.carry)
        outputs.out[i] = tmp.sum
        a = tmp

Inc16 = Component(mkInc16)


def mkAdd16(inputs, outputs):
    a = HalfAdder(a=inputs.a[0], b=inputs.b[0])
    outputs.out[0] = a.sum
    for i in range(1, 16):
        tmp = FullAdder(a=inputs.a[i], b=inputs.b[i], c=a.carry)
        outputs.out[i] = tmp.sum
        a = tmp

Add16 = Component(mkAdd16)


def mkALU(inputs, outputs):
    x = inputs.x
    y = inputs.y
    
    zx = inputs.zx
    nx = inputs.nx
    zy = inputs.zy
    ny = inputs.ny
    f  = inputs.f
    no = inputs.no
    
    x_zeroed = Mux16(a=x, b=Const(0), sel=zx).out
    y_zeroed = Mux16(a=y, b=Const(0), sel=zy).out

    x_inverted = Mux16(a=x_zeroed, b=Not16(in_=x_zeroed).out, sel=nx).out
    y_inverted = Mux16(a=y_zeroed, b=Not16(in_=y_zeroed).out, sel=ny).out
    
    anded = And16(a=x_inverted, b=y_inverted).out
    added = Add16(a=x_inverted, b=y_inverted).out
    
    result = Mux16(a=anded, b=added, sel=f).out
    result_inverted = Not16(in_=result).out
    
    outputs.out = Mux16(a=result, b=result_inverted, sel=no).out
    
ALU = Component(mkALU)