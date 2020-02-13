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

    def _fix_stack(self):
        if self.top_in_d:
            self._push_d()
            self.top_in_d = False
