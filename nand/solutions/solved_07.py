"""Solutions for projects 07 and 08.

SPOILER ALERT: this files contains a complete VM translator.
If you want to write this on your own, stop reading now!
"""


class Translator:
    """Translate all VM opcodes to assembly instructions. 
    
    Note: this implementation is not broken out into separate classes for projects 07 and 08.
    """
    
    def __init__(self, asm):
        self.asm = asm
        self.class_namespace = "static"
        self.function_namespace = "_"
        
        # HACK: some code that's always required, even when preamble is not used.
        
        start = self.asm.next_label("start")
        self.asm.instr(f"@{start}")
        self.asm.instr("0;JMP")
        
        # "Microcoded" instructions:
        self.eq_label = self._compare("EQ")
        self.lt_label = self._compare("LT")
        self.gt_label = self._compare("GT")
        self.return_label = self._return()
        self.call_label = self._call()
        
        self.asm.label(start)

    
    def push_constant(self, value):
        assert 0 <= value < 2**15
        self.asm.start(f"push constant {value}")
        if value <= 1:
            # Save a couple of instructions by embedding the value right in the assignment:
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("A=M-1")
            self.asm.instr(f"M={value}")
        elif value == 2:
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("A=M-1")
            self.asm.instr("M=1")
            self.asm.instr("M=M+1")
        else:
            # All other values use D for 6 instructions total:
            self.asm.instr(f"@{value}")
            self.asm.instr("D=A")
            self._push_d()

    def add(self):
        self.asm.start("add")
        self._binary("D+M")
        
    def sub(self):
        self.asm.start("sub")
        self._binary("M-D")

    def neg(self):
        self.asm.start("neg")
        self._unary("-M")

    def and_op(self):
        self.asm.start("and")
        self._binary("D&M")

    def or_op(self):
        self.asm.start("or")
        self._binary("D|M")

    def not_op(self):
        self.asm.start("not")
        self._unary("!M")

    def eq(self):
        # A short sequence that jumps to the common impl and returns, which costs only 4 instructions,
        # as opposed to 20 or more (which could probaby be reduced to more like 16).
        return_label = self.asm.next_label("eq_return")
        self.asm.start("eq")
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{self.eq_label}")
        self.asm.instr("0;JMP")
        self.asm.label(return_label)

    def lt(self):
        # A short sequence that jumps to the common impl and returns, which costs only 4 instructions,
        # as opposed to 20 or more (which could probaby be reduced to more like 16).
        return_label = self.asm.next_label("lt_return")
        self.asm.start("lt")
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{self.lt_label}")
        self.asm.instr("0;JMP")
        self.asm.label(return_label)

    def gt(self):
        # A short sequence that jumps to the common impl and returns, which costs only 4 instructions,
        # as opposed to 20 or more (which could probaby be reduced to more like 16).
        return_label = self.asm.next_label("gt_return")
        self.asm.start("gt")
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{self.gt_label}")
        self.asm.instr("0;JMP")
        self.asm.label(return_label)
            
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
        self.asm.instr(f"@R{5+index}")
        self.asm.instr("M=D")
    
    def _pop_segment(self, segment_ptr, index):
        if index <= 6:
            self._pop_d()
            
            self.asm.instr(f"@{segment_ptr}")
            if index == 0:
                self.asm.instr("A=M")
            else:
                self.asm.instr("A=M+1")
                for _ in range(index-1):
                    self.asm.instr("A=A+1")
            self.asm.instr("M=D")
            
        else:
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
        self.asm.instr(f"@R{5+index}")
        self.asm.instr("D=M")
        self._push_d()
        

    def _push_segment(self, segment_ptr, index):
        if index == 0:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M")
            self.asm.instr("D=M")
        elif index == 1:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M+1")
            self.asm.instr("D=M")
        elif index == 2:
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("A=M+1")
            self.asm.instr("A=A+1")
            self.asm.instr("D=M")
        else:
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
            raise SyntaxError(f"Invalid index for pop pointer: {index!r}")
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
        # A short sequence that jumps to the common impl, which costs only 2 instructions in ROM per
        # use. Note: this is simple because it doesn't need to return here.
        self.asm.start("return")
        self.asm.instr(f"@{self.return_label}")
        self.asm.instr("0;JMP")


    def call(self, class_name, function_name, num_args):
        # Note: this is currently 13 instructions per occurrence, which is pretty heavy.
        # Can it be shrunk more? Move more work into the common impl somehow?
        
        return_label = self.asm.next_label("RET_ADDRESS_CALL")

        self.asm.start(f"call {class_name}.{function_name} {num_args}")
                
        # Push the return address
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self._push_d()

        # R14 = callee address
        self.asm.instr(f"@{class_name.lower()}.{function_name}")
        self.asm.instr("D=A")
        self.asm.instr("@R14")
        self.asm.instr("M=D")
        
        # D = num_args + 1
        self.asm.instr(f"@{num_args+1}")
        self.asm.instr("D=A")

        # Jump to the common implementation
        self.asm.instr(f"@{self.call_label}") 
        self.asm.instr("0;JMP")

        self.asm.label(f"{return_label}")


    def preamble(self):
        self.asm.start("VM initialization")
        self.asm.instr("@256")
        self.asm.instr("D=A")
        self.asm.instr("@SP")
        self.asm.instr("M=D")

        self.call("Sys", "init", 0)  # TODO: don't need the full frame?


    def _compare(self, op):
        # Common implementation for compare opcodes:
        label = self.asm.next_label(f"{op.lower()}_common")
        l1 = self.asm.next_label(f"{op.lower()}_common$1")
        l2 = self.asm.next_label(f"{op.lower()}_common$2")
        self.asm.start(f"{op.lower()}_common")
        self.asm.label(label)
        self.asm.instr("@R15")    # R15 = return address
        self.asm.instr("M=D")
        self._pop_d_m()           # EQ
        self.asm.instr("D=M-D")
        self.asm.instr(f"@{l1}")
        self.asm.instr(f"D;J{op}")
        self.asm.instr("D=0")
        self.asm.instr(f"@{l2}")
        self.asm.instr("0;JMP")
        self.asm.label(l1)
        self.asm.instr("D=-1")
        self.asm.label(l2)
        self._push_d()
        self.asm.instr("@R15")   # JMP to R15
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")
        return label

    def _push_d(self):
        """Common sequence pushing the contents of the D register onto the stack."""
        self.asm.instr("@SP")
        self.asm.instr("M=M+1")
        self.asm.instr("A=M-1")
        self.asm.instr("M=D")

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
        
    def _binary(self, op):
        """Pop two, combine, and push, but update SP only once."""
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")  # update SP
        self.asm.instr("D=M")     # D = top
        self.asm.instr("@SP")
        self.asm.instr("A=M-1")   # Don't update SP again

        self.asm.instr(f"M={op}")   
        
    def _unary(self, op):
        """Modify the top item on the stack without updating SP."""
        self.asm.instr("@SP")
        self.asm.instr("A=M-1")
        self.asm.instr(f"M={op}")

    def _call(self):
        """Common sequence for all calls.
        
        D = num_args + 1
        R14 = callee address
        stack: return address already pushed
        """
        
        label = self.asm.next_label("call_common")

        self.asm.start(f"call_common")
        self.asm.label(label)

        # R15 = SP - (D+1) (which will be the new ARG)
        self.asm.instr("@SP")
        self.asm.instr("D=M-D")
        self.asm.instr("@R15")
        self.asm.instr("M=D")

        # push four segment pointers:
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

        # JMP to R14 (the callee)
        self.asm.instr("@R14")
        self.asm.instr("A=M")
        self.asm.instr("0;JMP")
        return label

    def _return(self):
        label = self.asm.next_label("return_common")
        
        self.asm.start(f"return_common")
        self.asm.label(label)
        
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
        
        return label


def translate_line(translate, line):
    """Parse a line of VM source, and invoke a translator to handle it.
    
    Note: this is the absolutely the dumbest possible parser, not dealing with 
    """
    
    words = line.strip().split(' ')
    if len(words) == 0:
        pass
    elif words[0] == "function":
        c, f = words[1].split('.')
        translate.function(c, f, int(words[2]))
    elif words[0] == "call":
        c, f = words[1].split('.')
        translate.call(c, f, int(words[2]))
    elif words[0] in ("label", "goto", "if-goto"):
        translate.__getattribute__(words[0].replace('-', '_'))(words[1])
    elif words[0] in ("push", "pop"):
        name = '_'.join(words[:-1])
        index = int(words[-1])
        translate.__getattribute__(name)(index)
    elif len(words) == 1:
        if words[0] in ("and", "or", "not", "return"):
            translate.__getattribute__(words[0] + "_op")()
        else:
            translate.__getattribute__(words[0])()
    else:
        raise Exception(f"Unable to translate: {line}")
    
    