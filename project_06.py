# Assembler
#
# See https://www.nand2tetris.org/project06

# SOLVERS: remove this import to get started
from nand.solutions import solved_06


def parse_op(string):
    """Parse a single assembly op directly to the corresponding Hack instruction word.

    The op may be a numeric symbol (an A-command) or a C-command, but not a reference
    to a symbol or variable.
    """

    # SOLVERS: replace this with code to parse a single assembly instruction string, producing
    # a machine instruction as a 16-bit int
    instr = solved_06.parse_op(string)

    return instr


def assemble(lines, min_static=16, max_static=255):
    """Parse a sequence of lines as assembly commands, accounting for builtin symbols,
    labels, and variables.

    "//" denotes a comment and is ignored, along with the remainder of the line.
    Leading and trailing white space on each line is ignored.
    After comments and white space are stripped, blank lines are ignored.

    :return: A tuple containing (list of instruction words,
                dictionary mapping labels to locations in ROM,
                dictionary mapping non-label symbols to addresses in RAM).
    """

    # SOLVERS: replace this with code to parse a sequence of lines, using parse_op
    # to handle the individual instructions found within it.
    return solved_06.assemble(lines, min_static=min_static, max_static=max_static)
