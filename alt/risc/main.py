#! /usr/bin/env python3

from nand.solutions.solved_06 import assemble
from nand.platform import BUNDLED_PLATFORM
import alt.risc.asm
import alt.risc.chip
import alt.risc.vm

# First off, a translator for the standard VM:
RiSC_PLATFORM = BUNDLED_PLATFORM._replace(
    chip=alt.risc.chip.RiSCComputer,
    assemble=alt.risc.asm.assemble,
    translator=alt.risc.vm.Translator)

if __name__ == "__main__":
    import computer

    computer.main(RiSC_PLATFORM)
