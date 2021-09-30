#! /usr/bin/env pytest

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
def parameterize_simulators(f):
    def vector(chip, **args):
        return run(chip, simulator="vector", **args)
    def codegen(chip, **args):
        return run(chip, simulator="codegen", **args)
    return pytest.mark.parametrize("run", [vector, codegen])(f)
    # TODO: cython is hanging at the moment
    # def compiled(chip, **args):
    #     return run(chip, simulator="compiled", **args)
    # return pytest.mark.parametrize("run", [vector, codegen, compiled])(f)

def parameterize_simulators_by_name(f):
    return pytest.mark.parametrize("simulator", ["vector", "codegen"])(f)
    # TODO: cython is hanging at the moment
    # return pytest.mark.parametrize("simulator", ["vector", "codegen", "compiled"])(f)


@parameterize_simulators
def test_not8(run):
    assert unsigned(run(Not8, in_=0b0000_0000).out) == 0b1111_1111
    assert unsigned(run(Not8, in_=0b1111_1111).out) == 0b0000_0000
    assert unsigned(run(Not8, in_=0b1010_1010).out) == 0b0101_0101
    assert unsigned(run(Not8, in_=0b1100_0011).out) == 0b0011_1100
    assert unsigned(run(Not8, in_=0b0011_0100).out) == 0b1100_1011

@parameterize_simulators
def test_and8(run):
    assert unsigned(run(And8, a=0b0000_0000, b=0b0000_0000).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b0000_0000, b=0b1111_1111).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b1111_1111, b=0b1111_1111).out) == 0b1111_1111
    assert unsigned(run(And8, a=0b1010_1010, b=0b0101_0101).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b1100_0011, b=0b1111_0000).out) == 0b1100_0000
    assert unsigned(run(And8, a=0b0011_0100, b=0b0111_0110).out) == 0b0011_0100

@parameterize_simulators
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

@parameterize_simulators
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

@parameterize_simulators
def test_add8(run):
    assert run(Add8, a=  0, b=  0, carry_in=0).out ==   0
    assert run(Add8, a=255, b=255, carry_in=0).out == 254
    assert run(Add8, a=  0, b=  0, carry_in=1).out ==   1
    assert run(Add8, a=255, b=255, carry_in=1).out == 255

    assert run(Add8, a=  0, b=  0, carry_in=0).carry_out == False
    assert run(Add8, a=255, b=255, carry_in=0).carry_out == True
    assert run(Add8, a=  0, b=  0, carry_in=1).carry_out == False
    assert run(Add8, a=255, b=255, carry_in=1).carry_out == True

@parameterize_simulators
def test_zero8(run):
    assert run(Zero8, in_=0).out == True

    z = run(Zero8)
    for i in range(1, 256):
        z.in_ = i
        assert z.out == False


@parameterize_simulators
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


@parameterize_simulators
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

@parameterize_simulators
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

@parameterize_simulators
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

    # Tricky: jump target shows up in the bottom half and has to overwrite both halves of the PC
    top()
    pc.in_ = 12345; pc.load = 1
    bottom()
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
        'nands': 266,  # Compare to 287. Not much savings here.
        'dffs': 24,    # This is actually 8 _more_.
    }


#
# First test that the new CPU executes all Hack instructions as expected:
#

