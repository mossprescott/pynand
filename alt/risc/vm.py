#! /usr/bin/env python3

"""Translator for the standard VM, generating RiSC assembly.

SP, LCL, ARG, THIS, and THAT are stored in r1-r5.
r6 and r7 are used as temporary locations for everything else.

In `call`, the return address is stored in r7 (and then copied to the stack
durinfg `function`.)

Effectively, this is going to look like the standard VM for the HACK CPU,
just with the five pointers mapped into registers. Coincidentally, that leaves
the same number of registers for scratch use, except r6 and r7 aren't limited
the way A and D are.

This something like 30% smaller in ROM than the similar translation for HACK,
mostly because it takes only two cycles to push/pop the stack.
"""

# from nand import jack_ast
from nand.platform import BUNDLED_PLATFORM
from nand.translate import AssemblySource
# from nand.solutions import solved_07

# import alt.reg as compiler
import alt.risc.asm
import alt.risc.chip


# Each register is assigned a specific role, and gets a symbolic name
Z = "r0"  # just a name for zero, for consistency. Bad idea?
SP = "r1"
LCL = "r2"
ARG = "r3"
THIS = "r4"
THAT = "r5"
X = "r6"
Y = "r7"

# Low-memory "registers":
G0 = 13
G1 = 14
G2 = 15

