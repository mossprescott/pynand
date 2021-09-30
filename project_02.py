# Boolean Arithmetic
#
# See https://www.nand2tetris.org/project02

from nand import Nand, chip
from project_01 import And, And16, Or, Mux16, Not, Not16, Xor

# SOLVERS: remove this import to get started
from nand.solutions import solved_02


@chip
def HalfAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.HalfAdder(a=a, b=b)

    outputs.sum = n1.sum
    outputs.carry = n1.carry


@chip
def FullAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b
    c = inputs.c

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.FullAdder(a=a, b=b, c=c)

    outputs.sum = n1.sum
    outputs.carry = n1.carry


@chip
def Inc16(inputs, outputs):
    """Add one to a single 16-bit input, ignoring overflow."""

    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Inc16(in_=in_)

    outputs.out = n1.out


@chip
def Add16(inputs, outputs):
    """Add two 16-bit inputs, ignoring overflow."""

    a = inputs.a
    b = inputs.b

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Add16(a=a, b=b)

    outputs.out = n1.out


@chip
def Zero16(inputs, outputs):
    """Test whether a single 16-bit input has the value 0."""

    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Zero16(in_=in_)

    outputs.out = n1.out


@chip
def Neg16(inputs, outputs):
    """Test whether a single 16-bit input is negative."""

    in_ = inputs.in_

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.Neg16(in_=in_)

    outputs.out = n1.out


@chip
def ALU(inputs, outputs):
    """Combine two 16-bit inputs according to six control bits, producing a 16-bit result and two
    condition codes.
    """

    x = inputs.x
    y = inputs.y

    zx = inputs.zx  # X is replaced by 0
    nx = inputs.nx  # X (or 0) is negated
    zy = inputs.zy  # Y is replaced by 0
    ny = inputs.ny  # Y (or 0) is negated
    f  = inputs.f   # if True, combine inputs with Add, otherwise, And
    no = inputs.no  # negate the output

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_02.ALU(x=x, y=y, zx=zx, nx=nx, zy=zy, ny=ny, f=f, no=no)

    outputs.out = n1.out  # the resulting value
    outputs.zr = n1.zr    # is the output equal to 0?
    outputs.ng = n1.ng    # is the output negative?
