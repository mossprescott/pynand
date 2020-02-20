import pytest

from nand import run, gate_count #, unsigned
import test_02
import test_05
import test_07
import test_08
import test_optimal_08

from alt.eight import *


#
# Components:
#

# TODO: put this somewhere common:
def parametrize_simulators(f):
    def vector(chip, **args):
        return run(chip, simulator="vector", **args)
    def codegen(chip, **args):
        return run(chip, simulator="codegen", **args)
    return pytest.mark.parametrize("run", [vector, codegen])(f)


@parametrize_simulators
def test_not8(run):
    assert unsigned(run(Not8, in_=0b0000_0000).out) == 0b1111_1111
    assert unsigned(run(Not8, in_=0b1111_1111).out) == 0b0000_0000
    assert unsigned(run(Not8, in_=0b1010_1010).out) == 0b0101_0101
    assert unsigned(run(Not8, in_=0b1100_0011).out) == 0b0011_1100
    assert unsigned(run(Not8, in_=0b0011_0100).out) == 0b1100_1011

@parametrize_simulators
def test_and8(run):
    assert unsigned(run(And8, a=0b0000_0000, b=0b0000_0000).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b0000_0000, b=0b1111_1111).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b1111_1111, b=0b1111_1111).out) == 0b1111_1111
    assert unsigned(run(And8, a=0b1010_1010, b=0b0101_0101).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b1100_0011, b=0b1111_0000).out) == 0b1100_0000
    assert unsigned(run(And8, a=0b0011_0100, b=0b0111_0110).out) == 0b0011_0100

@parametrize_simulators
def test_mux8(run):
    assert unsigned(run(Mux8, a=0b0000_0000, b=0b0000_0000, sel=0).out) == 0b0000_0000
    assert unsigned(run(Mux8, a=0b0000_0000, b=0b0000_0000, sel=1).out) == 0b0000_0000
    assert unsigned(run(Mux8, a=0b0000_0000, b=0b0011_0100, sel=0).out) == 0b0000_0000
    assert unsigned(run(Mux8, a=0b0000_0000, b=0b0011_0100, sel=1).out) == 0b0011_0100
    assert unsigned(run(Mux8, a=0b0111_0110, b=0b0000_0000, sel=0).out) == 0b0111_0110
    assert unsigned(run(Mux8, a=0b0111_0110, b=0b0000_0000, sel=1).out) == 0b0000_0000
    assert unsigned(run(Mux8, a=0b1010_1010, b=0b0101_0101, sel=0).out) == 0b1010_1010
    assert unsigned(run(Mux8, a=0b1010_1010, b=0b0101_0101, sel=1).out) == 0b0101_0101

def test_gates_not8():
    assert gate_count(Not8)['nands'] == 8

def test_gates_and8():
    assert gate_count(And8)['nands'] == 16

def test_gates_mux8():
    assert gate_count(Mux8)['nands'] == 25  # optimal?



# Project 02:

@parametrize_simulators
def test_inc8(run):
    assert run(Inc8, in_=  0, carry_in=0).out == 0
    assert run(Inc8, in_=  5, carry_in=0).out == 5
    assert run(Inc8, in_=255, carry_in=0).out == 255
    assert run(Inc8, in_=  0, carry_in=1).out == 1
    assert run(Inc8, in_=  5, carry_in=1).out == 6
    assert run(Inc8, in_=255, carry_in=1).out == 0

    # TODO: what to do with negatives? Probably need to treat these value as unsigned until they're 
    # re-assembled into 16-bits.
    # assert run(Inc8, in_=-1).out ==  0
    # assert run(Inc8, in_=-5).out == -4
    
    assert run(Inc8, in_=  0, carry_in=0).carry_out == 0
    assert run(Inc8, in_=255, carry_in=0).carry_out == 0
    assert run(Inc8, in_=  0, carry_in=1).carry_out == 0
    assert run(Inc8, in_=255, carry_in=1).carry_out == 1
    
