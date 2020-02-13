"""A more efficient VM translator for the book's CPU.

Uses a single trick: when an opcode is encountered, if the opcode pushes a value on to the stack, 
the value is simply left in D and the translator remembers that this was done. If the next opcode
consumes the top of the stack, it can usually generate a simpler sequence using the value from D.
Otherwise, the value is pushed and then the usual opcodes are emitted.
"""


from nand.translate import AssemblySource
from nand.solutions import solved_07


class Translator(solved_07.Translator):
    def __init__(self):
        self.asm = AssemblySource()
        
        solved_07.Translator.__init__(self, self.asm)
        
        self.top_in_d = False
    
    def push_constant(self, value):
        self._fix_stack()

        self.asm.start(f"push constant {value}")
        self.asm.instr(f"@{value}")
        self.asm.instr(f"D=A")
        self.top_in_d = True


    def add(self):
        if self.top_in_d:
            self.asm.start(f"add")
            self.asm.instr("@SP")
            self.asm.instr("A=M-1")
            self.asm.instr("M=D+M")
        else:
            solved_07.Translator.add(self)

    def _fix_stack(self):
        if self.top_in_d:
            self._push_d()
            self.top_in_d = False
