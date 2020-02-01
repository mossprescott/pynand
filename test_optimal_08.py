import os

import nand.syntax
from nand.translate import translate_dir
from project_05 import Computer
from project_06 import assemble
from project_07 import parse_line
from project_08 import Translator

# from nand.translate import AssemblySource
# from nand.solutions import solved_07

def test_code_size_pong():
    """A simple translator will work for small programs, but won't be able to fit a real program in the ROM."""

    translate = Translator()
    
    translate.preamble()

    translate_dir(translate, parse_line, "examples/Pong")
    translate_dir(translate, parse_line, "nand2tetris/tools/OS")  # HACK not committed

    # for instr in translate.asm:
    #     print(instr)
    print(f"instructions: {translate.asm.instruction_count:0,d}")

    # Note: the nand2tetris translator does it in about 27,500
    assert translate.asm.instruction_count <= 2**15


def test_cycles_to_init():
    """Count the number of cycles executed before Main.main is called."""

    translate = Translator()
    # translate = solved_07.Translator(AssemblySource())
    
    translate.preamble()

    translate_dir(translate, parse_line, "examples/Draw")
    translate_dir(translate, parse_line, "nand2tetris/tools/OS")  # HACK not committed

    computer = nand.syntax.run(Computer, simulator='codegen')
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

    print(f"cycles to init: {cycles:0,d}")
    
    assert cycles < 5_000_000
