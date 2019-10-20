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


def mkDMux4Way(inputs, outputs):
    # TODO: optimal?
    in_ = inputs.in_
    sel = inputs.sel
    lo = DMux(in_=in_, sel=sel[0])
    outputs.a = DMux(in_=lo.a, sel=sel[1]).a
    outputs.b = DMux(in_=lo.b, sel=sel[1]).a
    outputs.c = DMux(in_=lo.a, sel=sel[1]).b
    outputs.d = DMux(in_=lo.b, sel=sel[1]).b
    
DMux4Way = Component(mkDMux4Way)


def mkDMux8Way(inputs, outputs):
    # TODO: optimal?
    # TODO: implement bit slice syntax and use DMux4Way?
    in_ = inputs.in_
    sel = inputs.sel
    lo = DMux(in_=in_, sel=sel[0])
    lo0 = DMux(in_=lo.a, sel=sel[1])
    lo1 = DMux(in_=lo.b, sel=sel[1])
    outputs.a = DMux(in_=lo0.a, sel=sel[2]).a
    outputs.b = DMux(in_=lo1.a, sel=sel[2]).a
    outputs.c = DMux(in_=lo0.b, sel=sel[2]).a
    outputs.d = DMux(in_=lo1.b, sel=sel[2]).a
    outputs.e = DMux(in_=lo0.a, sel=sel[2]).b
    outputs.f = DMux(in_=lo1.a, sel=sel[2]).b
    outputs.g = DMux(in_=lo0.b, sel=sel[2]).b
    outputs.h = DMux(in_=lo1.b, sel=sel[2]).b
    
DMux8Way = Component(mkDMux8Way)


def mkNot16(inputs, outputs):
    in_ = inputs.in_
    for i in range(16):
        outputs.out[i] = Not(in_=in_[i]).out

Not16 = Component(mkNot16)
        

def mkAnd16(inputs, outputs):
    for i in range(16):
        outputs.out[i] = And(a=inputs.a[i], b=inputs.b[i]).out

And16 = Component(mkAnd16)


def mkMux16(inputs, outputs):
    for i in range(16):
        outputs.out[i] = Mux(a=inputs.a[i], b=inputs.b[i], sel=inputs.sel).out

Mux16 = Component(mkMux16)


def mkMux4Way16(inputs, outputs):
    # decode only once for fewer gates?
    ab = Mux16(a=inputs.a, b=inputs.b, sel=inputs.sel[0]).out
    cd = Mux16(a=inputs.c, b=inputs.d, sel=inputs.sel[0]).out
    outputs.out = Mux16(a=ab, b=cd, sel=inputs.sel[1]).out    

Mux4Way16 = Component(mkMux4Way16)


def mkMux8Way16(inputs, outputs):
    ab = Mux16(a=inputs.a, b=inputs.b, sel=inputs.sel[0]).out
    cd = Mux16(a=inputs.c, b=inputs.d, sel=inputs.sel[0]).out
    ef = Mux16(a=inputs.e, b=inputs.f, sel=inputs.sel[0]).out
    gh = Mux16(a=inputs.g, b=inputs.h, sel=inputs.sel[0]).out
    abcd = Mux16(a=ab, b=cd, sel=inputs.sel[1]).out
    efgh = Mux16(a=ef, b=gh, sel=inputs.sel[1]).out
    outputs.out = Mux16(a=abcd, b=efgh, sel=inputs.sel[2]).out
            
Mux8Way16 = Component(mkMux8Way16)
