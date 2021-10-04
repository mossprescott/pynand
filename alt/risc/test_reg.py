#! /usr/bin/env pytest

from alt.risc.chip import RiSCComputer
import alt.risc.main
import alt.risc.reg
import test_07, test_08, test_12, test_optimal_08


# All the "OS" tests work, because they compile and run complete Jack programs:

def test_array_lib():
    test_12.test_array_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_string_lib():
    test_12.test_string_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_memory_lib():
    test_12.test_memory_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_keyboard_lib():
    test_12.test_keyboard_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_output_lib():
    test_12.test_output_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_math_lib():
    test_12.test_math_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_screen_lib():
    test_12.test_screen_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)


def test_code_size_pong():
    instruction_count = test_optimal_08.count_pong_instructions(alt.risc.reg.RiSC_REG_PLATFORM)

    assert instruction_count < -1  # 19_100

def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(alt.risc.reg.RiSC_REG_PLATFORM)

    assert cycles < -1 # 27_500


def test_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(alt.risc.reg.RiSC_REG_PLATFORM)

    assert cycles < -1 # 80_000