@parameterize_simulators
def test_backward_compatible_cpu(run):
    """This is test_05.test_cpu, but accounting for signals showing up in the bottom half-cycle,
    but the PC being updated after.
    """

    cpu = run(EightCPU)
    cycles_per_instr = 2

    cpu.instruction = 0b0011000000111001  # @12345
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 12345 and cpu.pc == 1 # and DRegister == 0

    cpu.instruction = 0b1110110000010000  # D=A
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 12345 and cpu.pc == 2 # and DRegister == 12345

    cpu.instruction = 0b0101101110100000  # @23456
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 23456 and cpu.pc == 3 # and DRegister == 12345

    cpu.instruction = 0b1110000111010000  # D=A-D
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 23456 and cpu.pc == 4 # and DRegister == 11111

    cpu.instruction = 0b0000001111101000  # @1000
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 5 # and DRegister == 11111

    cpu.instruction = 0b1110001100001000  # M=D
    cpu.ticktock()
    assert cpu.outM == 11111 and cpu.writeM == 1 and cpu.addressM == 1000  # and DRegister == 11111
    cpu.ticktock()
    assert cpu.writeM == 0 and cpu.pc == 6 # and DRegister == 11111

    cpu.instruction = 0b0000001111101001  # @1001
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1001 and cpu.pc == 7 # and DRegister == 11111

    # Note confusing timing here: outM has the value to be written to memory when the clock falls. Afterward,
    # outM has a nonsense value.
    # TODO: always assert outM and writeM before tick/tock?
    cpu.instruction = 0b1110001110011000  # MD=D-1
    cpu.ticktock()
    assert cpu.outM == 11110 and cpu.writeM == 1 and cpu.addressM == 1001 # and DRegister == 11111
    cpu.ticktock()
    assert cpu.pc == 8 # and DRegister == 11110

    cpu.instruction = 0b0000001111101000  # @1000
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 9 # and DRegister == 11110

    cpu.instruction = 0b1111010011010000  # D=D-M
    cpu.inM = 11111
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 10 # and DRegister == -1

    cpu.instruction = 0b0000000000001110  # @14
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 14 and cpu.pc == 11 # and DRegister == -1

    cpu.instruction = 0b1110001100000100  # D;jlt
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 14 and cpu.pc == 14 # and DRegister == -1

    cpu.instruction = 0b0000001111100111  # @999
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 999 and cpu.pc == 15 # and DRegister == -1

    cpu.instruction = 0b1110110111100000  # A=A+1
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 16 # and DRegister == -1

    cpu.instruction = 0b1110001100001000  # M=D
    cpu.ticktock()
    assert cpu.outM == -1 and cpu.writeM == 1 and cpu.addressM == 1000 # and DRegister == -1
    cpu.ticktock()
    assert cpu.pc == 17 # and DRegister == -1

    cpu.instruction = 0b0000000000010101  # @21
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 21 and cpu.pc == 18 # and DRegister == -1

    cpu.instruction = 0b1110011111000010  # D+1;jeq
    cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 21 # and DRegister == -1
    cpu.ticktock()
    assert cpu.pc == 21 # and DRegister == -1

    cpu.instruction = 0b0000000000000010  # @2
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 2 and cpu.pc == 22 # and DRegister == -1

    cpu.instruction = 0b1110000010010000  # D=D+A
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 2 and cpu.pc == 23 # and DRegister == 1

    cpu.instruction = 0b0000001111101000  # @1000
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 24 # and DRegister == -1

    cpu.instruction = 0b1110111010010000  # D=-1
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 25 # and DRegister == -1

    cpu.instruction = 0b1110001100000001  # D;JGT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 26 # and DRegister == -1

    cpu.instruction = 0b1110001100000010  # D;JEQ
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 27 # and DRegister == -1

    cpu.instruction = 0b1110001100000011  # D;JGE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 28 # and DRegister == -1

    cpu.instruction = 0b1110001100000100  # D;JLT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110001100000101  # D;JNE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110001100000110  # D;JLE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110001100000111  # D;JMP
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110101010010000  # D=0
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 0

    cpu.instruction = 0b1110001100000001  # D;JGT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1002 # and DRegister == 0

    cpu.instruction = 0b1110001100000010  # D;JEQ
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110001100000011  # D;JGE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110001100000100  # D;JLT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 0

    cpu.instruction = 0b1110001100000101  # D;JNE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1002 # and DRegister == 0

    cpu.instruction = 0b1110001100000110  # D;JLE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110001100000111  # D;JMP
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110111111010000  # D=1
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000001  # D;JGT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.instruction = 0b1110001100000010  # D;JEQ
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000011  # D;JGE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.instruction = 0b1110001100000100  # D;JLT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000101  # D;JNE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.instruction = 0b1110001100000110  # D;JLE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000111  # D;JMP
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1


    # Negative value with "positive" low byte:
    cpu.instruction = solved_06.parse_op("@32767")
    for _ in range(cycles_per_instr): cpu.ticktock()  # pc = 1001
    cpu.instruction = solved_06.parse_op("D=A+1")
    for _ in range(cycles_per_instr): cpu.ticktock()  # pc = 1002
    cpu.instruction = solved_06.parse_op("@1000")
    for _ in range(cycles_per_instr): cpu.ticktock()  # pc = 1003

    cpu.instruction = 0b1110001100000001  # D;JGT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1004 # and DRegister == -32768

    cpu.instruction = 0b1110001100000010  # D;JEQ
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1005 # and DRegister == -32768

    cpu.instruction = 0b1110001100000011  # D;JGE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1006 # and DRegister == -32768

    cpu.instruction = 0b1110001100000100  # D;JLT
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -32768

    cpu.instruction = 0b1110001100000101  # D;JNE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -32768

    cpu.instruction = 0b1110001100000110  # D;JLE
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -32768

    cpu.instruction = 0b1110001100000111  # D;JMP
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -32768

    # Reset is effective in a single clock:
    cpu.reset = 1
    cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 0 # and DRegister == 1

    cpu.instruction = 0b0111111111111111  # @32767
    cpu.reset = 0
    for _ in range(cycles_per_instr): cpu.ticktock()
    assert cpu.writeM == 0 and cpu.addressM == 32767 and cpu.pc == 1 # and DRegister == 1


