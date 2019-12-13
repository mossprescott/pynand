from nand import Component, lazy
from project_01 import *
from project_02 import *
from project_03 import *

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
    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).
    
    i, _, _, a, c5, c4, c3, c2, c1, c0, da, dd, dm, j2, j1, j0 = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out
    
    alu = lazy()
    a_reg = Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out, load=Or(a=not_i, b=da).out)
    d_reg = Register(in_=alu.out, load=And(a=i, b=dd).out)
    pc = PC(in_=Const(0), load=Const(0), inc=Const(1), reset=reset)
    alu.set(ALU(x=d_reg.out, y=a_reg.out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))
    

    outputs.outM = alu.out                   # M value output
    outputs.writeM = And(a=dm, b=i).out      # Write to M?
    outputs.addressM = a_reg.out             # Address in data memory (of M) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)
    

CPU = Component(mkCPU)
    
def mkComputer(inputs, outputs):
    pass

