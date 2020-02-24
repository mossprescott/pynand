#! /usr/bin/env pytest

import os
import pytest

import nand.syntax
from nand.translate import translate_dir
import project_05, project_06, project_07, project_08

# from nand.translate import AssemblySource
from nand.solutions import solved_07

@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_code_size_pong():
    """A simple translator will work for small programs, but won't be able to fit a real program in the ROM."""
    # TODO: promote this test to test_08, since it has to work or you can't actually play the game.

    instruction_count = count_pong_instructions(project_08.Translator)

    print(f"instructions: {instruction_count:0,d}")

    # Note: the nand2tetris translator does it in about 27,500
    assert instruction_count <= 2**15


def count_pong_instructions(translator):
    translate = translator()
    
    translate.preamble()

    translate_dir(translate, solved_07.parse_line, "examples/Pong")
    translate_dir(translate, solved_07.parse_line, "nand2tetris/tools/OS")  # HACK not committed
    
    translate.finish()

    # for instr in translate.asm:
    #     print(instr)
    return translate.asm.instruction_count


@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_pong_first_iteration():
    cycles = count_pong_cycles_first_iteration(project_05.Computer, project_06.assemble, project_08.Translator)

    print(f"cycles for first iteration: {cycles:0,d}")
    
    assert cycles < 1  #?


def count_pong_cycles_first_iteration(chip, assemble, translator):
    translate = translator()

    translate.preamble()

    translate_dir(translate, solved_07.parse_line, "examples/Pong")
    translate_dir(translate, solved_07.parse_line, "nand2tetris/tools/OS")  # HACK not committed

    translate.finish()

    computer = nand.syntax.run(chip, simulator='codegen')
    asm = assemble(translate.asm)
    computer.init_rom(asm)

    src_map = translate.asm.src_map
    bat_start, (bat_end,) = find_function(src_map, "Bat", "move", 0)
    move_ball_start, (move_ball_end,) = find_function(src_map, "PongGame", "moveBall", 5)

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


def find_function(src_map, class_name, function_name, num_vars):
    """Search in the src map for the location of the instructions that begin and end a particular function.
    Returns a tuple (address of "function" op, [addresses of "return" ops]).
    """

    # Note: reversed, so we always find the _last_ occurrence, in case the function has been overridden
    for addr, op in sorted(src_map.items(), reverse=True):
        if op == f"function {class_name}.{function_name} {num_vars}":
            start = addr
            break

    ends = []
    for addr, op in [t for t in sorted(src_map.items()) if t[0] > addr]:
        if op == "return":
            ends.append(addr)
        elif op.startswith("function"):
            break

    return start, ends


@pytest.mark.skip(reason="Sources aren't in the repo yet")
def test_cycles_to_init():
    cycles = count_cycles_to_init(project_05.Computer, project_06.assemble, project_08.Translator)

    print(f"cycles to init: {cycles:0,d}")
    
    assert cycles < 5_000_000


def count_cycles_to_init(chip, assemble, translator):
    """Count the number of cycles executed before Main.main is called."""

    translate = translator()
    
    translate.preamble()

    translate_dir(translate, solved_07.parse_line, "examples/Draw")
    translate_dir(translate, solved_07.parse_line, "nand2tetris/tools/OS")  # HACK not committed

    translate.finish()

    computer = nand.syntax.run(chip, simulator='codegen')
    asm = assemble(translate.asm)
    computer.init_rom(asm)

    cycles = 0
    while True:
        computer.ticktock()
        if translate.asm.src_map.get(computer.pc) == 'function Main.main 1':
            break
        elif cycles > 10_000_000:
            assert False, "Ran for 10 million cycles without reaching Main.main"
        cycles += 1

    return cycles