@parameterize_simulators_by_name
def test_backward_compatible_computer_add(simulator):
    test_05.test_computer_add(EightComputer, simulator=simulator)

@parameterize_simulators_by_name
def test_backward_compatible_computer_max(simulator):
    test_05.test_computer_max(EightComputer, simulator=simulator, cycles_per_instr=2)

@parameterize_simulators_by_name
def test_backward_compatible_keyboard(simulator):
    test_05.test_computer_keyboard(EightComputer, simulator=simulator, cycles_per_instr=2)

@parameterize_simulators_by_name
def test_backward_compatible_tty(simulator):
    test_05.test_computer_tty(EightComputer, simulator=simulator, cycles_per_instr=2)

def test_backward_compatible_speed():
    """Note: alyways compared using the (slower, fairer) "vector" simulator."""
    test_05.test_speed(EightComputer, cycles_per_instr=2)



def test_computer_gates():
   assert gate_count(EightComputer) == {
       'nands': 1032,  # ??? compare to 1262
       'dffs': 67,  # 3*16 bits (as in the standard CPU), plus two more half-words to hold results between half-cycles, plus a handful more to track some odd bits
       'roms': 1,
       'rams': 2,
       'inputs': 1,
       'outputs': 1,
   }


#
# VM translator:
#

def test_vm_simple_add():
    test_07.test_simple_add(chip=EightComputer, simulator='vector')

def test_vm_stack_ops():
    test_07.test_stack_ops(chip=EightComputer, simulator='vector')

def test_vm_memory_access_basic():
    test_07.test_memory_access_basic(chip=EightComputer, simulator='vector')

def test_vm_memory_access_pointer():
    test_07.test_memory_access_pointer(chip=EightComputer, simulator='vector')

def test_vm_memory_access_static():
    test_07.test_memory_access_static(chip=EightComputer, simulator='vector')


def test_vm_basic_loop():
    test_08.test_basic_loop(chip=EightComputer, simulator='vector')

def test_vm_fibonacci_series():
    test_08.test_fibonacci_series(chip=EightComputer, simulator='vector')

def test_vm_simple_function():
    test_08.test_simple_function(chip=EightComputer, simulator='vector')

def test_vm_nested_call():
    test_08.test_nested_call(chip=EightComputer, simulator='vector')

def test_vm_fibonacci_element():
    test_08.test_fibonacci_element(chip=EightComputer, simulator='vector')

def test_vm_statics_multiple_files():
    test_08.test_statics_multiple_files(chip=EightComputer, simulator='vector')


#
# Performance. TL;DR, it's worse.
#

def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(platform=EIGHT_PLATFORM)

    assert cycles < 85_000


def test_vm_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(platform=EIGHT_PLATFORM)

    assert cycles < 260_000
