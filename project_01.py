from Nand import *


def mkNot(inputs, outputs):
    in_ = inputs.in_
    n = Nand(a=in_, b=in_)
    outputs.out = n.out

Not = Component(mkNot)


def mkOr(inputs, outputs):
    a = inputs.a
    b = inputs.b
    notA = Not(in_=a)
    notB = Not(in_=b)
    notNotBoth = Nand(a=notA.out, b=notB.out)
    outputs.out = notNotBoth.out

Or = Component(mkOr)


def mkAnd(inputs, outputs):
    a = inputs.a
    b = inputs.b
    notAandB = Nand(a=a, b=b).out
    outputs.out = Not(in_=notAandB).out

And = Component(mkAnd)


def mkXor(inputs, outputs):
    a = inputs.a
    b = inputs.b
    nand = Nand(a=a, b=b).out
    nandANand = Nand(a=a, b=nand).out
    nandBNand = Nand(a=nand, b=b).out
    outputs.out = Nand(a=nandANand, b=nandBNand).out

Xor = Component(mkXor)


def mkMux(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel
    fromAneg = Nand(a=a, b=Not(in_=sel).out).out
    fromBneg = Nand(a=b, b=sel).out
    outputs.out = Nand(a=fromAneg, b=fromBneg).out

Mux = Component(mkMux)


def mkDMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel
    outputs.a = And(a=in_, b=Not(in_=sel).out).out
    outputs.b = And(a=in_, b=sel).out

DMux = Component(mkDMux)


def mkNot16(inputs, outputs):
    in_ = inputs.in_
    for i in range(16):
        outputs.out[i] = Not(in_=in_[i]).out

Not16 = Component(mkNot16)
        

# TODO:
# DMux4Way
# DMux8Way
# And16
# Mux16
# Mux4Way16
# Mux8Way16
