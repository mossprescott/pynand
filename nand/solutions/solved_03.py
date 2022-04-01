"""Solutions for project 03.

SPOILER ALERT: this files contains complete and optimal solutions for all the exercises.
If you want to solve them on your own, stop reading now!
"""

from nand import chip
from nand.solutions.solved_01 import *
from nand.solutions.solved_02 import *


@chip
def MyDFF(inputs, outputs):
    # Note: provided as a primitive in the Nand to Tetris simulator, but implementing it
    # from scratch is fun.

    @chip
    def Latch(inputs, outputs):
        mux = lazy()
        mux.set(Mux(a=mux.out, b=inputs.in_, sel=inputs.enable))
        outputs.out = mux.out

    l1 = Latch(in_=inputs.in_, enable=clock)
    l2 = Latch(in_=l1.out, enable=Not(in_=clock).out)

    outputs.out = l2.out


@chip
def Bit(inputs, outputs):
    # OK to use DynamicDFF here, for the most efficient result.

    in_ = inputs.in_
    load = inputs.load
    dff = lazy()
    mux = Mux(a=dff.out, b=inputs.in_, sel=inputs.load)
    dff.set(DFF(in_=mux.out))
    outputs.out = dff.out


@chip
def Register(inputs, outputs):
    for i in range(16):
        outputs.out[i] = Bit(in_=inputs.in_[i], load=inputs.load).out


# Note: these RAMs don't latch the address and delay delivery of the output until the following
# cycle, as the "real" RAM is allowed/required to do. That's ok, because implementing RAM from
# DFFs like this is an unrealistic exercise anyway. The tests for this project allow either
# behavior.

@chip
def RAM8(inputs, outputs):
    load = DMux8Way(in_=inputs.load, sel=inputs.address)
    reg0 = Register(in_=inputs.in_, load=load.a)
    reg1 = Register(in_=inputs.in_, load=load.b)
    reg2 = Register(in_=inputs.in_, load=load.c)
    reg3 = Register(in_=inputs.in_, load=load.d)
    reg4 = Register(in_=inputs.in_, load=load.e)
    reg5 = Register(in_=inputs.in_, load=load.f)
    reg6 = Register(in_=inputs.in_, load=load.g)
    reg7 = Register(in_=inputs.in_, load=load.h)
    outputs.out = Mux8Way16(a=reg0.out, b=reg1.out, c=reg2.out, d=reg3.out,
                            e=reg4.out, f=reg5.out, g=reg6.out, h=reg7.out,
                            sel=inputs.address).out


@chip
def RAM64(inputs, outputs):
    @chip
    def RShift3(inputs, outputs):
        outputs.out[0] = inputs.in_[3]
        outputs.out[1] = inputs.in_[4]
        outputs.out[2] = inputs.in_[5]

    shifted = RShift3(in_=inputs.address)
    load = DMux8Way(in_=inputs.load, sel=shifted.out)
    ram0 = RAM8(in_=inputs.in_, load=load.a, address=inputs.address)
    ram1 = RAM8(in_=inputs.in_, load=load.b, address=inputs.address)
    ram2 = RAM8(in_=inputs.in_, load=load.c, address=inputs.address)
    ram3 = RAM8(in_=inputs.in_, load=load.d, address=inputs.address)
    ram4 = RAM8(in_=inputs.in_, load=load.e, address=inputs.address)
    ram5 = RAM8(in_=inputs.in_, load=load.f, address=inputs.address)
    ram6 = RAM8(in_=inputs.in_, load=load.g, address=inputs.address)
    ram7 = RAM8(in_=inputs.in_, load=load.h, address=inputs.address)
    outputs.out = Mux8Way16(a=ram0.out, b=ram1.out, c=ram2.out, d=ram3.out,
                            e=ram4.out, f=ram5.out, g=ram6.out, h=ram7.out,
                            sel=shifted.out).out


@chip
def RAM512(inputs, outputs):
    @chip
    def RShift6(inputs, outputs):
        outputs.out[0] = inputs.in_[6]
        outputs.out[1] = inputs.in_[7]
        outputs.out[2] = inputs.in_[8]

    shifted = RShift6(in_=inputs.address)
    load = DMux8Way(in_=inputs.load, sel=shifted.out)
    ram0 = RAM64(in_=inputs.in_, load=load.a, address=inputs.address)
    ram1 = RAM64(in_=inputs.in_, load=load.b, address=inputs.address)
    ram2 = RAM64(in_=inputs.in_, load=load.c, address=inputs.address)
    ram3 = RAM64(in_=inputs.in_, load=load.d, address=inputs.address)
    ram4 = RAM64(in_=inputs.in_, load=load.e, address=inputs.address)
    ram5 = RAM64(in_=inputs.in_, load=load.f, address=inputs.address)
    ram6 = RAM64(in_=inputs.in_, load=load.g, address=inputs.address)
    ram7 = RAM64(in_=inputs.in_, load=load.h, address=inputs.address)
    outputs.out = Mux8Way16(a=ram0.out, b=ram1.out, c=ram2.out, d=ram3.out,
                            e=ram4.out, f=ram5.out, g=ram6.out, h=ram7.out,
                            sel=shifted.out).out


# Note: here's an implementation which is probably correct, but the resulting chip
# is so large when it's flattened that it's no fun actually trying to simulate it.
@chip
def RAM4K(inputs, outputs):
    @chip
    def RShift9(inputs, outputs):
        outputs.out[0] = inputs.in_[9]
        outputs.out[1] = inputs.in_[10]
        outputs.out[2] = inputs.in_[11]

    shifted = RShift9(in_=inputs.address)
    load = DMux8Way(in_=inputs.load, sel=shifted.out)
    ram0 = RAM512(in_=inputs.in_, load=load.a, address=inputs.address)
    ram1 = RAM512(in_=inputs.in_, load=load.b, address=inputs.address)
    ram2 = RAM512(in_=inputs.in_, load=load.c, address=inputs.address)
    ram3 = RAM512(in_=inputs.in_, load=load.d, address=inputs.address)
    ram4 = RAM512(in_=inputs.in_, load=load.e, address=inputs.address)
    ram5 = RAM512(in_=inputs.in_, load=load.f, address=inputs.address)
    ram6 = RAM512(in_=inputs.in_, load=load.g, address=inputs.address)
    ram7 = RAM512(in_=inputs.in_, load=load.h, address=inputs.address)
    outputs.out = Mux8Way16(a=ram0.out, b=ram1.out, c=ram2.out, d=ram3.out,
                            e=ram4.out, f=ram5.out, g=ram6.out, h=ram7.out,
                            sel=shifted.out).out


# Note: this is just wrapping the built-in RAM primitive, so we can test that its interface
# is the same as the rest.
RAM16K = RAM(14)
"""14 address bits yields a 16K memory."""


@chip
def PC(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    inc = inputs.inc
    reset = inputs.reset

    reseted = lazy()
    pc = Register(in_=reseted.out, load=1)

    nxt = Inc16(in_=pc.out).out
    inced = Mux16(a=pc.out, b=nxt, sel=inc)
    loaded = Mux16(a=inced.out, b=in_, sel=load)
    reseted.set(Mux16(a=loaded.out, b=0, sel=reset))

    outputs.out = pc.out
    # Note: the address of the next instruction may be useful even if we're not going there,
    # so expose it in case some other component wants to use it.
    outputs.nxt = nxt
