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

    # for instr in translate.asm:
    #     print(instr)
    return translate.asm.instruction_count


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
