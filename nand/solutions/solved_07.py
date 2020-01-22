"""Solutions for projects 07 and 08.

SPOILER ALERT: this files contains a complete VM translator.
If you want to write this on your own, stop reading now!
"""

# Disclaimer: this implementation was written quickly and seems to work, but those are the only good
# things that can be said about it.


class Translator:
    """Translate all VM opcodes to assembly instructions. 
    
    Note: this implementation is not broken out into separate classes for projects 07 and 08.
    """
    
    def __init__(self, asm):
        self.asm = asm

    def push_constant(self, value):
        # TODO: special-case 1, 0, -1 and negative values
        self.asm.start(f"push constant {value}")
        self.asm.instr(f"@{value}")
        self.asm.instr("D=A")
        self._push_d()

    def add(self):
        # TODO: mutate M in place, for a lot fewer instructions
        self.asm.start("add")
        self._pop_d_m()
        self.asm.instr("D=D+M")
        self._push_d()

    def sub(self):
        # TODO: mutate M in place, for a lot fewer instructions
        self.asm.start("sub")
        self._pop_d_m()
        self.asm.instr("D=M-D")
        self._push_d()

    def neg(self):
        # TODO: negate M in place, for a lot fewer instructions
        self.asm.start("neg")
        self._pop_d()
        self.asm.instr("D=-D")
        self._push_d()

    def and_op(self):
        # TODO: mutate M in place, for a lot fewer instructions
        self.asm.start("and")
        self._pop_d_m()
        self.asm.instr("D=D&M")
        self._push_d()

    def or_op(self):
        # TODO: mutate M in place, for a lot fewer instructions
        self.asm.start("or")
        self._pop_d_m()
        self.asm.instr("D=D|M")
        self._push_d()

    def not_op(self):
        # TODO: negate M in place, for a lot fewer instructions
        self.asm.start("not")
        self._pop_d()
        self.asm.instr("D=!D")
        self._push_d()

    def eq(self):
        l1 = self.asm.next_label("eq")
        l2 = self.asm.next_label("eq")
        self.asm.start("eq")
        self._pop_d_m()
        self.asm.instr("D=M-D")
        self.asm.instr(f"@{l1}")
        self.asm.instr("D;JEQ")
        self.asm.instr("D=0")
        self.asm.instr(f"@{l2}")
        self.asm.instr("0;JMP")
        self.asm.label(l1)
        self.asm.instr("D=-1")
        self.asm.label(l2)
        self._push_d()

    def lt(self):
        l1 = self.asm.next_label("lt")
        l2 = self.asm.next_label("lt")
        self.asm.start("lt")
        self._pop_d_m()
        self.asm.instr("D=M-D")
        self.asm.instr(f"@{l1}")
        self.asm.instr("D;JLT")
        self.asm.instr("D=0")
        self.asm.instr(f"@{l2}")
        self.asm.instr("0;JMP")
        self.asm.label(l1)
        self.asm.instr("D=-1")
        self.asm.label(l2)
        self._push_d()

    def gt(self):
        l1 = self.asm.next_label("gt")
        l2 = self.asm.next_label("gt")
        self.asm.start("gt")
        self._pop_d_m()
        self.asm.instr("D=M-D")
        self.asm.instr(f"@{l1}")
        self.asm.instr("D;JGT")
        self.asm.instr("D=0")
        self.asm.instr(f"@{l2}")
        self.asm.instr("0;JMP")
        self.asm.label(l1)
        self.asm.instr("D=-1")
        self.asm.label(l2)
        self._push_d()
            
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
        return [
            f"// label {name}",
            f"({self.namespace}${name})",
        ]
    
    def if_goto(self, name):
        return [f"// if-goto {name}"] + _POP_D + [
            f"@{self.namespace}${name}",
            "D;JNE",
        ]

    def goto(self, name):
        return [
            f"// goto {name}",
            f"@{self.namespace}${name}",
            "0;JMP",
        ]


    def function(self, class_name, function_name, num_vars):
        self.namespace = f"{class_name.lower()}.{function_name}"
        return [
            f"// function {class_name}.{function_name} {num_vars}",
            f"({self.namespace})",
            "@SP",
            "A=M"
        ] + [
            "M=0",
            "A=A+1",
        ]*num_vars + [
            "D=A",
            "@SP",
            "M=D",
        ]

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


    def call(self, class_name, function_name, num_args):
        l1 = self.next_label("RET_ADDRESS_CALL")
        return [
            f"// call {class_name}.{function_name} {num_args}",
            f"@{l1}",
            "D=A",
        ] + _PUSH_D + [
            "@LCL",
            "D=A",
        ] + _PUSH_D + [
            "@ARG",
            "D=A",
        ] + _PUSH_D + [
            "@THIS",
            "D=A",
        ] + _PUSH_D + [
            "@THAT",
            "D=A",
        ] + _PUSH_D + [
            # LCL = SP
            "@SP",
            "D=A",
            "@LCL",
            "M=D",
            
            # ARG = SP - (5 + num_args)
            f"@{5 + num_args}",
            "D=D-A",
            "@ARG",
            "M=D",
            
            # JMP to callee
            f"@{class_name.lower()}.{function_name}",
            "0;JMP",
            f"({l1})",
        ]
        
        return None

    def _push_d(self):
        """Common sequence pushing the contents of the D register onto the stack."""
        self.asm.instr("@SP")
        self.asm.instr("A=M")
        self.asm.instr("M=D")
        self.asm.instr("@SP")
        self.asm.instr("M=M+1")

    def _pop_d(self):
        """Common sequence popping one value from the stack into D."""
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")
        self.asm.instr("D=M")

    def _pop_d_m(self):
        """Common sequence popping two values from the stack into D (top) and M (second from top)."""
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")


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
