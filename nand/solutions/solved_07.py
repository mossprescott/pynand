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
        self.class_namespace = "static"
        self.function_namespace = "_"

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
        self.asm.start(f"pop local {index}")
        self._pop_segment("LCL", index)
        
    def pop_argument(self, index):
        self.asm.start(f"pop argument {index}")
        self._pop_segment("ARG", index)
        
    def pop_this(self, index):
        self.asm.start(f"pop this {index}")
        self._pop_segment("THIS", index)
        
    def pop_that(self, index):
        self.asm.start(f"pop that {index}")
        self._pop_segment("THAT", index)
    
    def pop_temp(self, index):
        assert 0 <= index < 8
        self.asm.start(f"pop temp {index}")
        self._pop_d()
        self.asm.instr(f"@{5+index}")
        self.asm.instr("M=D")
    
    def _pop_segment(self, segment_ptr, index):
        # TODO: special-case small indexes
        self.asm.instr(f"@{index}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("D=D+M")
        self.asm.instr("@R15")
        self.asm.instr("M=D")
        self._pop_d()
        self.asm.instr("@R15")
        self.asm.instr("A=M")
        self.asm.instr("M=D")

    def push_local(self, index):
        self.asm.start(f"push local {index}")
        return self._push_segment("LCL", index)

    def push_argument(self, index):
        self.asm.start(f"push argument {index}")
        return self._push_segment("ARG", index)

    def push_this(self, index):
        self.asm.start(f"push this {index}")
        return self._push_segment("THIS", index)

    def push_that(self, index):
        self.asm.start(f"push that {index}")
        return self._push_segment("THAT", index)

    def push_temp(self, index):
        assert 0 <= index < 8
        self.asm.start(f"push temp {index}")
        self.asm.instr(f"@{5+index}")
        self.asm.instr("D=M")
        self._push_d()
        

    def _push_segment(self, segment_ptr, index):
        self.asm.instr(f"@{index}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("A=D+M")
        self.asm.instr("D=M")
        self._push_d()


    def pop_pointer(self, index):
        self.asm.start(f"pop pointer {index}")
        if index == 0:
            segment_ptr = "THIS"
        elif index == 1:
            segment_ptr = "THAT"
        else:
            raise SyntaxError(f"Invalid index for pop pointer: {index}")
        self._pop_d()
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("M=D")

    def push_pointer(self, index):
        self.asm.start(f"push pointer {index}")
        if index == 0:
            segment_ptr = "THIS"
        elif index == 1:
            segment_ptr = "THAT"
        else:
            raise SyntaxError(f"Invalid index for push pointer: {index}")
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("D=M")
        self._push_d()


    def pop_static(self, index):
        self.asm.start(f"push static {index}")
        self._pop_d()
        self.asm.instr(f"@{self.class_namespace}.static{index}")
        self.asm.instr("M=D")
        
    def push_static(self, index):
        self.asm.start(f"pop static {index}")
        self.asm.instr(f"@{self.class_namespace}.static{index}")
        self.asm.instr("D=M")
        self._push_d()


    def label(self, name):
        self.asm.start(f"label {name}")
        self.asm.label(f"{self.function_namespace}${name}")
    
    def if_goto(self, name):
        self.asm.start(f"if-goto {name}")
        self._pop_d()
        self.asm.instr(f"@{self.function_namespace}${name}")
        self.asm.instr("D;JNE")

    def goto(self, name):
        self.asm.start(f"goto {name}")
        self.asm.instr(f"@{self.function_namespace}${name}")
        self.asm.instr("0;JMP")


    def function(self, class_name, function_name, num_vars):
        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{function_name}"

        self.asm.start(f"function {class_name}.{function_name} {num_vars}")
        self.asm.label(f"{self.function_namespace}")

        self.asm.instr("@SP")
        self.asm.instr("A=M")
        for _ in range(num_vars):
            self.asm.instr("M=0")
            self.asm.instr("A=A+1")
        self.asm.instr("D=A")
        self.asm.instr("@SP")
        self.asm.instr("M=D")

    def return_op(self):
        self.asm.start(f"return")
        
        # R13 = result
        self._pop_d()
        self.asm.instr("@R13")
        self.asm.instr("M=D")
        
        # SP = LCL
        self.asm.instr("@LCL")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("M=D")
        # R15 = ARG
        self.asm.instr("@ARG")
        self.asm.instr("D=M")
        self.asm.instr("@R15")
        self.asm.instr("M=D")
        # restore segment pointers from stack:
        self._pop_d()
        self.asm.instr("@THAT")
        self.asm.instr("M=D")
        self._pop_d()
        self.asm.instr("@THIS")
        self.asm.instr("M=D")
        self._pop_d()
        self.asm.instr("@ARG")
        self.asm.instr("M=D")
        self._pop_d()
        self.asm.instr("@LCL")
        self.asm.instr("M=D")
        # R14 = return address
        self._pop_d()
        self.asm.instr("@R14")
        self.asm.instr("M=D")
        # SP = R15
        self.asm.instr("@R15")
        self.asm.instr("D=M")
        self.asm.instr("@SP")
        self.asm.instr("M=D")
        # Push R13 (result)
        self.asm.instr("@R13")
        self.asm.instr("D=M")
        self._push_d()
        # jmp to R14
        self.asm.instr("@R14")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")


    def call(self, class_name, function_name, num_args):
        l1 = self.asm.next_label("RET_ADDRESS_CALL")

        self.asm.start(f"call {class_name}.{function_name} {num_args}")
        
        # R15 = SP - num_args
        self.asm.instr("@SP")
        self.asm.instr("D=M")
        self.asm.instr(f"@{num_args}")  # TODO: special-case 0 and 1
        self.asm.instr("D=D-A")
        self.asm.instr("@R15")
        self.asm.instr("M=D")
        
        self.asm.instr(f"@{l1}")
        self.asm.instr("D=A")
        self._push_d()
        self.asm.instr("@LCL")
        self.asm.instr("D=M")
        self._push_d()
        self.asm.instr("@ARG")
        self.asm.instr("D=M")
        self._push_d()
        self.asm.instr("@THIS")
        self.asm.instr("D=M")
        self._push_d()
        self.asm.instr("@THAT")
        self.asm.instr("D=M")
        self._push_d()
        
        # LCL = SP
        # Note: setting LCL here (as opposed to in "function") feels wrong, but it makes the 
        # state of the segment pointers consistent after each opcode, so it's easier to debug.
        self.asm.instr("@SP")
        self.asm.instr("D=M")
        self.asm.instr("@LCL")
        self.asm.instr("M=D")
        
        # ARG = R15
        self.asm.instr("@R15")
        self.asm.instr("D=M")
        self.asm.instr("@ARG")
        self.asm.instr("M=D")
            
        # JMP to callee
        self.asm.instr(f"@{class_name.lower()}.{function_name}")
        self.asm.instr("0;JMP")
        self.asm.label(f"{l1}")


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
