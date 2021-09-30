# Sequential Logic
#
# See https://www.nand2tetris.org/project03

from nand import build, clock

from project_01 import *
from project_02 import *

# SOLVERS: remove this import to get started
from nand.solutions import solved_03


def mkMyDFF(inputs, outputs):
    # Note: provided as a primitive in the Nand to Tetris simulator, but implementing it
    # from scratch is fun.

    in_ = inputs.in_
    enable = inputs.enable

    # SOLVERS: replace this with one or more Nands and/or components defined above
    # Hint: you can use `clock` as an input to any component.
    n1 = solved_03.MyDFF(in_=in_)

    outputs.out = n1.out

MyDFF = build(mkMyDFF)


def mkBit(inputs, outputs):
    # OK to use the primitive DFF here, for the most efficient result.

    in_ = inputs.in_
    load = inputs.load

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_03.Bit(in_=in_, load=load)

    outputs.out = n1.out

Bit = build(mkBit)


def mkRegister(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_03.Register(in_=in_, load=load)

    outputs.out = n1.out

Register = build(mkRegister)


def mkRAM8(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_03.RAM8(in_=in_, load=load, address=address)

    outputs.out = n1.out

RAM8 = build(mkRAM8)


def mkRAM64(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_03.RAM64(in_=in_, load=load, address=address)

    outputs.out = n1.out

RAM64 = build(mkRAM64)


def mkRAM512(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_03.RAM512(in_=in_, load=load, address=address)

    outputs.out = n1.out

RAM512 = build(mkRAM512)


# SOLVERS: This has gotten repetitive by now, so just use the provided RAM4K and RAM16K
RAM4K = solved_03.RAM4K
RAM16K = solved_03.RAM16K


def mkPC(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    inc = inputs.inc
    reset = inputs.reset

    # SOLVERS: replace this with one or more Nands and/or components defined above
    n1 = solved_03.PC(in_=in_, load=load, inc=inc, reset=reset)

    outputs.out = n1.out

PC = build(mkPC)