@parametrize_simulators
def test_add8(run):
    assert run(Add8, a=  0, b=  0, carry_in=0).out ==   0
    assert run(Add8, a=255, b=255, carry_in=0).out == 254
    assert run(Add8, a=  0, b=  0, carry_in=1).out ==   1
    assert run(Add8, a=255, b=255, carry_in=1).out == 255

    assert run(Add8, a=  0, b=  0, carry_in=0).carry_out == False
    assert run(Add8, a=255, b=255, carry_in=0).carry_out == True
    assert run(Add8, a=  0, b=  0, carry_in=1).carry_out == False
    assert run(Add8, a=255, b=255, carry_in=1).carry_out == True

@parametrize_simulators
def test_zero8(run):
    assert run(Zero8, in_=0).out == True
    
    z = run(Zero8)
    for i in range(1, 256):
        z.in_ = i
        assert z.out == False


@parametrize_simulators
def test_alu_nostat(run):
    alu = run(EightALU)
    
    alu.x = 0
    alu.y = -1 
    
    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 0   # 0
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 1   # 1
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 255  # -1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0; assert alu.out == 0   # X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == 255  # Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1; assert alu.out == 255  # !X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1; assert alu.out == 0   # !Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 0   # -X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 1   # -Y
    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 1   # X + 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 0   # Y + 1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0; assert alu.out == 255  # X - 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 254  # Y - 1
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 255  # X + Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 1   # X - Y
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 255  # Y - X
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == 0   # X & Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1; assert alu.out == 255  # X | Y


    alu.x = 23  # 0x17
    alu.y = 45  # 0x2D
    
    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 0      # 0
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 1      # 1
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 255     # -1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0; assert alu.out == 23  # X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == 45   # Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1; assert alu.out == 0xE8 # !X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1; assert alu.out == 0xD2 # !Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 256-23 # -X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 256-45  # -Y
    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 24  # X + 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 46   # Y + 1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0; assert alu.out == 22  # X - 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 44   # Y - 1
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 68  # X + Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 256-22  # X - Y
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 22 # Y - X
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == 0x05 # X & Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1; assert alu.out == 0x3F # X | Y


@parametrize_simulators
def test_alu(run):
    alu = run(EightALU)

    alu.x = 0
    alu.y = 255

    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # 0
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # -1
    assert alu.out == 255 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0  # X
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # Y
    assert alu.out == 255 and alu.carry_out == 1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1  # !X
    assert alu.out == 255 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1  # !Y
    assert alu.out == 0 and alu.carry_out == 1 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # -X
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # -Y
    assert alu.out == 1 and alu.carry_out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # X + 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y + 1
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0  # X - 1
    assert alu.out == 255 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # Y - 1
    assert alu.out == 254 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # X + Y
    assert alu.out == 255 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # X - Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y - X
    assert alu.out == 255 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # X & Y
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1  # X | Y
    assert alu.out == 255 and alu.zr == 0 and alu.ng == 1


    alu.x = 17
    alu.y = 3 

    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # 0
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # -1
    assert alu.out == 256-1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0  # X
    assert alu.out == 17 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # Y
    assert alu.out == 3 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1  # !X
    assert alu.out == 256-18 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1  # !Y
    assert alu.out == 256-4 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # -X
    assert alu.out == 256-17 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # -Y
    assert alu.out == 256-3 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # X + 1
    assert alu.out == 18 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y + 1
    assert alu.out == 4 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0  # X - 1
    assert alu.out == 16 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # Y - 1
    assert alu.out == 2 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # X + Y
    assert alu.out == 20 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # X - Y
    assert alu.out == 14 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y - X
    assert alu.out == 256-14 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # X & Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1  # X | Y
    assert alu.out == 19 and alu.zr == 0 and alu.ng == 0

def test_alu_chained():
    """Test sequential application of the 8-bit ALU by connecting two separate ALUs, with the 
    carry bit wired between them.
    """
    def mkChainedALU(inputs, outputs):
        x_split = Split(in_=inputs.x)
        y_split = Split(in_=inputs.y)
        alu_lo = EightALU(x=x_split.lo, y=y_split.lo, 
                    zx=inputs.zx, nx=inputs.nx, zy=inputs.zy, ny=inputs.ny, f=inputs.f, no=inputs.no,
                    carry_in=0)
        alu_hi = EightALU(x=x_split.hi, y=y_split.hi, 
                    zx=inputs.zx, nx=inputs.nx, zy=inputs.zy, ny=inputs.ny, f=inputs.f, no=inputs.no,
                    carry_in=alu_lo.carry_out)
        outputs.out = Splice(lo=alu_lo.out, hi=alu_hi.out).out
        outputs.zr = And(a=alu_lo.zr, b=alu_hi.zr).out
        outputs.ng = alu_hi.ng
    ChainedALU = build(mkChainedALU)

    test_02.test_alu(ChainedALU)


