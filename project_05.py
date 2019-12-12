from nand import Component
from project_01 import *
from project_02 import *

def mkMemorySystem(inputs, outputs):
    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    def mkShift13(inputs, outputs):
        outputs.out[0] = inputs.in_[13]
        outputs.out[1] = inputs.in_[14]
    Shift13 = Component(mkShift13)

    def mkMask14(inputs, outputs):
        for i in range(14):
            outputs.out[i] = inputs.in_[i]
    Mask14 = Component(mkMask14)
    
    bank = Shift13(in_=address).out
    load_bank = DMux4Way(in_=load, sel=bank)
    address14 = Mask14(in_=address).out

    # addresses 0x0000 to 0x3FFF
    ram = Memory(14, in_=in_, load=Or(a=load_bank.a, b=load_bank.b).out, address=address14)
    
    # addresses 0x4000 to 0x5FFFF
    # TODO: connect to pygame display
    # note: bit 13 is definitely zero, so address[0..13] == address[0..12]
    screen = Memory(13, in_=in_, load=load_bank.c, address=address14)
    
    # address 0x6000
    # TODO: keyboard = Keyboard()
    keyboard = Const(0)

    outputs.out = Mux4Way16(a=ram.out, b=ram.out, c=screen.out, d=keyboard, sel=bank).out
    
MemorySystem = Component(mkMemorySystem)

    
def mkCPU(inputs, outputs):
    pass

    
def mkComputer(inputs, outputs):
    pass

