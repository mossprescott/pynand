from nand import Component, lazy
from project_01 import *
from project_02 import *


def mkDFF(inputs, outputs):
    # Note: provided as a primitive in the Nand to Tetris simulator, but implementing it
    # from scratch is fun.

    def mkLatch(inputs, outputs):
        mux = lazy()
        mux.set(Mux(a=mux.out, b=inputs.in_, sel=inputs.enable))
        outputs.out = mux.out
    Latch = Component(mkLatch)
    
    l1 = Latch(in_=inputs.in_, enable=clock)
    l2 = Latch(in_=l1.out, enable=Not(in_=clock).out)
    
    outputs.out = l2.out

DFF = Component(mkDFF)


def mkBit(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    dff = lazy()
    mux = Mux(a=dff.out, b=inputs.in_, sel=inputs.load)
    dff.set(DFF(in_=mux.out))
    outputs.out = dff.out

Bit = Component(mkBit)


def mkRegister(inputs, outputs):
    for i in range(16):
        outputs.out[i] = Bit(in_=inputs.in_[i], load=inputs.load).out
        
Register = Component(mkRegister)


def mkRAM8(inputs, outputs):
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
    
RAM8 = Component(mkRAM8)


def mkRAM64(inputs, outputs):
    def mkRShift3(inputs, outputs):
        outputs.out[0] = inputs.in_[3]
        outputs.out[1] = inputs.in_[4]
        outputs.out[2] = inputs.in_[5]
    RShift3 = Component(mkRShift3)

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

RAM64 = Component(mkRAM64)


def mkRAM512(inputs, outputs):
    pass

def mkRAM4K(inputs, outputs):
    pass

def mkRAM16K(inputs, outputs):
    pass

def mkPC(inputs, outputs):
    pass