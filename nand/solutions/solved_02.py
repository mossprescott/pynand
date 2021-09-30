"""Solutions for project 02.

SPOILER ALERT: this files contains complete and optimal solutions for all the exercises.
If you want to solve them on your own, stop reading now!
"""

from nand import *

from nand.solutions.solved_01 import And, And16, Or, Mux16, Not, Not16, Xor


@chip
def HalfAdder(inputs, outputs):
    a = inputs.a
    b = inputs.b

    nand = Nand(a=a, b=b).out

    # Xor(a, b):
    nandANand = Nand(a=a, b=nand).out
    nandBNand = Nand(a=nand, b=b).out
    outputs.sum = Nand(a=nandANand, b=nandBNand).out

    # And(a, b):
    outputs.carry = Not(in_=nand).out


@chip
def FullAdder(inputs, outputs):
    @chip
    def HalfAdderNot(inputs, outputs):
        """Half-adder with one less gate by exposing the opposite of carry."""
        nand = Nand(a=inputs.a, b=inputs.b).out
        nandANand = Nand(a=inputs.a, b=nand).out
        nandBNand = Nand(a=nand, b=inputs.b).out
        outputs.sum = Nand(a=nandANand, b=nandBNand).out
        outputs.not_carry = nand

    ab = HalfAdderNot(a=inputs.a, b=inputs.b)
    abc = HalfAdderNot(a=ab.sum, b=inputs.c)
    outputs.carry = Nand(a=ab.not_carry, b=abc.not_carry).out
    outputs.sum = abc.sum


@chip
def Inc16(inputs, outputs):
    # Don't even need a whole HalfAdder for the low bit:
    outputs.out[0] = Not(in_=inputs.in_[0]).out
    carry = inputs.in_[0]
    for i in range(1, 16):
        tmp = HalfAdder(a=carry, b=inputs.in_[i])
        outputs.out[i] = tmp.sum
        carry = tmp.carry


@chip
def Add16(inputs, outputs):
    a = HalfAdder(a=inputs.a[0], b=inputs.b[0])
    outputs.out[0] = a.sum
    for i in range(1, 16):
        tmp = FullAdder(a=inputs.a[i], b=inputs.b[i], c=a.carry)
        outputs.out[i] = tmp.sum
        a = tmp


@chip
def Zero16(inputs, outputs):
    in_ = inputs.in_
    outputs.out = And(
        a=And(a=And(a=And(a=Not(in_=in_[15]).out,
                          b=Not(in_=in_[14]).out).out,
                    b=And(a=Not(in_=in_[13]).out,
                          b=Not(in_=in_[12]).out).out).out,
              b=And(a=And(a=Not(in_=in_[11]).out,
                          b=Not(in_=in_[10]).out).out,
                    b=And(a=Not(in_=in_[ 9]).out,
                          b=Not(in_=in_[ 8]).out).out).out).out,
        b=And(a=And(a=And(a=Not(in_=in_[ 7]).out,
                          b=Not(in_=in_[ 6]).out).out,
                    b=And(a=Not(in_=in_[ 5]).out,
                          b=Not(in_=in_[ 4]).out).out).out,
              b=And(a=And(a=Not(in_=in_[ 3]).out,
                          b=Not(in_=in_[ 2]).out).out,
                    b=And(a=Not(in_=in_[ 1]).out,
                          b=Not(in_=in_[ 0]).out).out).out).out).out


@chip
def Neg16(inputs, outputs):
    outputs.out = inputs.in_[15]


@chip
def ALU(inputs, outputs):
    x = inputs.x
    y = inputs.y

    zx = inputs.zx
    nx = inputs.nx
    zy = inputs.zy
    ny = inputs.ny
    f  = inputs.f
    no = inputs.no

    x_zeroed = Mux16(a=x, b=0, sel=zx).out
    y_zeroed = Mux16(a=y, b=0, sel=zy).out

    x_inverted = Mux16(a=x_zeroed, b=Not16(in_=x_zeroed).out, sel=nx).out
    y_inverted = Mux16(a=y_zeroed, b=Not16(in_=y_zeroed).out, sel=ny).out

    anded = And16(a=x_inverted, b=y_inverted).out
    added = Add16(a=x_inverted, b=y_inverted).out

    result = Mux16(a=anded, b=added, sel=f).out
    result_inverted = Not16(in_=result).out

    out = Mux16(a=result, b=result_inverted, sel=no).out

    outputs.out = out
    outputs.zr = Zero16(in_=out).out
    outputs.ng = Neg16(in_=out).out
