import pytest

from nand import run, unsigned
import test_05
import test_06

from alt.sp import *

#
# First test that the new CPU executes all Hack instructions as expected:
#

def test_backward_compatible_cpu():
    test_05.test_cpu(SPCPU)

def test_backward_compatible_computer_add():
    test_05.test_computer_add(SPComputer)
    
def test_backward_compatible_computer_max():
    test_05.test_computer_max(SPComputer)
    
def test_backward_compatible_speed():
    test_05.test_speed(SPComputer)


#
# Components:
#
def test_dec16():
    assert run(Dec16, in_=1).out == 0
    assert run(Dec16, in_=0).out == -1
    assert run(Dec16, in_=12345).out == 12344
    assert run(Dec16, in_=-23456).out == -23457
    assert run(Dec16, in_=-32768).out == 32767
    
    assert gate_count(Dec16) == {'nands': 16+76+16}


#
# Now some tests of added stuff:
#

def test_write_sp():
    """Writing to address 0 using Hack instructions updates SP."""

    cpu = run(SPCPU)

    init_sp(cpu)

    assert cpu.writeM == False  # to avoid confusion, the RAM is not also written
    assert cpu.sp == 256


def test_read_sp():
    """The value of SP is used when reading from address 0."""

    cpu = run(SPCPU)

    init_sp(cpu)

    ASM = [
        # Now read the value back into A:
        "A=-1",
        "@0",
        "A=M",
    ]
    for instr in ASM:
        cpu.instruction = parse_op(instr)
        cpu.ticktock()

    cpu.inM = 12345  # Nonense value, not used
    cpu.instruction = parse_op("D=M")  # Put the value of A on the address lines
    assert cpu.addressM == 256


def test_computer_gates():
    assert gate_count(SPComputer) == {
        'nands': -1,  # ??? compare to 1262
        'dffs': 64,  # 4 registers
        'roms': 1,
        'rams': 2,
        'inputs': 1,
    }

   
#
# Test that all Hack instructions are assembled the same way:
#

def test_backward_compatible_asm_ops_add():
    test_06.test_asm_ops_add(parse_op)

def test_backward_compatible_asm_ops_max():
    test_06.test_asm_ops_max(parse_op)

def test_backward_compatible_ops():
    test_06.test_ops(parse_op)


#
# Test SP-modifying instructions:
#

def test_assemble_sp_ops():
    assert unsigned(parse_op("D=--SP"))  == 0b100_1_110000_010_000
    assert unsigned(parse_op("A=--SP"))  == 0b100_1_110000_100_000
    assert unsigned(parse_op("AD=--SP")) == 0b100_1_110000_110_000
    with pytest.raises(SyntaxError) as exc_info:
        parse_op("M=--SP")
    assert str(exc_info.value).startswith("M not allowed as a destination for pop")

    assert unsigned(parse_op("SP++=0")) == 0b100_0_101010_000_000
    assert unsigned(parse_op("SP++=D+1")) == 0b100_0_011111_000_000
    with pytest.raises(Exception) as exc_info:
        parse_op("SP++=M")
    assert str(exc_info.value).startswith("unrecognized alu op")


def test_push_constant():
    cpu = run(SPCPU)
    
    init_sp(cpu)
    
    cpu.instruction = parse_op("SP++=-1")
    assert cpu.outM == -1
    assert cpu.writeM == True
    assert cpu.addressM == 256
    
    cpu.ticktock()
    
    assert cpu.sp == 257

def test_pop_to_a():
    cpu = run(SPCPU)
    
    init_sp(cpu)
    
    cpu.instruction = parse_op("A=--SP")
    assert cpu.writeM == False
    assert cpu.addressM == 255
    cpu.inM = 12345
    
    cpu.ticktock()
    
    cpu.instruction = parse_op("D=M")  # Put A on the address lines
    assert cpu.sp == 255
    assert cpu.addressM == 12345


def init_sp(cpu):
    ASM = [
        "@256",
        "D=A",
        "@0",
        "M=D",
    ]
    for instr in ASM:
        cpu.instruction = parse_op(instr)
        cpu.ticktock()
