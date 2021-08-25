#! /usr/bin/env pytest

import os
import pytest

import nand.syntax
from nand.platform import USER_PLATFORM
from nand.translate import translate_dir, translate_library

def test_code_size_pong():
    """A simple translator will work for small programs, but won't be able to fit a real program in the ROM."""
    # TODO: promote this test to test_08, since it has to work or you can't actually play the game.

    instruction_count = count_pong_instructions(USER_PLATFORM)

    print(f"instructions: {instruction_count:0,d}")

    # Note: the nand2tetris translator does it in about 27,500
    assert instruction_count <= 2**15


def count_pong_instructions(platform):
    translator = platform.translator()

    translator.preamble()
    translate_dir(translator, platform, "examples/project_11/Pong")
    translate_library(translator, platform)
    translator.finish()

    return translator.asm.instruction_count


def test_pong_first_iteration():
    cycles = count_pong_cycles_first_iteration(USER_PLATFORM)

    print(f"cycles for first iteration: {cycles:0,d}")

    assert cycles < 35000


def count_pong_cycles_first_iteration(platform, simulator="codegen"):
    translator = platform.translator()

    translator.preamble()
    translate_dir(translator, platform, "examples/project_11/Pong")
    translate_library(translator, platform)
    translator.finish()

    computer = nand.syntax.run(platform.chip, simulator=simulator)
    asm, _, _ = platform.assemble(translator.asm)
    computer.init_rom(asm)

    src_map = translator.asm.src_map
    bat_start, (bat_end,) = find_function(src_map, "Bat", "move")
    move_ball_start, (move_ball_end,) = find_function(src_map, "PongGame", "moveBall")

    cycles = 0

    while computer.pc != bat_start:
        computer.ticktock()
        cycles += 1
        assert cycles < 10_000_000
    bat_start_cycles = cycles
    # print(f"Bat.move started at cycle {cycles:0,d}")

    while computer.pc != bat_end:
        computer.ticktock()
        cycles += 1
        assert cycles < 10_000_000
    bat_end_cycles = cycles
    # print(f"Bat.move ended at cycle {cycles:0,d}")

    while computer.pc != move_ball_start:
        computer.ticktock()
        cycles += 1
        assert cycles < 10_000_000
    move_ball_start_cycles = cycles
    # print(f"moveBall started at cycle {cycles:0,d}")

    while computer.pc != move_ball_end:
        computer.ticktock()
        cycles += 1
        assert cycles < 10_000_000
    move_ball_end_cycles = cycles
    # print(f"moveBall ended at cycle {cycles:0,d}")

    return (bat_end_cycles - bat_start_cycles) + (move_ball_end - move_ball_start)


def find_function(src_map, class_name, function_name):
    """Search in the src map for the location of the instructions that begin and end a particular function.
    Returns a tuple (address of "function" op, [addresses of "return" ops]).
    """

    # Note: reversed, so we always find the _last_ occurrence, in case the function has been overridden
    for addr, op in sorted(src_map.items(), reverse=True):
        if op.startswith(f"function {class_name}.{function_name} "):
            start = addr
            break

    ends = []
    for addr, op in [t for t in sorted(src_map.items()) if t[0] > addr]:
        if op == "return":
            ends.append(addr)
        elif op.startswith("function"):
            break

    return start, ends


def test_cycles_to_init():
    cycles = count_cycles_to_init(USER_PLATFORM)

    print(f"cycles to init: {cycles:0,d}")

    assert cycles < 5_000_000


def count_cycles_to_init(platform, simulator="codegen"):
    """Count the number of cycles executed before Main.main is called."""

    translator = platform.translator()

    translator.preamble()
    translate_dir(translator, platform, "examples/project_12/ScreenTest.jack")
    translate_library(translator, platform)
    translator.finish()

    computer = nand.syntax.run(platform.chip, simulator=simulator)
    asm, _, _ = platform.assemble(translator.asm)
    computer.init_rom(asm)

    cycles = 0
    while True:
        computer.ticktock()
        op = translator.asm.src_map.get(computer.pc)
        if op is not None and op.startswith('function Main.main'):
            break
        elif cycles > 10_000_000:
            assert False, "Ran for 10 million cycles without reaching Main.main"
        cycles += 1

    return cycles
