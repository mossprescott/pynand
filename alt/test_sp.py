from nand import run
from project_06 import parse_op
import test_05

from alt.sp import *

#
# First test that the new CPU executes all Hack inststructions as expected:
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
# Now some tests of added stuff
#

def test_write_sp():
    """Writing to address 0 using Hack instructions updates SP (and not the RAM)."""
    cpu = run(SPCPU)

    ASM = [
        "@256",
        "D=A",
        "@0",
        "M=D",
    ]
    for instr in ASM:
        cpu.instruction = parse_op(instr)
        cpu.ticktock()

    assert cpu.sp == 256
    assert cpu.peek(0) == 0


def test_read_sp():
    cpu = run(SPCPU)

    ASM = [
        # Initialize SP the same way:
        "@256",
        "D=A",
        "@0",
        "M=D",
        
        # Now read it into A and observe the value at addressM:
        "D=-1",
        "@0",
        "A=M",
    ]
    for instr in ASM:
        cpu.instruction = parse_op(instr)
        cpu.ticktock()

    assert cpu.addressM == 256


def test_computer_gates():
    assert gate_count(SPComputer) == {
        'nands': -1,  # ??? compare to 1262
        'dffs': 64,  # 4 registers
        'roms': 1,
        'rams': 2,
        'inputs': 1,
    }