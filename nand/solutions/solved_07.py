"""Solutions for project 07.

SPOILER ALERT: this files contains a complete VM translator.
If you want to write this on your own, stop reading now!
"""

# Disclaimer: this implementation was written quickly and seems to work, but those are the only good
# things that can be said about it.


def translate_push_constant(label_gen, value):
    # TODO: special-case 1, 0, -1 and negative values
    return [
        f"// push constant {value}",
        f"@{value}",
        "D=A",
        ] + _PUSH_D


def translate_add(label_gen):
    # TODO: mutate M in place, for a lot fewer instructions
    return ["// add"] + _POP_D_M + [
        "D=D+M",
        ] + _PUSH_D


def translate_sub(label_gen):
    # TODO: mutate M in place, for a lot fewer instructions
    return ["// sub"] + _POP_D_M + [
        "D=M-D",
        ] + _PUSH_D


def translate_neg(label_gen):
    # TODO: negate M in place, for a lot fewer instructions
    return ["// neg"] + _POP_D + [
        "D=-D",
        ] + _PUSH_D


def translate_and(label_gen):
    # TODO: mutate M in place, for a lot fewer instructions
    return ["// and"] + _POP_D_M + [
        "D=D&M",
        ] + _PUSH_D


def translate_or(label_gen):
    # TODO: mutate M in place, for a lot fewer instructions
    return ["// or"] + _POP_D_M + [
        "D=D|M",
        ] + _PUSH_D


def translate_not(label_gen):
    # TODO: negate M in place, for a lot fewer instructions
    return ["// neg"] + _POP_D + [
        "D=!D",
        ] + _PUSH_D
    
    # l1 = label_gen("not")
    # l2 = label_gen("not")
    # return ["// not"] + _POP_D + [
    #     f"@{l1}",
    #     "D;JEQ",
    #     "D=0",
    #     f"@{l2}",
    #     "0;JMP",
    #     f"({l1})",
    #     "D=-1",
    #     f"({l2})",
    #     ] + _PUSH_D


def translate_eq(label_gen):
    l1 = label_gen("eq")
    l2 = label_gen("eq")
    return ["// eq"] + _POP_D_M + [
        "D=M-D",
        f"@{l1}",
        "D;JEQ",
        "D=0",
        f"@{l2}",
        "0;JMP",
        f"({l1})",
        "D=-1",
        f"({l2})",
        ] + _PUSH_D


def translate_lt(label_gen):
    l1 = label_gen("lt")
    l2 = label_gen("lt")
    return ["// lt"] + _POP_D_M + [
        "D=M-D",
        f"@{l1}",
        "D;JLT",
        "D=0",
        f"@{l2}",
        "0;JMP",
        f"({l1})",
        "D=-1",
        f"({l2})",
        ] + _PUSH_D


def translate_gt(label_gen):
    l1 = label_gen("gt")
    l2 = label_gen("gt")
    return ["// gt"] + _POP_D_M + [
        "D=M-D",
        f"@{l1}",
        "D;JGT",
        "D=0",
        f"@{l2}",
        "0;JMP",
        f"({l1})",
        "D=-1",
        f"({l2})",
        ] + _PUSH_D


# TODO: having to thread this through all the calls is pretty lame. 
# Maybe make the whole shebang a class, with label_gen and all of the opcode handlers
# as methods.
def make_label_gen():
    seq = 0
    def gen_next(str):
        nonlocal seq
        result = f"_{str}_{seq}"
        seq += 1
        return result
    return gen_next
    

# Common sequence pushing the contents of the D register onto the stack:
_PUSH_D = [
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1",    
]

# Common sequence popping one value from the stack into D:
_POP_D = [
    "@SP",
    "AM=M-1",
    "D=M",
]

# Common sequence popping two values from the stack into D (top) and M (second from top):
_POP_D_M = [
    "@SP",
    "AM=M-1",
    "D=M",
    "@SP",
    "AM=M-1",    
]