class Translator:
    def __init__(self):
        self.asm = AssemblySource()
        self.defined_functions = []
        self.referenced_functions = []

        # If true, emit extra code to make debug traces more useful:
        self.debug = True

    def push_constant(self, value):
        self.asm.start(f"push constant {value}")

        if -64 <= value <= 63:
            self.asm.instr(f"addi {X} {Z} {value}")
        else:
            self.asm.instr(f"lui {X} {value & ~0x3F}")
            self.asm.instr(f"addi {X} {X} {value & 0x3F}")
        self._push(X)

    def push_local(self, index):
        self._push_segment("local", LCL, index)

    def push_argument(self, index):
        self._push_segment("argument", ARG, index)

    def push_this(self, index):
        self._push_segment("this", THIS, index)

    def push_that(self, index):
        self._push_segment("that", THAT, index)

    def _push_segment(self, segment_name, segment_ptr, index):
        self.asm.start(f"push {segment_name} {index}")
        if 0 <= index <= 63:
            self.asm.instr(f"lw {X} {segment_ptr} {index}")
            self._push(X)
        else:
            self.asm.comment("TODO and/or fail")

    def push_pointer(self, index):
        self.asm.start(f"push pointer {index}")

        if index == 0:
            src = THIS
        elif index == 1:
            src = THAT
        else:
            raise Exception(f"Unexpected index for pointer: {index}")

        self._push(src)

    def push_static(self, index):
        self.asm.start(f"push static {index}")

        label = f"@{self.class_namespace}.static{index}"


        self.asm.comment("HACK: embed a reference to the static to get the assembler to allocate for it.")
        self.asm.instr(f"beq {Z} {Z} +1")
        self.asm.instr(f"{label}")

        self.asm.instr(f"lui {Y} {label}")
        self.asm.instr(f"lli {Y} {label}")
        self.asm.instr(f"lw {X} {Y} 0")
        self._push(X)


    def _push(self, src):
        self.asm.instr(f"sw {src} {SP} 0")
        self.asm.instr(f"addi {SP} {SP} 1")

    def _poke(self, src):
        """Overwrite the value at the top of the stack."""
        self.asm.instr(f"sw {src} {SP} -1")


    def pop_local(self, index):
        self._pop_segment("local", LCL, index)

    def pop_argument(self, index):
        self._pop_segment("argument", ARG, index)

    def pop_this(self, index):
        self._pop_segment("this", THIS, index)

    def pop_that(self, index):
        self._pop_segment("that", THAT, index)

    def _pop_segment(self, segment_name, segment_ptr, index):
        self.asm.start(f"pop {segment_name} {index}")
        if 0 <= index <= 63:
            self._pop(X)
            self.asm.instr(f"sw {X} {segment_ptr} {index}")
        else:
            self.asm.comment("TODO and/or fail")

    def pop_static(self, index):
        self.asm.start(f"pop static {index}")

        label = f"@{self.class_namespace}.static{index}"

        self.asm.comment("HACK: embed a reference to the static to get the assembler to allocate for it.")
        self.asm.instr(f"beq {Z} {Z} +1")
        self.asm.instr(f"{label}")

        self._pop(X)
        self.asm.instr(f"lui {Y} {label}")
        self.asm.instr(f"lli {Y} {label}")
        self.asm.instr(f"sw {X} {Y} 0")

    def pop_pointer(self, index):
        self.asm.start(f"pop pointer {index}")

        if index == 0:
            dest = THIS
        elif index == 1:
            dest = THAT
        else:
            raise Exception(f"Unexpected index for pointer: {index}")

        self._pop(dest)

    def pop_temp(self, index):
        assert 0 <= index < 8
        self.asm.start(f"pop temp {index}")

        self._pop(X)
        self.asm.instr(f"sw {X} {Z} {5+index}")


    def _pop(self, dest):
        self.asm.instr(f"addi {SP} {SP} -1")
        self.asm.instr(f"lw {dest} {SP} 0")

    def _peek(self, dest):
        """Get the value at the top of the stack, without adjusting SP."""
        self.asm.instr(f"lw {dest} {SP} -1")


    def add(self):
        self.asm.start("add")

        # rhs:
        self._pop(Y)

        # add to top of stack (without adjusting SP)
        self._peek(X)
        self.asm.instr(f"add {X} {X} {Y}")
        self._poke(X)

    def sub(self):
        self.asm.start("sub")

        # pop the rhs and negate it:
        self._pop(Y)
        self._neg(Y)

        # add to top of stack (without adjusting SP)
        self._peek(X)
        self.asm.instr(f"add {X} {X} {Y}")
        self._poke(X)

    def and_op(self):
        self.asm.start("and")

        # pop the rhs:
        self._pop(Y)

        # get lhs from top of stack (without adjusting SP)
        self._peek(X)

        self.asm.instr(f"nand {X} {X} {Y}")
        self.asm.instr(f"nand {X} {X} {X}")

        self._poke(X)

    def or_op(self):
        self.asm.start("or")

        # pop the rhs:
        self._pop(Y)
        self.asm.instr(f"nand {Y} {Y} {Y}")  # y = not(rhs)

        # get lhs from top of stack (without adjusting SP)
        self._peek(X)
        self.asm.instr(f"nand {X} {X} {X}")  # x = not(lhs)

        self.asm.instr(f"nand {X} {X} {Y}")  # x = not(and(not(lhs), not(rhs)))

        self._poke(X)

    def eq(self):
        self.asm.start("eq")

        # pop the rhs:
        self._pop(Y)

        # get lhs from top of stack (without adjusting SP)
        self._peek(X)

        # Note: two branches, because don't have a spare register
        self.asm.instr(f"beq {X} {Y} +2")   # skip false case

        self.asm.instr(f"add {Y} {Z} {Z}")  # result = 0
        self.asm.instr(f"beq {Z} {Z} +1")   # skip true case

        self.asm.instr(f"addi {Y} {Z} -1")  # result = -1

        self._poke(Y)

    def lt(self):
        self.asm.start("lt")

        # pop the rhs and negate it:
        self._pop(Y)
        self._neg(Y)

        # get lhs from top of stack (without adjusting SP)
        self._peek(X)
        self.asm.instr(f"add {X} {X} {Y}")

        # Y = 0x8000; X = X & Y
        self.asm.instr(f"lui {Y} -32768")
        self.asm.instr(f"nand {X} {X} {Y}")
        self.asm.instr(f"nand {X} {X} {X}")

        self.asm.instr(f"add {Y} {Z} {Z}")  # result = 0 unless overwritten
        self.asm.instr(f"beq {X} {Z} +1")   # sign bit not set: >= 0
        self.asm.instr(f"addi {Y} {Z} -1")  # result = -1

        self._poke(Y)

    def gt(self):
        self.asm.start("gt")

        # pop the rhs and negate it:
        self._pop(Y)

        # get lhs from top of stack (without adjusting SP)
        self._peek(X)
        self._neg(X)
        self.asm.instr(f"add {X} {X} {Y}")

        # Y = 0x8000; X = X & Y
        self.asm.instr(f"lui {Y} -32768")
        self.asm.instr(f"nand {X} {X} {Y}")
        self.asm.instr(f"nand {X} {X} {X}")

        self.asm.instr(f"add {Y} {Z} {Z}")  # result = 0 unless overwritten
        self.asm.instr(f"beq {X} {Z} +1")   # sign bit not set: >= 0
        self.asm.instr(f"addi {Y} {Z} -1")  # result = -1

        self._poke(Y)

    def neg(self):
        self.asm.start("neg")

        # load/negate/store, without adjusting the stack pointer
        self._peek(X)
        self._neg(X)
        self._poke(X)

    def _neg(self, reg):
        """Negate the value in a register (in-place)."""
        self.asm.instr(f"nand {reg} {reg} {reg}")
        self.asm.instr(f"addi {reg} {reg} 1")

    def not_op(self):
        self.asm.start("not")

        # load/not/store, without adjusting the stack pointer
        self._peek(X)
        self.asm.instr(f"nand {X} {X} {X}")
        self._poke(X)

    def label(self, name):
        self.asm.start(f"label {name}")
        self.asm.label(f"{self.function_namespace}${name}")

    def goto(self, name):
        self.asm.start(f"goto {name}")

        dest = f"@{self.function_namespace}${name}"

        # Note: always use jalr (discarding the return address), with two-cycle address load,
        # because a simple "beq" will fail if the target is more than 63 words away.
        self.asm.instr(f"lui {X} {dest}")
        self.asm.instr(f"lli {X} {dest}")
        self.asm.instr(f"jalr {Z} {X}")

    def if_goto(self, name):
        self.asm.start(f"if-goto {name}")

        dest = f"@{self.function_namespace}${name}"

        self._pop(Y)
        self.asm.instr(f"beq {Y} {Z} +3")

        # Note: always use jalr (discarding the return address), with two-cycle address load,
        # because a simple "beq" will fail if the target is more than 63 words away.
        self.asm.instr(f"lui {X} {dest}")
        self.asm.instr(f"lli {X} {dest}")
        self.asm.instr(f"jalr {Z} {X}")


    def function(self, class_name, function_name, num_vars):
        self.last_function_start = self.asm.instruction_count

        self.defined_functions.append(f"{class_name}.{function_name}")

        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{function_name}"

        self.asm.blank()
        self.asm.start(f"function {class_name}.{function_name} {num_vars}")
        self.asm.label(f"{self.function_namespace}")

        self.asm.comment("store the return address before the segment pointers")
        self.asm.instr(f"sw {Y} {SP} -5")

        self.asm.comment(f"reserve space for {num_vars}")
        for _ in range(num_vars):
            # TODO: one cycle per var, plus one to update SP
            self._push(Z)

    def call(self, class_name, function_name, num_args):
        # 7 cycles for the mostly common sequence, then 3 for the jump
        self.referenced_functions.append(f"{class_name}.{function_name}")

        self.asm.start(f"call {class_name}.{function_name} {num_args}")

        self.asm.comment("Note: return address gets stashed at SP, but after the jalr")
        self.asm.instr(f"sw {LCL} {SP} +1")
        self.asm.instr(f"sw {ARG} {SP} +2")
        self.asm.instr(f"sw {THIS} {SP} +3")
        self.asm.instr(f"sw {THAT} {SP} +4")
        self.asm.instr(f"addi {SP} {SP} 5")
        self.asm.comment("LCL = SP")
        self.asm.instr(f"add {LCL} {SP} {Z}")
        self.asm.comment(f"ARG = SP - (5 + {num_args} args)")
        self.asm.instr(f"addi {ARG} {SP} {-(5 + num_args)}")  # ???!!

        if self.debug:
            self.asm.comment("write LCL and ARG to memory for debugging")
            self.asm.instr(f"sw {LCL} r0 1")
            self.asm.instr(f"sw {ARG} r0 2")

        # two cycles to load the destination, always:
        dest = f"@{class_name.lower()}.{function_name}"
        self.asm.instr(f"lui {X} {dest}")
        self.asm.instr(f"lli {X} {dest}")
        self.asm.instr(f"jalr {Y} {X}")

    def return_op(self):
        # Note: if there were no arguments, then the return address is saved at the same location
        # where the return value will be stored, so have to take care not to overwrite it.

        self.asm.start("return")

        self.asm.comment("adjust stack/restore pointers")


        # (somewhat lamely) stash the return value in G2:
        self.asm.instr(f"lw {X} {SP} -1")
        self.asm.instr(f"sw {X} {Z} {G2}")

        # stash caller's SP (ARG)
        self.asm.instr(f"addi {X} {ARG} 0")

        # restore LCL, ARG, THIS, THAT:
        self.asm.instr(f"add {SP} {LCL} {Z}")
        self.asm.instr(f"lw {THAT} {SP} -1")
        self.asm.instr(f"lw {THIS} {SP} -2")
        self.asm.instr(f"lw {ARG} {SP} -3")
        self.asm.instr(f"lw {LCL} {SP} -4")

        if self.debug:
            self.asm.comment("write LCL and ARG to memory for debugging")
            self.asm.instr(f"sw {LCL} r0 1")
            self.asm.instr(f"sw {ARG} r0 2")

        # stash the return address:
        self.asm.instr(f"lw {Y} {SP} -5")

        # reset the caller's stack pointer (plus space for the return value):
        self.asm.instr(f"addi {SP} {X} 1")

        # copy return value to top of adjusted stack
        self.asm.instr(f"lw {X} {Z} {G2}")
        self.asm.instr(f"sw {X} {SP} -1")

        self.asm.instr(f"jalr {Z} {Y}")


    def handle(self, op):
        op_name, args = op
        self.__getattribute__(op_name)(*args)

    def preamble(self):
        self.asm.start("VM initialization")

        self.asm.instr(f"lui {SP} 256")
        self.call("Sys", "init", 0)

    def finish(self):
        pass

    def rewrite_ops(self, ops):
        return ops

    def check_references(self):
        # Probably don't use this translator to validate your compiler
        pass



RiSC_VM_PLATFORM = BUNDLED_PLATFORM._replace(
    chip=alt.risc.chip.RiSCComputer,
    assemble=alt.risc.asm.assemble,
    translator=Translator)

if __name__ == "__main__":
    # Note: this import requires pygame; putting it here allows the tests to import the module
    import computer

    computer.main(RiSC_VM_PLATFORM)
