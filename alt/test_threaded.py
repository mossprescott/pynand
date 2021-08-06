#! /usr/bin/env pytest

import pytest

from nand import run, unsigned
from nand.translate import translate_dir
import test_05
import test_06
import test_07
import test_08
import test_optimal_08

from alt.threaded import *

#
# First test that the new CPU executes all Hack instructions as expected:
#

def test_backward_compatible_cpu():
    test_05.test_cpu(ThreadedCPU)

def test_backward_compatible_computer_add():
    test_05.test_computer_add(ThreadedComputer)
    
def test_backward_compatible_computer_max():
    test_05.test_computer_max(ThreadedComputer)

def test_backward_compatible_keyboard():
    test_05.test_computer_keyboard(ThreadedComputer)

def test_backward_compatible_tty():
    test_05.test_computer_tty(ThreadedComputer)

def test_backward_compatible_speed():
    test_05.test_speed(ThreadedComputer)


#
# Components:
#
@pytest.mark.parametrize("simulator", ["vector", "codegen"])
def test_eq16(simulator):
    assert run(Eq16, a=1, b=0, simulator=simulator).out == False
    assert run(Eq16, a=0, b=0, simulator=simulator).out == True
    assert run(Eq16, a=12345, b=12345, simulator=simulator).out == True
    assert run(Eq16, a=-23456, b=-23456, simulator=simulator).out == True
    assert run(Eq16, a=-32768, b=-32768, simulator=simulator).out == True
    for i in range(16):
        assert run(Eq16, a=(1 << i), b=(1 << i), simulator=simulator).out == True
        assert run(Eq16, a=(1 << i), b=       0, simulator=simulator).out == False
        assert run(Eq16, a=       0, b=(1 << i), simulator=simulator).out == False

def test_eq16_gates():
    # Ouch. Probably could do it with less if was smarter.
    assert gate_count(Eq16) == {'nands': 110}


#
# Now some tests of added stuff:
#

@pytest.mark.parametrize("simulator", ["vector", "codegen"])
def test_call_and_return(simulator):
    """CPU jumps and returns using two new instructions and a new register."""

    symbols = {"target": 12345}

    cpu = run(ThreadedCPU, simulator=simulator)

    # init PC to 1000
    cpu.instruction = parse_op("@1000")
    cpu.ticktock()
    cpu.instruction = parse_op("0;JMP")
    cpu.ticktock()

    cpu.instruction = parse_op("CALL target", symbols)
    cpu.ticktock()
    
    assert cpu.pc == 12345

    cpu.instruction = parse_op("RTN")
    cpu.ticktock()
    assert cpu.pc == 1001    


def test_computer_gates():
   assert gate_count(ThreadedComputer) == {
       'nands': 1549,  # ??? compare to 1262
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
# Test new instructions:
#

def test_assemble_call():
    symbols = {"target": 12345}
    assert unsigned(parse_op("CALL target", symbols))  == 0b1000_0000_0000_0000 | 12345
    
    # with pytest.raises(SyntaxError) as exc_info:
    #     parse_op("CALL ")
    # assert str(exc_info.value).startswith("M not allowed as a destination for pop")

def test_assemble_return():
    assert unsigned(parse_op("RTN"))  == 0b1000_0000_0000_0000


#
# VM translator:
#

def test_vm_simple_add():
    test_07.test_simple_add(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_stack_ops():
    test_07.test_stack_ops(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_memory_access_basic():
    test_07.test_memory_access_basic(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_memory_access_pointer():
    test_07.test_memory_access_pointer(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_memory_access_static():
    test_07.test_memory_access_static(chip=ThreadedComputer, assemble=assemble, translator=Translator)


def test_vm_basic_loop():
    test_08.test_basic_loop(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_fibonacci_series():
    test_08.test_fibonacci_series(chip=ThreadedComputer, assemble=assemble, translator=Translator)
    
def test_vm_simple_function():
    test_08.test_simple_function(chip=ThreadedComputer, assemble=assemble, translator=Translator)
    
def test_vm_nested_call():
    test_08.test_nested_call(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_fibonacci_element():
    test_08.test_fibonacci_element(chip=ThreadedComputer, assemble=assemble, translator=Translator)

def test_vm_statics_multiple_files():
    test_08.test_statics_multiple_files(chip=ThreadedComputer, assemble=assemble, translator=Translator)


@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_vm_pong_instructions():
    instruction_count = test_optimal_08.count_pong_instructions(Translator)

    # compare to the project_08 solution (about 28k)
    assert instruction_count < -1  # ~8_700


@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(ThreadedComputer, assemble, Translator)

    assert cycles < 1  #?


@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_vm_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(ThreadedComputer, assemble, Translator)

    # compare to the project_08 solution (about 4m)
    assert cycles < -1  # ~5.1m
