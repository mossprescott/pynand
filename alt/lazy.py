"""A more efficient VM translator for the book's CPU.

Uses a single trick: when an opcode is encountered, if the opcode pushes a value on to the stack, 
the value is simply left in D and the translator remembers that this was done. If the next opcode
consumes the top of the stack, it can usually generate a simpler sequence using the value from D.
Otherwise, the value is pushed and then the usual opcodes are emitted.

Note on debugging: this tends to make tracing hard to interpret, because whenever a stack operation
is omitted, the stack just looks wrong in the trace.
"""


from nand.translate import AssemblySource, translate_dir
from nand.solutions import solved_05, solved_06, solved_07


class Translator(solved_07.Translator):
    def __init__(self):
        self.asm = AssemblySource()
        
        solved_07.Translator.__init__(self, self.asm)
        
        self.top_in_d = False

    def finish(self):
        self._fix_stack()

    def push_constant(self, value):
        self._fix_stack()

        # TODO: this is _costing_ one instruction when the following instr. can't take it 
        # from D, by doing D=0/1 ... M=D instead of folding the constant in.
        self.asm.start(f"push constant {value}")
        if value <= 1:
            self.asm.instr(f"D={value}")
        else:
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
        # Believe it or not, using this unrolled loop for indexes all the way to 13
        # makes the code smaller overall (empirically determined.)
        if self.top_in_d and index <= 13:
            self.asm.start(f"pop {segment_name} {index} (from D)")
            self.asm.instr(f"@{segment_ptr}")
            if index == 0:
                self.asm.instr("A=M")
            else:
                self.asm.instr("A=M+1")
                for _ in range(index-1):
                    self.asm.instr("A=A+1")
            self.asm.instr("M=D")
            self.top_in_d = False
        else:
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


    def pop_static(self, index):
        if self.top_in_d:
            self.asm.start(f"push static {index} (from D)")
            self.asm.instr(f"@{self.class_namespace}.static{index}")
            self.asm.instr("M=D")
            self.top_in_d = False
        else:
            solved_07.Translator.pop_static(self, index)
        
    def push_static(self, index):
        self._fix_stack()

        self.asm.start(f"push static {index}")
        self.asm.instr(f"@{self.class_namespace}.static{index}")
        self.asm.instr("D=M")
        self.top_in_d = True


    def label(self, name):
        self._fix_stack()
        solved_07.Translator.label(self, name)

    def if_goto(self, name):
        if self.top_in_d:
            self.asm.start(f"if-goto {name} (from D)")
            self.asm.instr(f"@{self.function_namespace}${name}")
            self.asm.instr("D;JNE")
            self.top_in_d = False
        else:
            solved_07.Translator.if_goto(self, name)

    def goto(self, name):
        self._fix_stack()
        solved_07.Translator.goto(self, name)


    def function(self, class_name, function_name, num_vars):
        assert not self.top_in_d
        solved_07.Translator.function(self, class_name, function_name, num_vars)

    def return_op(self):
        # TODO: an alt. return handler?
        self._fix_stack()
        solved_07.Translator.return_op(self)

    def call(self, class_name, function_name, num_args):
        self._fix_stack()
        solved_07.Translator.call(self, class_name, function_name, num_args)


    def _fix_stack(self):
        if self.top_in_d:
            self._push_d()
            self.top_in_d = False



if __name__ == "__main__":
    TRACE = False

    import sys
    import computer

    translate = Translator()
    
    translate.preamble()
    
    translate_dir(translate, solved_07.parse_line, sys.argv[1])
    translate_dir(translate, solved_07.parse_line, "nand2tetris/tools/OS")  # HACK not committed
    
    if TRACE:
        for instr in translate.asm:
            print(instr)

    computer.run(solved_06.assemble(translate.asm), chip=solved_05.Computer, src_map=translate.asm.src_map if TRACE else None)


