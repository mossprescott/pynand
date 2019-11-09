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
        outputs.out[i] = Bit(in_=inputs.in_[i], load=inputs.load, clock=inputs.clock).out
        
Register = Component(mkRegister)


def mkRAM8(inputs, outputs):
    load = DMux8Way(in_=inputs.load, sel=inputs.address)
    reg0 = Register(in_=inputs.in_, load=load.a, clock=inputs.clock)
    reg1 = Register(in_=inputs.in_, load=load.b, clock=inputs.clock)
    reg2 = Register(in_=inputs.in_, load=load.c, clock=inputs.clock)
    reg3 = Register(in_=inputs.in_, load=load.d, clock=inputs.clock)
    reg4 = Register(in_=inputs.in_, load=load.e, clock=inputs.clock)
    reg5 = Register(in_=inputs.in_, load=load.f, clock=inputs.clock)
    reg6 = Register(in_=inputs.in_, load=load.g, clock=inputs.clock)
    reg7 = Register(in_=inputs.in_, load=load.h, clock=inputs.clock)
    outputs.out = Mux8Way16(a=reg0.out, b=reg1.out, c=reg2.out, d=reg3.out,
                            e=reg4.out, f=reg5.out, g=reg6.out, h=reg7.out,
                            sel=inputs.address).out
    
RAM8 = Component(mkRAM8)


def mkRAM64(inputs, outputs):
    # TODO: need bit-slicing?
    pass

def mkRAM512(inputs, outputs):
    pass

def mkRAM4K(inputs, outputs):
    pass

def mkRAM16K(inputs, outputs):
    pass

def mkPC(inputs, outputs):
    pass