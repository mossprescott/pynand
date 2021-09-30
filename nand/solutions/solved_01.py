"""Solutions for project 01.

SPOILER ALERT: this files contains complete and optimal solutions for all the exercises.
If you want to solve them on your own, stop reading now!
"""

from nand import *


@chip
def Not(inputs, outputs):
    in_ = inputs.in_
    n = Nand(a=in_, b=in_)
    outputs.out = n.out


@chip
def Or(inputs, outputs):
    a = inputs.a
    b = inputs.b
    notA = Not(in_=a)
    notB = Not(in_=b)
    notNotBoth = Nand(a=notA.out, b=notB.out)
    outputs.out = notNotBoth.out


@chip
def And(inputs, outputs):
    a = inputs.a
    b = inputs.b
    notAandB = Nand(a=a, b=b).out
    outputs.out = Not(in_=notAandB).out


@chip
def Xor(inputs, outputs):
    a = inputs.a
    b = inputs.b
    nand = Nand(a=a, b=b).out
    nandANand = Nand(a=a, b=nand).out
    nandBNand = Nand(a=nand, b=b).out
    outputs.out = Nand(a=nandANand, b=nandBNand).out


@chip
def Mux(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel
    fromAneg = Nand(a=a, b=Not(in_=sel).out).out
    fromBneg = Nand(a=b, b=sel).out
    outputs.out = Nand(a=fromAneg, b=fromBneg).out


@chip
def DMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel
    outputs.a = And(a=in_, b=Not(in_=sel).out).out
    outputs.b = And(a=in_, b=sel).out


@chip
def DMux4Way(inputs, outputs):
    @chip
    def DMuxPlus(inputs, outputs):
        outputs.a = And(a=inputs.in_, b=inputs.not_sel).out
        outputs.b = And(a=inputs.in_, b=inputs.sel).out

    # TODO: optimal?
    in_ = inputs.in_
    sel = inputs.sel
    lo = DMux(in_=in_, sel=sel[0])
    sel1 = sel[1]
    not_sel1 = Not(in_=sel1).out
    dmux1 = DMuxPlus(in_=lo.a, not_sel=not_sel1, sel=sel1)
    dmux2 = DMuxPlus(in_=lo.b, not_sel=not_sel1, sel=sel1)
    outputs.a = dmux1.a
    outputs.b = dmux2.a
    outputs.c = dmux1.b
    outputs.d = dmux2.b


@chip
def DMux8Way(inputs, outputs):
    @chip
    def DMuxPlus(inputs, outputs):
        outputs.a = And(a=inputs.in_, b=inputs.not_sel).out
        outputs.b = And(a=inputs.in_, b=inputs.sel).out
    # TODO: optimal?
    # TODO: implement bit slice syntax and use DMux4Way?
    in_ = inputs.in_
    sel = inputs.sel
    sel1 = sel[1]
    not_sel1 = Not(in_=sel1).out
    sel2 = sel[2]
    not_sel2 = Not(in_=sel2).out
    lo = DMux(in_=in_, sel=sel[0])
    lo0 = DMuxPlus(in_=lo.a, not_sel=not_sel1, sel=sel1)
    lo1 = DMuxPlus(in_=lo.b, not_sel=not_sel1, sel=sel1)
    dmux1 = DMuxPlus(in_=lo0.a, not_sel=not_sel2, sel=sel2)
    dmux2 = DMuxPlus(in_=lo1.a, not_sel=not_sel2, sel=sel2)
    dmux3 = DMuxPlus(in_=lo0.b, not_sel=not_sel2, sel=sel2)
    dmux4 = DMuxPlus(in_=lo1.b, not_sel=not_sel2, sel=sel2)
    outputs.a = dmux1.a
    outputs.b = dmux2.a
    outputs.c = dmux3.a
    outputs.d = dmux4.a
    outputs.e = dmux1.b
    outputs.f = dmux2.b
    outputs.g = dmux3.b
    outputs.h = dmux4.b


@chip
def Not16(inputs, outputs):
    in_ = inputs.in_
    for i in range(16):
        outputs.out[i] = Not(in_=in_[i]).out


@chip
def And16(inputs, outputs):
    for i in range(16):
        outputs.out[i] = And(a=inputs.a[i], b=inputs.b[i]).out


@chip
def Mux16(inputs, outputs):
    sel = inputs.sel
    not_sel = Not(in_=sel).out
    for i in range(16):
        fromAneg = Nand(a=inputs.a[i], b=not_sel).out
        fromBneg = Nand(a=inputs.b[i], b=sel).out
        outputs.out[i] = Nand(a=fromAneg, b=fromBneg).out


@chip
def Mux4Way16(inputs, outputs):
    # Share not_sel to save one gate:
    @chip
    def Mux16Plus(inputs, outputs):
        for i in range(16):
            fromAneg = Nand(a=inputs.a[i], b=inputs.not_sel).out
            fromBneg = Nand(a=inputs.b[i], b=inputs.sel).out
            outputs.out[i] = Nand(a=fromAneg, b=fromBneg).out

    not_sel0 = Not(in_=inputs.sel[0]).out
    ab = Mux16Plus(a=inputs.a, b=inputs.b, not_sel=not_sel0, sel=inputs.sel[0]).out
    cd = Mux16Plus(a=inputs.c, b=inputs.d, not_sel=not_sel0, sel=inputs.sel[0]).out
    outputs.out = Mux16(a=ab, b=cd, sel=inputs.sel[1]).out


@chip
def Mux8Way16(inputs, outputs):
    # Share not_sel to save a total of 4 gates:
    @chip
    def Mux16Plus(inputs, outputs):
        for i in range(16):
            fromAneg = Nand(a=inputs.a[i], b=inputs.not_sel).out
            fromBneg = Nand(a=inputs.b[i], b=inputs.sel).out
            outputs.out[i] = Nand(a=fromAneg, b=fromBneg).out

    not_sel0 = Not(in_=inputs.sel[0]).out
    ab = Mux16Plus(a=inputs.a, b=inputs.b, not_sel=not_sel0, sel=inputs.sel[0]).out
    cd = Mux16Plus(a=inputs.c, b=inputs.d, not_sel=not_sel0, sel=inputs.sel[0]).out
    ef = Mux16Plus(a=inputs.e, b=inputs.f, not_sel=not_sel0, sel=inputs.sel[0]).out
    gh = Mux16Plus(a=inputs.g, b=inputs.h, not_sel=not_sel0, sel=inputs.sel[0]).out
    not_sel1 = Not(in_=inputs.sel[1]).out
    abcd = Mux16Plus(a=ab, b=cd, not_sel=not_sel1, sel=inputs.sel[1]).out
    efgh = Mux16Plus(a=ef, b=gh, not_sel=not_sel1, sel=inputs.sel[1]).out
    outputs.out = Mux16(a=abcd, b=efgh, sel=inputs.sel[2]).out
