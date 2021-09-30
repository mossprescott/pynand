#! /usr/bin/env pytest

import pytest

from nand import run, unsigned
from nand.translate import translate_dir
import test_05
import test_06
import test_07
import test_08
import test_optimal_08

from alt.shift import *

#
# First test that the new CPU executes all Hack instructions as expected:
#

def test_backward_compatible_cpu():
    test_05.test_cpu(ShiftCPU)

def test_backward_compatible_computer_add():
    test_05.test_computer_add(ShiftComputer)

def test_backward_compatible_computer_max():
    test_05.test_computer_max(ShiftComputer)

def test_backward_compatible_keyboard():
    test_05.test_computer_keyboard(ShiftComputer)

def test_backward_compatible_tty():
    test_05.test_computer_tty(ShiftComputer)

def test_backward_compatible_speed():
    cps = test_05.cycles_per_second(ShiftComputer)
    print(f"Measured speed: {cps:0,.1f} cycles/s")
    assert cps > 1_000


#
# Components:
#
def test_shiftR16():
    assert run(ShiftR16, in_=0).out == 0
    assert run(ShiftR16, in_=1).out == 0
    assert run(ShiftR16, in_=2).out == 1
    assert run(ShiftR16, in_=3).out == 1  # truncates as expected
    assert run(ShiftR16, in_=12345).out == 6172
    assert run(ShiftR16, in_=-23456).out == -11728
    assert run(ShiftR16, in_=-4).out == -2
    assert run(ShiftR16, in_=-2).out == -1

    # These two might be unexpected, but this is what you get: floor instead of truncate.
    assert run(ShiftR16, in_=-3).out == -2
    assert run(ShiftR16, in_=-1).out == -1

    assert gate_count(ShiftR16) == {}  # No gates: this is just wiring.


#
# Now some tests of added stuff:
#

def test_shift_instr():
    cpu = run(ShiftCPU)

    cpu.instruction = parse_op("@4")
    cpu.ticktock()

    cpu.instruction = parse_op("A=A>>1")
    cpu.ticktock()
    assert cpu.addressM == 2

    cpu.ticktock()
    assert cpu.addressM == 1

    cpu.ticktock()
    assert cpu.addressM == 0

    cpu.ticktock()
    assert cpu.addressM == 0

    cpu.instruction = parse_op("@6")
    cpu.ticktock()
    cpu.instruction = parse_op("D=-A")
    cpu.ticktock()
    assert cpu.outM == -6

    cpu.instruction = parse_op("D=D>>1")
    assert cpu.outM == -3
    cpu.ticktock()

    assert cpu.outM == -2  # Note: this is _floor_ division.
    cpu.ticktock()

    assert cpu.outM == -1
    cpu.ticktock()

    assert cpu.outM == -1


def test_computer_gates():
    assert gate_count(ShiftComputer) == {
        'nands': 1_311,  # compare to 1262
        'dffs': 48,
        'roms': 1,
        'rams': 2,
        'inputs': 1,
        'outputs': 1,
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
# Test shift instructions:
#

def test_assemble_shift_ops():
    assert unsigned(parse_op("D=D>>1")) == solved_06.parse_op("D=D") & ~0b001_0_000000_000_000
    assert unsigned(parse_op("A=D+M>>1")) == solved_06.parse_op("A=D+M") & ~0b001_0_000000_000_000


#
# VM translator:
#

def test_vm_simple_add():
    test_07.test_simple_add(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_stack_ops():
    test_07.test_stack_ops(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_memory_access_basic():
    test_07.test_memory_access_basic(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_memory_access_pointer():
    test_07.test_memory_access_pointer(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_memory_access_static():
    test_07.test_memory_access_static(chip=ShiftComputer, assemble=assemble, translator=Translator)


def test_vm_basic_loop():
    test_08.test_basic_loop(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_fibonacci_series():
    test_08.test_fibonacci_series(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_simple_function():
    test_08.test_simple_function(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_nested_call():
    test_08.test_nested_call(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_fibonacci_element():
    test_08.test_fibonacci_element(chip=ShiftComputer, assemble=assemble, translator=Translator)

def test_vm_statics_multiple_files():
    test_08.test_statics_multiple_files(chip=ShiftComputer, assemble=assemble, translator=Translator)


#
# Test modified Math.multiply:
#

def test_multiply():
    translate = Translator()

    translate.push_constant(123)
    translate.push_constant(34)
    translate.neg()
    translate.call("Math", "multiply", 2)

    translate.finish()

    # Include Math.abs here just so we don't have to load the entire library. Might end up
    # implementing it as an opcode anyway.
    abs_ops = """
        function Math.abs 0
        push argument 0
        push constant 0
        lt
        if-goto IF_TRUE0
        goto IF_FALSE0
        label IF_TRUE0
        push argument 0
        neg
        pop argument 0
        label IF_FALSE0
        push argument 0
        return
        """
    for line in abs_ops.split('\n'):
        t = solved_07.parse_line(line)
        if t:
            print(t)
            translate.handle(t)

    computer = run(ShiftComputer, simulator="codegen")
    asm, _, _ = assemble(translate.asm)
    computer.init_rom(asm)

    computer.poke(0, 256)
    translate.asm.run(assemble, computer, stop_cycles=1500, debug=True)

    assert computer.peek(0) == 257
    assert computer.peek(256) == -4182


def test_vm_pong_instructions():
    instruction_count = test_optimal_08.count_pong_instructions(platform=SHIFT_PLATFORM)

    assert instruction_count < 26_100


def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(platform=SHIFT_PLATFORM)

    assert cycles < 19_850


def test_vm_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(platform=SHIFT_PLATFORM)

    assert cycles < 130_000
