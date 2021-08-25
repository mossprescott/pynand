"""Solutions for projects 07 and 08.

SPOILER ALERT: this files contains a complete VM translator.
If you want to write this on your own, stop reading now!
"""

import re

from nand.translate import AssemblySource

class Translator:
    """Translate all VM opcodes to assembly instructions.

    Note: this implementation is not broken out into separate classes for projects 07 and 08.
    """

    def __init__(self, asm=None):
        self.asm = asm if asm else AssemblySource()
        self.class_namespace = "static"
        self.function_namespace = "_"

        self.defined_functions = []
        self.referenced_functions = []
        self.last_function_start = None

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


    def handle(self, op):
        """Dispatch to the handler for an opcode, in the form of a tuple (op_name, [args])."""

        op_name, args = op
        self.__getattribute__(op_name)(*args)


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
        self._binary("add", "D+M")

    def sub(self):
        self._binary("sub", "M-D")

    def neg(self):
        self._unary("neg", "-M")

    def and_op(self):
        self._binary("and", "D&M")

    def or_op(self):
        self._binary("or", "D|M")

    def not_op(self):
        self._unary("not", "!M")

    def eq(self):
        # A short sequence that jumps to the common impl and returns, which costs only 4 instructions
        # per ocurrence as opposed to about 11. On the other hand, this is 20 instructions at runtime.
        return_label = self.asm.next_label("eq_return")
        self.asm.start("eq")
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{self.eq_label}")
        self.asm.instr("0;JMP")
        self.asm.label(return_label)

    def lt(self):
        # A short sequence that jumps to the common impl and returns, which costs only 4 instructions
        # per ocurrence as opposed to about 11. On the other hand, this is 20 instructions at runtime.
        return_label = self.asm.next_label("lt_return")
        self.asm.start("lt")
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{self.lt_label}")
        self.asm.instr("0;JMP")
        self.asm.label(return_label)

    def gt(self):
        # A short sequence that jumps to the common impl and returns, which costs only 4 instructions
        # per ocurrence as opposed to about 11. On the other hand, this is 20 instructions at runtime.
        return_label = self.asm.next_label("gt_return")
        self.asm.start("gt")
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self.asm.instr(f"@{self.gt_label}")
        self.asm.instr("0;JMP")
        self.asm.label(return_label)

    def pop_local(self, index):
        self._pop_segment("local", "LCL", index)

    def pop_argument(self, index):
        self._pop_segment("argument", "ARG", index)

    def pop_this(self, index):
        self._pop_segment("this", "THIS", index)

    def pop_that(self, index):
        self._pop_segment("that", "THAT", index)

    def pop_temp(self, index):
        assert 0 <= index < 8
        self.asm.start(f"pop temp {index}")
        self._pop_d()
        self.asm.instr(f"@R{5+index}")
        self.asm.instr("M=D")

    def _pop_segment(self, segment_name, segment_ptr, index):
        self.asm.start(f"pop {segment_name} {index}")
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
        return self._push_segment("local", "LCL", index)

    def push_argument(self, index):
        return self._push_segment("argument", "ARG", index)

    def push_this(self, index):
        return self._push_segment("this", "THIS", index)

    def push_that(self, index):
        return self._push_segment("that", "THAT", index)

    def _push_segment(self, segment_name, segment_ptr, index):
        self.asm.start(f"push {segment_name} {index}")
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


    def push_temp(self, index):
        assert 0 <= index < 8
        self.asm.start(f"push temp {index}")
        self.asm.instr(f"@R{5+index}")
        self.asm.instr("D=M")
        self._push_d()


    def pop_pointer(self, index):
        self.asm.start(f"pop pointer {index}")
        segment_ptr = ("THIS", "THAT")[index]
        self._pop_d()
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("M=D")

    def push_pointer(self, index):
        self.asm.start(f"push pointer {index}")
        segment_ptr = ("THIS", "THAT")[index]
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("D=M")
        self._push_d()


    def pop_static(self, index):
        self.asm.start(f"pop static {index}")
        self._pop_d()
        self.asm.instr(f"@{self.class_namespace}.static{index}")
        self.asm.instr("M=D")

    def push_static(self, index):
        self.asm.start(f"push static {index}")
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
        # if self.last_function_start is not None:
        #     instrs = self.asm.instruction_count - self.last_function_start
        #     print(f"  {self.function_namespace} instructions: {instrs}")
        self.last_function_start = self.asm.instruction_count

        self.defined_functions.append(f"{class_name}.{function_name}")

        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{function_name}"

        self.asm.start(f"function {class_name}.{function_name} {num_vars}")
        self.asm.label(f"{self.function_namespace}")

        if num_vars == 0:
            # Note: a lot of functions have no locals, so skipping this has some impact.
            # Tricky: this instruction has no effect; it's just here to take up space in the ROM and ensure that the
            # "function" op has a unique address assigned to it, so that it can appear in tracing and profiling. Yes,
            # that is dumb.
            self.asm.instr("0")
        elif num_vars == 1:
            # 5 instr.
            self.asm.instr("@SP")
            self.asm.instr("A=M")
            self.asm.instr("M=0")
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
        elif num_vars == 2:
            # 8 instr.
            self.asm.instr("@SP")
            self.asm.instr("A=M")
            self.asm.instr("M=0")
            self.asm.instr("A=A+1")
            self.asm.instr("M=0")
            self.asm.instr("@SP")
            self.asm.instr("M=M+1")
            self.asm.instr("M=M+1")
        else:
            # 5 + 2*(num_vars) instr.
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
        self.referenced_functions.append(f"{class_name}.{function_name}")

        # Note: this is currently 13 instructions per occurrence, which is pretty heavy.
        # Can it be shrunk more? Move more work into the common impl somehow?

        return_label = self.asm.next_label("RET_ADDRESS_CALL")

        self.asm.start(f"call {class_name}.{function_name} {num_args}")

        # Push the return address
        # Note: could save 2 instrs here by stashing it in R13, but then the common code
        # sequence would be longer and take more cycles, so not worth it?
        self.asm.instr(f"@{return_label}")
        self.asm.instr("D=A")
        self._push_d()

        # R14 = callee address
        self.asm.instr(f"@{class_name.lower()}.{function_name}")
        self.asm.instr("D=A")
        self.asm.instr("@R14")
        self.asm.instr("M=D")

        # D = num_args
        if num_args <= 1:
            self.asm.instr(f"D={num_args}")
        else:
            self.asm.instr(f"@{num_args}")
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

        self.call("Sys", "init", 0)
        # self.asm.instr("@Sys.init")
        # self.asm.instr("0;JMP")


    def _compare(self, op):
        # TODO: this is almost certainly wrong for signed values where the difference overflows, though:
        #    -30,000 > 30,000
        #    30,000 - (-30,000) = 60,000 = -whatever, which is less than 0

        # Common implementation for compare opcodes:
        label = self.asm.next_label(f"{op.lower()}_common")
        end_label = self.asm.next_label(f"{op.lower()}_common$end")
        # self.asm.start(f"{op.lower()}_common")  # usually don't want to see this detail in traces
        self.asm.label(label)
        self.asm.instr("@R15")    # R15 = D (the return address)
        self.asm.instr("M=D")

        # D = top, M = second from top, SP -= 1 (not 2!)
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")
        self.asm.instr("D=M")
        self.asm.instr("A=A-1")

        # Compare
        self.asm.instr("D=M-D")

        # Set result True, optimistically (since A is already loaded with the destination)
        self.asm.instr("M=-1")  # note: true == -1 (all bits set)

        self.asm.instr(f"@{end_label}")
        self.asm.instr(f"D;J{op}")

        # Set result False
        self.asm.instr("@SP")
        self.asm.instr("A=M-1")
        self.asm.instr("M=0")

        self.asm.label(end_label)
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

    def _binary(self, opcode, op):
        """Pop two, combine, and push, but update SP only once."""
        self.asm.start(opcode)
        self.asm.instr("@SP")
        self.asm.instr("AM=M-1")  # update SP
        self.asm.instr("D=M")     # D = top
        self.asm.instr("A=A-1")   # Don't update SP again

        self.asm.instr(f"M={op}")

    def _unary(self, opcode, op):
        """Modify the top item on the stack without updating SP."""
        self.asm.start(opcode)
        self.asm.instr("@SP")
        self.asm.instr("A=M-1")
        self.asm.instr(f"M={op}")

    def _call(self):
        """Common sequence for all calls.

        D = num_args
        R14 = callee address
        stack: return address already pushed
        """

        label = self.asm.next_label("call_common")

        # self.asm.start(f"call_common")
        self.asm.label(label)

        # R15 = SP - (D + 1) (which will be the new ARG)
        self.asm.instr("@SP")
        self.asm.instr("D=M-D")
        self.asm.instr("D=D-1")
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

        # self.asm.start(f"return_common")
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


    def finish(self):
        """Called after all opcodes are processed, in case the translator needs to say any last words."""
        pass


    def rewrite_ops(self, ops):
        """Rewrite patterns of ops for which a more efficient sequence is available, say by
        using an op that isn't part of the VM's external specification.

        Expected to be called with large, coherent chunks of ops; at least an entire function
        at a time, or maybe a file at a time.
        """

        return ops


    def check_references(self):
        """Check for obvious "linkage" errors: e.g. functions that are referenced but never defined.
        """

        defined = set(self.defined_functions)
        referenced = set(self.referenced_functions)

        assert len(self.defined_functions) == len(defined), "Each function is defined only once"

        unresolved = referenced - defined
        assert unresolved == set(), f"Unresolved references: {unresolved}"


def parse_line(line):
    """Parse a line into a tuple (op_code, [args]).

    Note: this is absolutely the dumbest possible parser, not doing any real validation or
    imposing any structure at all, but munging the input into a shape that fits Translator.
    """

    m = re.match(r"([^/]*)(?://.*)?", line)
    if m:
        string = m.group(1).strip()
    else:
        string = line.strip()

    words = string.split()

    if not words:
        return None
    elif words[0] == "function":
        c, f = words[1].split('.')
        return "function", (c, f, int(words[2]),)
    elif words[0] == "call":
        c, f = words[1].split('.')
        return "call", (c, f, int(words[2]),)
    elif words[0] in ("label", "goto", "if-goto"):
        return words[0].replace('-', '_'), (words[1],)
    elif words[0] in ("push", "pop"):
        name = '_'.join(words[:-1])
        index = int(words[-1])
        return name, (index,)
    elif len(words) == 1:
        if words[0] in ("and", "or", "not", "return"):
            return words[0] + "_op", ()
        else:
            return words[0], ()
    else:
        raise Exception(f"Unable to translate: {line}")
