# See https://www.nand2tetris.org/project07

# SOLVERS: remove this import to get started
from nand.solutions import solved_07

def translate_push_constant(label_gen, value):
    # SOLVERS: write some code here to construct a list of strings containing Hack assembly 
    # instructions to push `value` onto the stack
    return solved_07.translate_push_constant(label_gen, value)


def translate_add(label_gen):
    # SOLVERS: implement the add opcode
    # Hint: this is actually going to be the same instructions every time, so just build
    # a list and return it.
    return solved_07.translate_add(label_gen)


def translate_eq(label_gen):
    # SOLVERS: implement the eq opcode
    return solved_07.translate_eq(label_gen)


def translate_lt(label_gen):
    # SOLVERS: implement the lt opcode
    return solved_07.translate_lt(label_gen)


def translate_gt(label_gen):
    # SOLVERS: implement the gt opcode
    return solved_07.translate_gt(label_gen)
