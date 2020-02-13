"""A more efficient VM translator for the book's CPU.

Uses a single trick: when an opcode is encountered, if the opcode pushes a value on to the stack, 
the value is simply left in D and the translator remembers that this was done. If the next opcode
consumes the top of the stack, it can usually generate a simpler sequence using the value from D.
Otherwise, the value is pushed and then the usual opcodes are emitted.

Note on debugging: this tends to make tracing hard to interpret, because whenever a stack operation
is omitted, the stack just looks wrong in the trace.
"""


from nand.translate import AssemblySource
from nand.solutions import solved_07


class Translator(solved_07.Translator):
    def __init__(self):
        self.asm = AssemblySource()
        
        solved_07.Translator.__init__(self, self.asm)
        
        self.top_in_d = False

    def finish(self):
        self._fix_stack()

    def push_constant(self, value):
        self._fix_stack()

        self.asm.start(f"push constant {value}")
        self.asm.instr(f"@{value}")
        self.asm.instr(f"D=A")
        self.top_in_d = True

    def lt(self):
        self._fix_stack()
        solved_07.Translator.lt(self)

    def eq(self):
        self._fix_stack()
        solved_07.Translator.eq(self)

    def gt(self):
        self._fix_stack()
        solved_07.Translator.gt(self)


    def _binary(self, opcode, op):
        if self.top_in_d:
            self.asm.start(opcode + " (from D)")
            self.asm.instr("@SP")
            self.asm.instr("AM=M-1")
            self.asm.instr(f"D={op}")
            # Note: this isn't really a win if the next instruction is going to just push. 
        else:
            solved_07.Translator._binary(self, opcode, op)

    def _unary(self, opcode, op):
        if self.top_in_d:
            self.asm.start(opcode + " (from D)")
            self.asm.instr(f"D={op.replace('M', 'D')}")
            # Note: and it stays in D
        else:
            solved_07.Translator._unary(self, opcode, op)

    def _pop_segment(self, segment_name, segment_ptr, index):
        # TODO: pull it from D for small args for sure
        # also for non-small by stashing D in R13?
        self._fix_stack()
        solved_07.Translator._pop_segment(self, segment_name, segment_ptr, index)

    def pop_temp(self, index):
        assert 0 <= index < 8
        if not self.top_in_d:  # Beautiful: only this conditional is added
            self.asm.start(f"pop temp {index}")
            self._pop_d()
        else:
            self.asm.start(f"pop temp {index} (from D)")
            self.top_in_d = False            
        self.asm.instr(f"@R{5+index}")
        self.asm.instr("M=D")

    def _push_segment(self, segment_name, segment_ptr, index):
        self._fix_stack()

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
        self.top_in_d = True
 
    def push_temp(self, index):
        assert 0 <= index < 8

        self._fix_stack()

        self.asm.start(f"push temp {index}")
        self.asm.instr(f"@R{5+index}")
        self.asm.instr("D=M")
        self.top_in_d = True


    def pop_pointer(self, index):
        if self.top_in_d:
            self.asm.start(f"pop pointer {index} (from D)")
            segment_ptr = ("THIS", "THAT")[index]
            self.asm.instr(f"@{segment_ptr}")
            self.asm.instr("M=D")
            self.top_in_d = False
        else:
            solved_07.Translator.pop_pointer(self, index)

    def push_pointer(self, index):
        self._fix_stack()
        
        self.asm.start(f"push pointer {index}")
        segment_ptr = ("THIS", "THAT")[index]
        self.asm.instr(f"@{segment_ptr}")
        self.asm.instr("D=M")
        self.top_in_d = True


    def _fix_stack(self):
        if self.top_in_d:
            self._push_d()
            self.top_in_d = False
