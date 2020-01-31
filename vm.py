import os
import sys

from nand.translate import translate_dir
from project_06 import assemble
from project_07 import parse_line
from project_08 import Translator

# from nand.solutions import solved_07
# from nand.translate import AssemblySource

import computer

TRACE = False


def main():
    translate = Translator()
    # translate = solved_07.Translator(AssemblySource())
    
    translate.preamble()
    
    translate_dir(translate, parse_line, sys.argv[1])
    translate_dir(translate, parse_line, "nand2tetris/tools/OS")  # HACK not committed
    
    if TRACE:
        for instr in translate.asm:
            print(instr)

    computer.run(assemble(translate.asm), src_map=translate.asm.src_map if TRACE else None)


if __name__ == "__main__":
    main()
