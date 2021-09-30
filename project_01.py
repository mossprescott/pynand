# Boolean Logic
#
# See https://www.nand2tetris.org/project01

from nand import Nand, chip

# SOLVERS: remove this import to get started
from nand.solutions import solved_01

@chip
def Not(inputs, outputs):
    in_ = inputs.in_

    # SOLVERS: replace this with a Nand
    n1 = solved_01.Not(in_=in_)

    outputs.out = n1.out


@chip
def Or(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and Nots
    n1 = solved_01.Or(a=a, b=b)

    outputs.out = n1.out


@chip
def And(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.And(a=a, b=b)

    outputs.out = n1.out


@chip
def Xor(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Xor(a=a, b=b)

    outputs.out = n1.out


@chip
def Mux(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux(a=a, b=b, sel=sel)

    outputs.out = n1.out


@chip
def DMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.DMux(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b


@chip
def DMux4Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: use sel[0] and sel[1] to extract each bit
    n1 = solved_01.DMux4Way(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b
    outputs.c = n1.c
    outputs.d = n1.d


@chip
def DMux8Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.DMux8Way(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b
    outputs.c = n1.c
    outputs.d = n1.d
    outputs.e = n1.e
    outputs.f = n1.f
    outputs.g = n1.g
    outputs.h = n1.h


@chip
def Not16(inputs, outputs):
    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: use outputs.out[0] = ... in_[0] ..., etc. to connect each bit of the output
    n1 = solved_01.Not16(in_=in_)

    outputs.out = n1.out


@chip
def And16(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.And16(a=a, b=b)

    outputs.out = n1.out


@chip
def Mux16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux16(a=a, b=b, sel=sel)

    outputs.out = n1.out


@chip
def Mux4Way16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    d = inputs.d
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux4Way16(a=a, b=b, c=c, d=d, sel=sel)

    outputs.out = n1.out


@chip
def Mux8Way16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    d = inputs.d
    e = inputs.e
    f = inputs.f
    g = inputs.g
    h = inputs.h
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux8Way16(a=a, b=b, c=c, d=d, e=e, f=f, g=g, h=h, sel=sel)

    outputs.out = n1.out
