#! /usr/bin/env pytest

from alt.risc.chip import RiSCComputer
import alt.risc.vm
import test_07, test_08, test_12, test_optimal_08


# def test_simple_add():
#     # TODO: this isn't going to work; the test assumes SP is mapped to RAM[0],
#     # and it uses HACK assembly to initialize it.
#     simulator = "compiled"
#     test_07.test_simple_add(chip=RiSCComputer, translator=alt.risc.vm.Translator, simulator=simulator)

# def test_large_constant():
#     # TODO: bit masking for constants with lui/addi is tricky...
#     assert False


def test_fibonacci_element():
    """This is the first VM test that uses the "normal" Sys.init() invocation sequence."""

    test_08.test_fibonacci_element(RiSCComputer, alt.risc.asm.assemble, alt.risc.vm.Translator)


# All the "OS" tests work, because they compile and run complete Jack programs:

def test_array_lib():
    test_12.test_array_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)

def test_string_lib():
    test_12.test_string_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)

def test_memory_lib():
    test_12.test_memory_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)

def test_keyboard_lib():
    test_12.test_keyboard_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)

def test_output_lib():
    test_12.test_keyboard_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)

def test_math_lib():
    test_12.test_math_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)

def test_screen_lib():
    test_12.test_screen_lib(platform=alt.risc.vm.RiSC_VM_PLATFORM)


def test_code_size_pong():
    instruction_count = test_optimal_08.count_pong_instructions(platform=alt.risc.vm.RiSC_VM_PLATFORM)

    assert instruction_count < 19_100