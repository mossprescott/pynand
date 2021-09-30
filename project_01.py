# Boolean Logic
#
# See https://www.nand2tetris.org/project01

from nand import Nand, build

# SOLVERS: remove this import to get started
from nand.solutions import solved_01


def mkNot(inputs, outputs):
    in_ = inputs.in_

    # SOLVERS: replace this with a Nand
    n1 = solved_01.Not(in_=in_)

    outputs.out = n1.out

Not = build(mkNot)


def mkOr(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and Nots
    n1 = solved_01.Or(a=a, b=b)

    outputs.out = n1.out

Or = build(mkOr)


def mkAnd(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.And(a=a, b=b)

    outputs.out = n1.out

And = build(mkAnd)


def mkXor(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Xor(a=a, b=b)

    outputs.out = n1.out

Xor = build(mkXor)


def mkMux(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux(a=a, b=b, sel=sel)

    outputs.out = n1.out

Mux = build(mkMux)


def mkDMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.DMux(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b

DMux = build(mkDMux)


def mkDMux4Way(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: use sel[0] and sel[1] to extract each bit
    n1 = solved_01.DMux4Way(in_=in_, sel=sel)

    outputs.a = n1.a
    outputs.b = n1.b
    outputs.c = n1.c
    outputs.d = n1.d

DMux4Way = build(mkDMux4Way)


def mkDMux8Way(inputs, outputs):
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

DMux8Way = build(mkDMux8Way)


def mkNot16(inputs, outputs):
    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: use outputs.out[0]... to connect each bit of the output
    n1 = solved_01.Not16(in_=in_)

    outputs.out = n1.out

Not16 = build(mkNot16)


def mkAnd16(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.And16(a=a, b=b)

    outputs.out = n1.out

And16 = build(mkAnd16)


def mkMux16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux16(a=a, b=b, sel=sel)

    outputs.out = n1.out

Mux16 = build(mkMux16)


def mkMux4Way16(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c
    d = inputs.d
    sel = inputs.sel

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_01.Mux4Way16(a=a, b=b, c=c, d=d, sel=sel)

    outputs.out = n1.out

Mux4Way16 = build(mkMux4Way16)


def mkMux8Way16(inputs, outputs):
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

Mux8Way16 = build(mkMux8Way16)
