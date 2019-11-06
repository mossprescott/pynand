from nand import Component
from project_01 import *
from project_02 import *


def mkDFF(inputs, outputs):
    # Note: provided as a primitive in the Nand to Tetris simulator, but implementing it
    # from scratch is fun.

    def mkLatch(inputs, outputs):
        d = lazy()
        d.set(DMux(a=d.out, b=inputs.data, sel=inputs.store))
        outputs.out = d.out
    Latch = Component(mkLatch)
    
    # TODO: make `clock` magic, so you don't have to propagate it everywhere?
    inner = Latch(data=inputs.in_, store=And(a=inputs.store, b=Not(in_=inputs.clock).out).out).out
    outputs.out = Latch(data=inner.out, store=inputs.clock).out

DFF = Component(mkDFF)


def mkBit(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    outputs.out = ___

def mkRegister(inputs, outputs):
    pass

def mkRAM8(inputs, outputs):
    pass

def mkRAM64(inputs, outputs):
    pass

def mkRAM512(inputs, outputs):
    pass

def mkRAM4K(inputs, outputs):
    pass

def mkRAM16K(inputs, outputs):
    pass

def mkPC(inputs, outputs):
    pass