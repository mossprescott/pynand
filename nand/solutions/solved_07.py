"""Solutions for project 07.

SPOILER ALERT: this files contains a complete VM translator.
If you want to write this on your own, stop reading now!
"""

# Disclaimer: this implementation was written quickly and seems to work, but those are the only good
# things that can be said about it.


class Translator:
    def __init__(self):
        self.seq = 0

    def push_constant(self, value):
        # TODO: special-case 1, 0, -1 and negative values
        return [
            f"// push constant {value}",
            f"@{value}",
            "D=A",
            ] + _PUSH_D

    def add(self):
        # TODO: mutate M in place, for a lot fewer instructions
        return ["// add"] + _POP_D_M + [
            "D=D+M",
            ] + _PUSH_D

    def sub(self):
        # TODO: mutate M in place, for a lot fewer instructions
        return ["// sub"] + _POP_D_M + [
            "D=M-D",
            ] + _PUSH_D

    def neg(self):
        # TODO: negate M in place, for a lot fewer instructions
        return ["// neg"] + _POP_D + [
            "D=-D",
            ] + _PUSH_D

    def and_op(self):
        # TODO: mutate M in place, for a lot fewer instructions
        return ["// and"] + _POP_D_M + [
            "D=D&M",
            ] + _PUSH_D

    def or_op(self):
        # TODO: mutate M in place, for a lot fewer instructions
        return ["// or"] + _POP_D_M + [
            "D=D|M",
            ] + _PUSH_D

    def not_op(self):
        # TODO: negate M in place, for a lot fewer instructions
        return ["// neg"] + _POP_D + [
            "D=!D",
            ] + _PUSH_D

    def eq(self):
        l1 = self.next_label("eq")
        l2 = self.next_label("eq")
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

    def lt(self):
        l1 = self.next_label("lt")
        l2 = self.next_label("lt")
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

    def gt(self):
        l1 = self.next_label("gt")
        l2 = self.next_label("gt")
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

    def next_label(self, name):
        result = f"_{name}_{self.seq}"
        self.seq += 1
        return result
    

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