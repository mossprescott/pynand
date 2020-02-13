# See https://www.nand2tetris.org/project02

from nand import Nand, build
from project_01 import And, And16, Or, Mux16, Not, Not16, Xor

# SOLVERS: remove this import to get started
from nand.solutions import solved_02


def mkHalfAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.HalfAdder(a=a, b=b)

    outputs.sum = n1.sum
    outputs.carry = n1.carry

HalfAdder = build(mkHalfAdder)


def mkFullAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.FullAdder(a=a, b=b, c=c)

    outputs.sum = n1.sum
    outputs.carry = n1.carry

FullAdder = build(mkFullAdder)


def mkInc16(inputs, outputs):
    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Inc16(in_=in_)

    outputs.out = n1.out

Inc16 = build(mkInc16)


def mkAdd16(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Add16(a=a, b=b)

    outputs.out = n1.out

Add16 = build(mkAdd16)


def mkZero16(inputs, outputs):
    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Zero16(in_=in_)

    outputs.out = n1.out

Zero16 = build(mkZero16)


def mkALU(inputs, outputs):
    x = inputs.x
    y = inputs.y

    zx = inputs.zx
    nx = inputs.nx
    zy = inputs.zy
    ny = inputs.ny
    f  = inputs.f
    no = inputs.no

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.ALU(x=x, y=y, zx=zx, nx=nx, zy=zy, ny=ny, f=f, no=no)

    outputs.out = n1.out
    outputs.zr = n1.zr
    outputs.ng = n1.ng
    
ALU = build(mkALU)