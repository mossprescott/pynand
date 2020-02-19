import pytest

from nand import run, gate_count #, unsigned
import test_05
import test_07
import test_08
import test_optimal_08

from alt.eight import *


#
# Components:
#


def test_not8():
    assert unsigned(run(Not8, in_=0b0000_0000).out) == 0b1111_1111
    assert unsigned(run(Not8, in_=0b1111_1111).out) == 0b0000_0000
    assert unsigned(run(Not8, in_=0b1010_1010).out) == 0b0101_0101
    assert unsigned(run(Not8, in_=0b1100_0011).out) == 0b0011_1100
    assert unsigned(run(Not8, in_=0b0011_0100).out) == 0b1100_1011

def test_and8():
    assert unsigned(run(And8, a=0b0000_0000, b=0b0000_0000).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b0000_0000, b=0b1111_1111).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b1111_1111, b=0b1111_1111).out) == 0b1111_1111
    assert unsigned(run(And8, a=0b1010_1010, b=0b0101_0101).out) == 0b0000_0000
    assert unsigned(run(And8, a=0b1100_0011, b=0b1111_0000).out) == 0b1100_0000
    assert unsigned(run(And8, a=0b0011_0100, b=0b0111_0110).out) == 0b0011_0100

def test_mux8():
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

@pytest.mark.parametrize("simulator", ["vector", "codegen"])
def test_inc8(simulator):
    assert run(Inc8, in_=  0, carry_in=0, simulator=simulator).out == 0
    assert run(Inc8, in_=  5, carry_in=0, simulator=simulator).out == 5
    assert run(Inc8, in_=255, carry_in=0, simulator=simulator).out == 255
    assert run(Inc8, in_=  0, carry_in=1, simulator=simulator).out == 1
    assert run(Inc8, in_=  5, carry_in=1, simulator=simulator).out == 6
    assert run(Inc8, in_=255, carry_in=1, simulator=simulator).out == 0

    # TODO: what to do with negatives? Probably need to treat these value as unsigned until they're 
    # re-assembled into 16-bits.
    # assert run(Inc8, in_=-1, simulator=simulator).out ==  0
    # assert run(Inc8, in_=-5, simulator=simulator).out == -4
    
    assert run(Inc8, in_=  0, carry_in=0, simulator=simulator).carry_out == 0
    assert run(Inc8, in_=255, carry_in=0, simulator=simulator).carry_out == 0
    assert run(Inc8, in_=  0, carry_in=1, simulator=simulator).carry_out == 0
    assert run(Inc8, in_=255, carry_in=1, simulator=simulator).carry_out == 1
    
@pytest.mark.parametrize("simulator", ["vector", "codegen"])
def test_add8(simulator):
    assert run(Add8, a=  0, b=  0, carry_in=0, simulator=simulator).out ==   0
    assert run(Add8, a=255, b=255, carry_in=0, simulator=simulator).out == 254
    assert run(Add8, a=  0, b=  0, carry_in=1, simulator=simulator).out ==   1
    assert run(Add8, a=255, b=255, carry_in=1, simulator=simulator).out == 255
    
    assert run(Add8, a=  0, b=  0, carry_in=0, simulator=simulator).carry_out == False
    assert run(Add8, a=255, b=255, carry_in=0, simulator=simulator).carry_out == True
    assert run(Add8, a=  0, b=  0, carry_in=1, simulator=simulator).carry_out == False
    assert run(Add8, a=255, b=255, carry_in=1, simulator=simulator).carry_out == True

@pytest.mark.parametrize("simulator", ["vector", "codegen"])
def test_zero8(simulator):
    assert run(Zero8, in_=0, simulator=simulator).out == True
    
    z = run(Zero8, simulator=simulator)
    for i in range(1, 256):
        z.in_ = i
        assert z.out == False


def test_alu_nostat():
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


# TODO: Need to sort out what happens with negatives here
def test_alu():
    alu = run(EightALU)

    alu.x = 0
    alu.y = -1 

    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # 0
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # -1
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0  # X
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # Y
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1  # !X
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1  # !Y
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # -X
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # -Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # X + 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y + 1
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0  # X - 1
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # Y - 1
    assert alu.out == -2 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # X + Y
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # X - Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y - X
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # X & Y
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1  # X | Y
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1


    alu.x = 17
    alu.y = 3 

    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # 0
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # -1
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0  # X
    assert alu.out == 17 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # Y
    assert alu.out == 3 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1  # !X
    assert alu.out == -18 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1  # !Y
    assert alu.out == -4 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # -X
    assert alu.out == -17 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # -Y
    assert alu.out == -3 and alu.zr == 0 and alu.ng == 1

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
    assert alu.out == -14 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # X & Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1  # X | Y
    assert alu.out == 19 and alu.zr == 0 and alu.ng == 0


def test_gates_inc8():
    assert gate_count(Inc8)['nands'] == 40  # gate_count(Inc16)/2 + 2

def test_gates_add8():
    assert gate_count(Add8)['nands'] == 72  # gate_count(Add16)/2 + 2

def test_gates_zero8():
    assert gate_count(Zero8)['nands'] == 22  # gate_count(Zero16)/2 - 1

def test_gates_alu():
    assert gate_count(EightALU)['nands'] == 286  # gate_count(ALU)/2 + 6
    

# Project 03:


#
# First test that the new CPU executes all Hack instructions as expected:
#

def test_backward_compatible_cpu():
    test_05.test_cpu(EightCPU)

def test_backward_compatible_computer_add():
    test_05.test_computer_add(EightComputer)
    
def test_backward_compatible_computer_max():
    test_05.test_computer_max(EightComputer)
    
def test_backward_compatible_speed():
    test_05.test_speed(EightComputer)



def test_computer_gates():
   assert gate_count(EightComputer) == {
       'nands': 1262,  # ??? compare to 1262
       'dffs': 64,  # 4 registers
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