def test_gates_inc8():
    assert gate_count(Inc8)['nands'] == 40  # gate_count(Inc16)/2 + 2

def test_gates_add8():
    assert gate_count(Add8)['nands'] == 72  # gate_count(Add16)/2 + 2

def test_gates_zero8():
    assert gate_count(Zero8)['nands'] == 22  # gate_count(Zero16)/2 - 1

def test_gates_alu():
    assert gate_count(EightALU)['nands'] == 284  # gate_count(ALU)/2 + 4
    

# Project 03:

@parametrize_simulators
def test_register8(run):
    reg = run(Register8)

    reg.in_ = 0
    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.load = 1
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.in_ = 123
    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.in_ = 111
    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.in_ = 123
    reg.load = 1
    reg.tick(); reg.tock()
    assert reg.out == 123

    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 123

    reg.in_ = -1
    reg.tick(); reg.tock()
    assert reg.out == 123

@parametrize_simulators
def test_pc8(run):
    pc = run(PC8)

    def top():
        pc.top_half = True
        pc.bottom_half = False
        pc.ticktock()
    def bottom():
        pc.top_half = False
        pc.bottom_half = True
        pc.ticktock()

    pc.in_ = 0; pc.reset = 0; pc.load = 0
    top()
    assert pc.out == 0  # No change on the first half-cycle
    bottom()
    assert pc.out == 1  # Now we go forward one word

    pc.in_ = -32123
    top(); bottom()
    assert pc.out == 2

    pc.load = 1
    top(); bottom()
    assert pc.out == -32123

    pc.load = 0
    top(); bottom()
    assert pc.out == -32122

    top(); bottom()
    assert pc.out == -32121

    pc.in_ = 12345; pc.load = 1
    top(); bottom()
    assert pc.out == 12345

    pc.reset = 1
    top(); bottom()
    assert pc.out == 0  # reset overrides load/in_

    pc.reset = 0
    top(); bottom()
    assert pc.out == 12345  # load/in_ still set from before

    pc.reset = 1
    top(); bottom()
    assert pc.out == 0

    pc.reset = 0; pc.load = 0
    top(); bottom()
    assert pc.out == 1

    pc.reset = 1
    top(); bottom()
    assert pc.out == 0

    pc.in_ = 0; pc.reset = 0; pc.load = 1
    top(); bottom()
    assert pc.out == 0

    pc.load = 0
    top(); bottom()
    assert pc.out == 1

    pc.in_ = 22222; pc.reset = 1
    top()   # Note: reset is effective immediately, without waiting for bottom_half
    assert pc.out == 0


def test_gates_register8():
    assert gate_count(Register8) == {
        'nands': 32,  # ?
        'dffs': 8
    }

def test_gates_pc8():
    assert gate_count(PC8) == {
        'nands': 270,  # Compare to 287. Not much savings here.
        'dffs': 24,    # This is actually 8 _more_.
    }


#
# First test that the new CPU executes all Hack instructions as expected:
#

def test_backward_compatible_cpu():
    test_05.test_cpu(EightCPU)

def test_backward_compatible_computer_add():
    test_05.test_computer_add(EightComputer)
    
def test_backward_compatible_computer_max():
    test_05.test_computer_max(EightComputer, cycles_per_instr=2)
    
def test_backward_compatible_speed():
    test_05.test_speed(EightComputer)



def test_computer_gates():
   assert gate_count(EightComputer) == {
       'nands': 1070,  # ??? compare to 1262
       'dffs': 67,  # 3*16 bits (as in the standard CPU), plus two more half-words to hold results between half-cycle, plus a handful more to track some odd bits
       'roms': 1,
       'rams': 2,
       'inputs': 1,
   }



#
# Performance. TL;DR, it's worse.
#

@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(EightComputer, solved_06.assemble, Translator)

    assert cycles < 70_000


@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_vm_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(solved_05.Computer, solved_06.assemble, Translator)

    # compare to the project_08 solution (about 4m)
    assert cycles < 8_000_000
