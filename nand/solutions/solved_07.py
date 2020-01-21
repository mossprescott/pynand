"""Solutions for projects 07 and 08.

SPOILER ALERT: this files contains a complete VM translator.
If you want to write this on your own, stop reading now!
"""

# Disclaimer: this implementation was written quickly and seems to work, but those are the only good
# things that can be said about it.


class Translator:
    """Translate all VM opcodes to assembly instructions. 
    
    Note: this implementation is not broken out into separate classes for each project.
    """
    
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
            
    def pop_local(self, index):
        return [f"// pop local {index}"] + self._pop_segment("LCL", index)
        
    def pop_argument(self, index):
        return [f"// pop argument {index}"] + self._pop_segment("ARG", index)
        
    def pop_this(self, index):
        return [f"// pop this {index}"] + self._pop_segment("THIS", index)
        
    def pop_that(self, index):
        return [f"// pop that {index}"] + self._pop_segment("THAT", index)
    
    def pop_temp(self, index):
        assert 0 <= index < 8
        return [f"// pop temp {index}"] + _POP_D + [
            f"@{5+index}",
            "M=D",
        ]
    
    def _pop_segment(self, segment_ptr, index):
        # TODO: special-case small indexes
        return [
            f"@{index}",
            "D=A",
            f"@{segment_ptr}",
            "D=D+M",
            "@R15",
            "M=D",
        ] + _POP_D + [
            "@R15",
            "A=M",
            "M=D",
        ]

    def push_local(self, index):
        return self._push_segment("LCL", index)

    def push_argument(self, index):
        return self._push_segment("ARG", index)

    def push_this(self, index):
        return self._push_segment("THIS", index)

    def push_that(self, index):
        return self._push_segment("THAT", index)

    def push_temp(self, index):
        assert 0 <= index < 8
        return [
            f"// push temp {index}",
            f"@{5+index}",
            "D=M",
        ] + _PUSH_D
        

    def _push_segment(self, segment_ptr, index):
        return [
            f"// push {segment_ptr} {index}",
            f"@{index}",
            "D=A",
            f"@{segment_ptr}",
            "A=D+M",
            "D=M",
        ] + _PUSH_D


    def pop_pointer(self, index):
        if index == 0:
            segment_ptr = "THIS"
        elif index == 1:
            segment_ptr = "THAT"
        else:
            raise SyntaxError(f"Invalid index for pop pointer: {index}")
        return [f"// pop pointer {index}"] + _POP_D + [
            f"@{segment_ptr}",
            "M=D",
        ]

    def push_pointer(self, index):
        if index == 0:
            segment_ptr = "THIS"
        elif index == 1:
            segment_ptr = "THAT"
        else:
            raise SyntaxError(f"Invalid index for push pointer: {index}")
        return [
            f"// push pointer {index}",
            f"@{segment_ptr}",
            "D=M",
        ] + _PUSH_D


    def pop_static(self, index):
        namespace = "static"  # HACK: need to get it from the caller
        return [f"// pop static {index}"] + _POP_D + [
            f"@{namespace}.{index}",
            "M=D",
        ]
        
    def push_static(self, index):
        namespace = "static"  # HACK: need to get it from the caller
        return [
            f"// push static {index}",
            f"@{namespace}.{index}",
            "D=M",
        ] + _PUSH_D


    def label(self, name):
        namespace = "_"  # HACK: need to get it from the caller
        return [
            f"// label {name}",
            f"({namespace}.{name})",
        ]
    
    def if_goto(self, name):
        namespace = "_"  # HACK: need to get it from the caller
        return [f"// if-goto {name}"] + _POP_D + [
            f"@{namespace}.{name}",
            "D;JNE",
        ]

    def goto(self, name):
        namespace = "_"  # HACK: need to get it from the caller
        return [
            f"// goto {name}",
            f"@{namespace}.{name}",
            "0;JMP",
        ]


    def function(self, class_name, function_name, num_vars):
        # Note: when num_vars is 1 or less, it costs no cycles to initialize them to 0, and 
        # it will make the behavior more predictable when there are errors in the program.
        return [
            f"// function {class_name}.{function_name} {num_vars}",
            "@SP",
            "A=M"
        ] + [
            "M=0",
            "A=A+1",
        ]*num_vars

    def return_op(self):
        return ["// return"] + self._pop_segment("ARG", 0) + [
            # SP = LCL
            "@LCL",
            "D=M",
            "@SP",
            "M=D",
            # R15 = old ARG
            "@ARG",
            "D=M",
            "@R15",
            "M=D",
            # restore segment pointers from stack:
        ] + _POP_D + [
            "@THAT",
            "M=D"
        ] + _POP_D + [
            "@THIS",
            "M=D",
        ] + _POP_D + [
            "@ARG",
            "M=D"
        ] + _POP_D + [
            "@LCL",
            "M=D",
            # R14 = return address
        ] + _POP_D + [
            "@R14",
            "M=D",
            # SP = R15 + 1
            "@R15",
            "D=M+1",
            "@SP",
            "M=D",
            # jmp to R14
            "@R14",
            "A=M",
            "0;JMP",
        ]


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

SP = 0
LCL = 1
ARG = 2
THIS = 3
THAT = 4


def print_vm_state(computer, num_locals, num_args):
    stack_bottom = max(256, computer.peek(ARG)+num_args+5)
    stack = [str(computer.peek(i)) for i in range(stack_bottom, computer.peek(SP))]
    lcl = [str(computer.peek(i)) for i in range(computer.peek(LCL), computer.peek(LCL)+num_locals)]
    arg = [str(computer.peek(i)) for i in range(computer.peek(ARG), computer.peek(ARG)+num_args)]
    tmp = [str(computer.peek(i)) for i in range(5, 13)]
    gpr = [str(computer.peek(i)) for i in range(13, 16)]
    static = [str(computer.peek(i)) for i in range(16, 32)]
    print(f"PC: {computer.pc}; temp: {tmp}; gpr: {gpr}")
    print(f"  stack: {stack}; local: {lcl}; arg: {arg}")
    print(f"  static: {static}")


# TODO: VM debugger
# Record a map of instructions back to the opcodes they were translated from.
# Execute one opcode at a time, show state after each.
# Capture number of locals/args as call/function ops go by?
