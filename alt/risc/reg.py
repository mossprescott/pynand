#! /usr/bin/env python3

"""Alternative compiler targeting RiSC-16.

Uses most of the same "front end" as `alt/reg.py`.


# Registers:

Locals are allocated to registers as follows:
- r1: SP
- r2-r5: the first 4 transient local variables
- r6: scratch values
- r7: scratch values and return addresses during subroutine calls
- RAM[5-12]: the next 8 transient local variables

The LCL and ARG segment pointers are stored in RAM[1] and RAM[2] as usual.
THIS and THAT are not used.

The code generator has to deal with targeting either a true register or a low-memory "register"
for every kind of primitive. Reading or writing a low-mem register always adds a single lw/sw
instruction. Nevertheless, it seems simpler to deal with both cases during code generation,
as opposed to trying to make the compiler know about two different kinds of Locals with
different access rules. We assume that register allocation does something reasonably intelligent
with the list of registers (e.g. allocate as many temps as possible to the first registers in
the list); in fact it's not that smart, but it does the right thing much of the time.

Note: accessing a value in the "local" and "argument" segments takes two instructions, because
the segment pointers are kept in RAM.

An alternative to store LCL in r2, which would make accessing the "local" segment just as efficient
as accessing low memory (basically, you index off r2 instead of r0). But that would leave one less
register for temporaries, and we're already pretty tight.


# Branches and jumps:

RiSC-16's beq instruction is *less* flexible than HACK's JMP:
- it can only compare values for equality
- it can only target instructions within +/- 64 locations
- on the other hand, it can compare two arbitrary register for equality

Every conditional branch turns into a beq that conditionally skips over a 3-cycle jalr to the
actual target:
    beq <value> r0 +3  # value is non-zero if the jump should be taken
    lui r7 @target
    lli r7 @target
    jalr r0 r7
"""

from typing import Optional

from nand import jack_ast
from nand.platform import BUNDLED_PLATFORM
from nand.translate import AssemblySource
from nand.solutions import solved_07

import alt.reg as compiler
import alt.risc.asm
import alt.risc.chip

# Flags to generate bigger/dumber code that's easier to debug. Turn them all off for the best
# possible performance.
ONLY_MEM_REGISTERS = False
EXTRA_DEBUG_CODE = False

FIRST_LOCAL_REG = 2
if ONLY_MEM_REGISTERS:
    # put everything in memory for debugging
    NUM_LOCAL_REGS = 0
else:
    NUM_LOCAL_REGS = 4

FIRST_MEM_REG = 5  # Note: could start at 3, since THIS/THAT are unused
NUM_MEM_REGS = 8  # Note: could go as high as maybe RAM[15]

SP = "r1"
LCL_ADDR = 1  # same as @LCL, but known to be < 64 and the assembler doesn't handle symbols in lw/sw
ARG_ADDR = 2  # same as @ARG
TEMP1 = "r6"
TEMP2 = "r7"

MIN_STATIC = 16
MAX_STATIC = 255

class RiSCCompiler(compiler.Compiler):
    def __init__(self):
        # Note: "r" means a true register, "R" is a low-memory temp location. That's
        # potentially confusing, but these are the conventions for the assembler and
        # the debugger.
        self.registers = (
            [compiler.Reg(i+FIRST_LOCAL_REG, "r", "?") for i in range(NUM_LOCAL_REGS)]
            + [compiler.Reg(i+FIRST_MEM_REG, "R", "?") for i in range(NUM_MEM_REGS)])


class Translator(solved_07.Translator):
    def __init__(self):
        self.asm = AssemblySource()
        # solved_07.Translator.__init__(self, self.asm)

        # If true, emit extra instructions that make it easier to see what's going on
        # in the simulator:
        self.debug = EXTRA_DEBUG_CODE

        # self.asm = asm if asm else AssemblySource()
        self.class_namespace = "static"
        self.function_namespace = "_"

        self.defined_functions = []
        self.referenced_functions = []
        self.last_function_start = None

        # Location in memory of the first static variable for the current class.
        # Need to track this here because the assembler's resolution of undefined labels doesn't
        # handle the RiSC-16 instruction format:
        self.static_base = MIN_STATIC

        # HACK: some code that's always required, even when preamble is not used.

        start_label = self.asm.next_label("start")
        self.asm.instr(f"lui {TEMP1} @{start_label}")
        self.asm.instr(f"lli {TEMP1} @{start_label}")
        self.asm.instr(f"jalr r0 {TEMP1}")
        self.asm.blank()

        # "Microcoded" instructions:
        # self.eq_label = self._compare("EQ")
        # self.lt_label = self._compare("LT")
        # self.gt_label = self._compare("GT")
        self.return_label = self._return()
        # self.call_label = self._call()

        self.asm.blank()
        self.asm.label(start_label)

    def handle(self, op):
        """Override for compatibility: an "op" in this context is an entire Class in the IR form."""
        self.translate_class(op)

    def translate_class(self, class_ast: compiler.Class):
        for s in class_ast.subroutines:
            self.translate_subroutine(s, class_ast.name)

        self.static_base += class_ast.num_statics

    def translate_subroutine(self, subroutine_ast: compiler.Subroutine, class_name: str):
        # print(subroutine_ast)

        # if self.last_function_start is not None:
        #     instrs = self.asm.instruction_count - self.last_function_start
        #     print(f"  {self.function_namespace} instructions: {instrs}")
        self.last_function_start = self.asm.instruction_count

        self.defined_functions.append(f"{class_name}.{subroutine_ast.name}")

        self.class_namespace = class_name.lower()
        self.function_namespace = f"{class_name.lower()}.{subroutine_ast.name}"

        instr_count_before = self.asm.instruction_count

        self.asm.start(f"function {class_name}.{subroutine_ast.name} {subroutine_ast.num_vars} (args: {subroutine_ast.num_args})")
        self.asm.label(f"{self.function_namespace}")

        # Note: this could be done with a common sequence in the preamble, but jumping there and
        # back would cost at least 6 cycles or so, and the goal here is to get small by generating
        # tighter code, not save space in ROM by adding runtime overhead.
        # TODO: avoid this overhead entirely for leaf functions, by just not adjusting the stack
        # at all.
        # self.asm.comment("push the return address, then LCL and ARG")
        self.asm.instr(f"sw {TEMP2} {SP} 0")
        self.asm.instr(f"lw {TEMP1} r0 {LCL_ADDR}")
        self.asm.instr(f"sw {TEMP1} {SP} +1")
        self.asm.instr(f"lw {TEMP1} r0 {ARG_ADDR}")
        self.asm.instr(f"sw {TEMP1} {SP} +2")
        self.asm.instr(f"addi {SP} {SP} 3")  # collapsed stack adjustment

        # self.asm.comment("LCL (RAM[1]) = SP (r1)")
        self.asm.instr(f"sw {SP} r0 {LCL_ADDR}")

        # self.asm.comment("ARG (RAM[2]) = SP (r1) - (num_args + 3)")
        self.asm.instr(f"addi {TEMP1} {SP} {-(subroutine_ast.num_args + 3)}")
        self.asm.instr(f"sw {TEMP1} r0 {ARG_ADDR}")

        if subroutine_ast.num_vars == 0:
            pass
        elif subroutine_ast.num_vars <= 63:
            # self.asm.comment(f"space for locals ({subroutine_ast.num_vars})")
            for i in range(subroutine_ast.num_vars):
                self.asm.instr(f"sw r0 {SP} +{i}")
            self.asm.instr(f"addi {SP} {SP} {subroutine_ast.num_vars}")  # collapsed stack adjustment
        else:
            raise Exception(f"Too many local variables: {subroutine_ast}")

        # Now the body:
        for s in subroutine_ast.body:
            self._handle(s)
        self.asm.blank()

        instr_count_after = self.asm.instruction_count

        # print(f"Translated {class_name}.{subroutine_ast.name}; instructions: {instr_count_after - instr_count_before:,d}")


    def handle_Eval(self, ast: compiler.Eval):
        assert isinstance(ast.dest, compiler.Reg)

        # TODO: lots of fancy optimization for various cases...

        if not isinstance(ast.expr, compiler.CallSub):
            self.asm.start(f"eval-{self.describe_expr(ast.expr)} {compiler._Stmt_str(ast)}")

        # TODO: when dest is a true register, assemble the result there direcly
        value_reg = self._handle_Expr(ast.expr)

        if self.debug:
            self.asm.comment("DEBUG: copy result to R15")
            self.asm.instr(f"sw {value_reg} r0 15")

        if isinstance(ast.expr, compiler.CallSub):
            self.asm.start(f"eval-result {compiler._Expr_str(ast.dest)} = <result>")

        if ast.dest.kind == "r":
            self.asm.instr(f"addi r{ast.dest.idx} {value_reg} 0")  # move result to destination register (somewhat wastefully)
        elif ast.dest.kind == "R":
            self.asm.instr(f"sw {value_reg} r0 {ast.dest.idx}")
        else:
            raise Exception(f"Unknown register: {ast.dest}")

    def handle_IndirectWrite(self, ast: compiler.IndirectWrite):
        self.asm.start(f"write {compiler._Stmt_str(ast)}")

        imm = self.immediate(ast.value)
        if imm == 0:
            # Only 0 can be written in a single cycle, using r0 as the source
            addr_reg = self._handle_Expr(ast.address)
            self.asm.instr(f"sw r0 {addr_reg} 0")
        elif imm is not None:
            self.asm.instr(f"addi {TEMP2} r0 {imm}")
            addr_reg = self._handle_Expr(ast.address)
            assert addr_reg != TEMP2
            self.asm.instr(f"sw {TEMP2} {addr_reg} 0")
        else:
            # Construct the value, move it to TEMP2:
            # TODO: just put it in the right place to begin with
            value_reg = self._handle_Expr(ast.value)
            self.asm.instr(f"addi {TEMP2} {value_reg} 0")

            addr_reg = self._handle_Expr(ast.address)
            assert addr_reg != TEMP2
            self.asm.instr(f"sw {TEMP2} {addr_reg} 0")

    def handle_Store(self, ast: compiler.Store):
        self.asm.start(f"store {compiler._Stmt_str(ast)}")

        kind, index = ast.location.kind, ast.location.idx
        if kind == "static":
            value_reg = self._handle_Expr(ast.value)

            addr = self.static_base + index
            assert addr <= MAX_STATIC, f"statics must all fit between {MIN_STATIC} and {MAX_STATIC}"
            assert addr <= 63, f"statics must all fit in a 6-bit offset for one-cycle store"
            self.asm.instr(f"sw {value_reg} r0 {addr}")

        elif kind == "field":
            raise Exception(f"should have been rewritten: {ast}")

        else:
            if kind == "argument":
                segment_ptr = ARG_ADDR
            elif kind == "local":
                segment_ptr = LCL_ADDR
            else:
                raise Exception(f"Unknown location: {ast}")

            if 0 <= index <= 63:
                value_reg = self._handle_Expr(ast.value)
                assert value_reg != TEMP2
                self.asm.instr(f"lw {TEMP2} r0 {segment_ptr}")
                self.asm.instr(f"sw {value_reg} {TEMP2} {index}")
            else:
                raise Exception(f"TODO: segment offset > 64: {kind} {index}")

    def handle_If(self, ast: compiler.If):
        self.asm.comment("if...")

        if ast.when_false is None:
            # Awesome: when there's no else, and the condition is simple, it turns into a single branch.

            end_label = self.asm.next_label("end")

            self.asm.start(f"if {compiler._Expr_str(ast.value)} {ast.cmp} 0?")
            self._handle_cond(ast.value, compiler.negate_cmp(ast.cmp), end_label)

            for s in ast.when_true:
                self._handle(s)

            self.asm.label(end_label)

        else:
            end_label = self.asm.next_label("end")
            false_label = self.asm.next_label("false")

            self.asm.start(f"if/else {compiler._Expr_str(ast.value)} {ast.cmp} 0?")
            self._handle_cond(ast.value, compiler.negate_cmp(ast.cmp), false_label)

            for s in ast.when_true:
                self._handle(s)

            # The last statement is often "return", in which case there's no need to skip over when_false:
            if isinstance(ast.when_true[-1], compiler.Return):
                self.asm.comment("(end of body unreachable)")
            else:
                self._jmp(end_label)

            self.asm.label(false_label)
            for s in ast.when_false:
                self._handle(s)

            self.asm.label(end_label)

    def handle_While(self, ast):
        # Note: putting the test at the bottom of the loop means one jump to start,
        # then a single (conditional) jump per iteration. That's cheaper as long
        # as the average loop does more than one iteration.

        body_label = self.asm.next_label("loop_body")
        test_label = self.asm.next_label("loop_test")

        self.asm.start("while-start")
        self._jmp(test_label)

        self.asm.label(body_label)
        for s in ast.body:
            self._handle(s)

        self.asm.label(test_label)
        for s in ast.test:
            self._handle(s)

        self.asm.start(f"while-test {compiler._Expr_str(ast.value)} {ast.cmp} 0?")
        self._handle_cond(ast.value, ast.cmp, body_label)

    def _handle_cond(self, value: compiler.Expr, cmp: compiler.Cmp, target_label: str):
        """Compare the value with zero according to the given compare op, and jump to the target
        if it is satisfied.
        Try to keep branching to a minimum, but it's tricky since the beq instruction is so limited.
        """

        value_reg = self._handle_Expr(value)
        if cmp == "=":
            # Easy case: if value = 0 then do the jump (by not skipping it)
            self.asm.instr(f"beq {value_reg} r0 +1")
            self.asm.instr(f"beq r0 r0 +3")
            self._jmp(target_label)

        elif cmp == "!=":
            # Easy case: if value = 0 then don't jump
            self.asm.instr(f"beq {value_reg} r0 +3")
            self._jmp(target_label)

        elif cmp == "<":
            # If the sign bit is set, then jump
            self._sign(src=value_reg, dst=TEMP2)  # r7 = sign bit

            self.asm.instr(f"beq {TEMP2} r0 +3")
            self._jmp(target_label)

        elif cmp == ">":
            # Negate, then if sign bit is set, jump
            # TODO: addi -1 is one less cycle than negate
            self._neg(value_reg, TEMP1)
            self._sign(src=TEMP1, dst=TEMP2)  # r7 = sign bit of -value

            self.asm.instr(f"beq {TEMP2} r0 +3")
            self._jmp(target_label)

        elif cmp == "<=":
            # Negate, then if the sign bit is not set, jump
            self._neg(value_reg, TEMP1)
            self._sign(src=TEMP1, dst=TEMP2)  # r7 = sign bit of -value

            self.asm.instr(f"beq {TEMP2} r0 +1")
            self.asm.instr(f"beq r0 r0 +3")
            self._jmp(target_label)

        elif cmp == ">=":
            # If the sign bit is not set, then jump
            self._sign(src=value_reg, dst=TEMP2)  # r7 = sign bit

            self.asm.instr(f"beq {TEMP2} r0 +1")
            self.asm.instr(f"beq r0 r0 +3")
            self._jmp(target_label)

        else:
            raise Exception(f"Unknown cmp: {cmp}")

    def _jmp(self, label):
        """Unconditionally jump to a label, without saving a return address.

        Always uses a three-cycle lui/lli/jalr sequence, because these jumps will often exceed 64
        addresses, and anyway the assembler can't yet beq to a label.

        Overwrites TEMP1 (with the target address).
        """

        self.asm.instr(f"lui {TEMP1} @{label}")
        self.asm.instr(f"lli {TEMP1} @{label}")
        self.asm.instr(f"jalr r0 {TEMP1}")

    def _neg(self, src, dst):
        """Negate the value in the given (true) register, possibly in place, in 2 cycles.
        If src and dst are different, src is not overwritten.
        """
        self.asm.instr(f"nand {dst} {src} {src}")
        self.asm.instr(f"addi {dst} {dst} 1")

    def _sign(self, src, dst):
        """Mask off the sign bit of the value in the given (true) register, into a separate register, in 3 cycles."""
        assert src != dst, "src and dst must be different registers"
        self.asm.instr(f"lui {dst} -32768")
        self.asm.instr(f"nand {dst} {src} {dst}")
        self.asm.instr(f"nand {dst} {dst} {dst}")  # dst = src & 0x8000


    def handle_Return(self, ast: compiler.Return):
        if isinstance(ast.expr, compiler.CallSub):
            self.call(ast.expr)
            self.asm.comment(f"leave the result in {TEMP2}")

        else:
            self.asm.start(f"eval-{self.describe_expr(ast.expr)} {compiler._Expr_str(ast.expr)} (for return)")

            # Save a cycle for "return 0" (and other constant values):
            imm = self.immediate(ast.expr)
            if imm is not None:
                self.asm.instr(f"addi {TEMP2} r0 {imm}")
            else:
                value_reg = self._handle_Expr(ast.expr)
                if value_reg != TEMP2:
                    # TODO: construct the value in TEMP2 directly
                    self.asm.instr(f"addi {TEMP2} {value_reg} 0")

        self.asm.start("return")

        if self.debug:
            self.asm.comment("DEBUG: copy return value to R15")
            self.asm.instr(f"sw {TEMP2} r0 15")

        self._jmp(self.return_label)

    def handle_Push(self, ast):
        if not isinstance(ast.expr, compiler.CallSub):
            self.asm.start(f"push-{self.describe_expr(ast.expr)} {compiler._Expr_str(ast.expr)}")

        # Save a cycle for "push 0" only:
        imm = self.immediate(ast.expr)
        if imm == 0:
            self.asm.instr(f"sw r0 {SP} 0")
            self.asm.instr(f"addi {SP} {SP} 1")
        else:
            # Any non-zero value has to go to a register anyway, so just use the normal handler:
            value_reg = self._handle_Expr(ast.expr)

            if isinstance(ast.expr, compiler.CallSub):
                self.asm.start(f"push-result {compiler._Expr_str(ast.expr)}")

            self.asm.instr(f"sw {value_reg} {SP} 0")
            self.asm.instr(f"addi {SP} {SP} 1")

    def handle_Discard(self, ast: compiler.Discard):
        # Note: now that results are passed in a register, there's no cleanup to do when
        # the result is not used.
        self.call(ast.expr)

        self.asm.comment(f"ignore the result")


    # Expressions:

    def _handle_Expr(self, ast: compiler.Expr, *args) -> str:
        """Emit instructions to compute the value of an expression, returning the location, which
        is always a "true" register.

        The caller should not assume that it's safe to overwrite the register where the value
        is found, unless it knows otherwise. However, it's always safe to overwrite TEMP1 and TEMP2.
        """

        return self.__getattribute__(f"handle_Expr_{ast.__class__.__name__}")(ast, *args)

    def handle_Expr_CallSub(self, ast: compiler.CallSub) -> str:
        self.call(ast)

        return TEMP2


    def call(self, ast: compiler.CallSub):
        """Note: no need to label the return address; jalr captures it for us."""

        self.referenced_functions.append(f"{ast.class_name}.{ast.sub_name}")

        self.asm.start(f"call {ast.class_name}.{ast.sub_name} {ast.num_args}")

        target_label = f"{ast.class_name.lower()}.{ast.sub_name}"
        self.asm.instr(f"lui {TEMP1} @{target_label}")
        self.asm.instr(f"lli {TEMP1} @{target_label}")
        self.asm.instr(f"jalr {TEMP2} {TEMP1}")

    def handle_Expr_Const(self, ast: compiler.Const, reg: str = TEMP1) -> str:
        """Construct the value in the requested location.

        Note: no other register is overwritten.
        """

        if -64 <= ast.value <= 63:
            self.asm.instr(f"addi {reg} r0 {ast.value}")
        else:
            high10 = ast.value & ~0x3F
            low6 = ast.value & 0x3F
            self.asm.instr(f"lui {reg} {high10}")
            if low6 != 0:
                self.asm.instr(f"addi {reg} {reg} {low6}")
        return reg

    def handle_Expr_Location(self, ast: compiler.Location) -> str:
        kind, index = ast.kind, ast.idx
        if kind == "static":
            addr = self.static_base + index
            assert addr <= MAX_STATIC, f"statics must all fit between {MIN_STATIC} and {MAX_STATIC}"
            assert addr <= 63, f"statics must all fit in a 6-bit offset for one-cycle load"
            self.asm.instr(f"lw {TEMP1} r0 {addr}")
        elif kind == "field":
            raise Exception(f"should have been rewritten: {ast}")
        else:
            if kind == "argument":
               segment_ptr = ARG_ADDR
            elif kind == "local":
                segment_ptr = LCL_ADDR
            else:
                raise Exception(f"Unknown location: {ast}")

            if 0 <= index <= 63:
                self.asm.instr(f"lw {TEMP2} r0 {segment_ptr}")
                self.asm.instr(f"lw {TEMP1} {TEMP2} {index}")
            else:
                raise Exception(f"TODO: segment offset > 64: {kind} {index}")
        return TEMP1

    def handle_Expr_Reg(self, ast: compiler.Reg, reg: str = TEMP1) -> str:
        """If the value is already in a (true) register, just return the actual location,
        otherwise copy it to `reg` and return that.

        Note: no other register is overwritten.
        """
        if ast.kind == "r":
            return f"r{ast.idx}"
        elif ast.kind == "R":
            self.asm.instr(f"lw {reg} r0 {ast.idx}")
            return reg
        else:
            raise Exception(f"Unknown register: {ast}")

    def handle_Expr_Binary(self, ast: compiler.Binary) -> str:
        # TODO: the compiler's first phase *should* be rewriting these to be trivial for this
        # CPU, but it doesn't at the moment so where does that leave us for now?

        # TODO: take a "reg" parameter, and put the result there, minimizing copying.

        # Load the left and right operands, either in their source registers, or in TEMP1 or
        # TEMP2, respectively. Because both operands must be either Reg or Const, we can
        # be sure that they don't overwrite each other.
        left_reg = self._handle_Expr(ast.left, TEMP1)
        right_reg = self._handle_Expr(ast.right, TEMP2)
        assert left_reg != TEMP2
        assert right_reg != TEMP1

        # Note: each case may overwrite TEMP1, TEMP2, or both, but never overwrite
        # any other register which might appear as a source.
        if ast.op.symbol == "+":
            # TODO: special-case for Const with addi
            self.asm.instr(f"add {TEMP1} {left_reg} {right_reg}")
            return TEMP1
        elif ast.op.symbol == "-":
            # First negate rhs:
            self._neg(right_reg, TEMP2)
            self.asm.instr(f"add {TEMP1} {left_reg} {TEMP2}")
            return TEMP1
        elif ast.op.symbol == "&":
            self.asm.instr(f"nand {TEMP1} {left_reg} {right_reg}")
            self.asm.instr(f"nand {TEMP1} {TEMP1} {TEMP1}")
            return TEMP1
        elif ast.op.symbol == "|":
            self.asm.instr(f"nand {TEMP1} {left_reg} {left_reg}")  # r6 = !lhs
            self.asm.instr(f"nand {TEMP2} {right_reg} {right_reg}")  # r7 = !rhs
            self.asm.instr(f"nand {TEMP1} {TEMP1} {TEMP2}")  # r6 = !(!lhs & !rhs) = lhs | rhs
            return TEMP1
        elif ast.op.symbol == "=":
            self.asm.instr(f"beq {left_reg} {right_reg} +2")  # skip true case
            self.asm.instr(f"addi {TEMP1} r0 0")
            self.asm.instr(f"beq r0 r0 +1")  # skip false case
            self.asm.instr(f"addi {TEMP1} r0 -1")
            return TEMP1
        elif ast.op.symbol == "<":
            self._neg(right_reg, TEMP2)
            self.asm.instr(f"add {TEMP1} {left_reg} {TEMP2}")  # r6 = lhs - rhs

            self._sign(TEMP1, TEMP2)  # r7 = 0x8000 if (lhs - rhs) < 0

            self.asm.instr(f"addi {TEMP1} r0 0")  # result = 0 (false) unless overwritten
            self.asm.instr(f"beq {TEMP2} r0 +1")   # sign bit not set: >= 0; skip true case
            self.asm.instr(f"addi {TEMP1} r0 -1")  # result = -1 (true)
            return TEMP1
        elif ast.op.symbol == ">":
            self._neg(left_reg, TEMP1)
            self.asm.instr(f"add {TEMP1} {TEMP1} {right_reg}")  # r6 = rhs - lhs

            self._sign(TEMP1, TEMP2)  # r7 = 0x8000 if (rhs - lhs) < 0

            self.asm.instr(f"addi {TEMP1} r0 0")  # result = 0 (true) unless overwritten
            self.asm.instr(f"beq {TEMP2} r0 +1")   # sign bit not set: >= 0; skip true case
            self.asm.instr(f"addi {TEMP1} r0 -1")  # result = -1
            return TEMP1
        else:
            raise Exception(f"Unknown binary op: {compiler._Expr_str(ast)}")

    def handle_Expr_Unary(self, ast: compiler.Unary) -> str:
        value_reg = self._handle_Expr(ast.value)
        if ast.op.symbol == "-":
            self._neg(value_reg, TEMP1)
            return TEMP1
        elif ast.op.symbol == "~":
            self.asm.instr(f"nand {TEMP1} {value_reg} {value_reg}")
            return TEMP1
        else:
            raise Exception(f"Unknown unary op: {compiler._Expr_str(ast)}")

    def handle_Expr_IndirectRead(self, ast: compiler.IndirectRead) -> str:
        addr_reg = self._handle_Expr(ast.address)
        self.asm.instr(f"lw {TEMP1} {addr_reg} 0")
        return TEMP1


    def immediate(self, ast: compiler.Expr) -> Optional[int]:
        """If the expression is a constant which can appear in an "addi", "lw", or "sw"
        (i.e. 7 signed bits), then unpack it.
        """
        if isinstance(ast, compiler.Const) and -64 <= ast.value <= 63:
            return ast.value
        else:
            return None

    def describe_expr(self, expr: compiler.Expr) -> str:
        """A short suffix categorizing the type of expression, for example 'const'.

        Added to "opcode" tags in the instruction stream, these separate descriptions might be
        helpful for readers; mainly they improve profiling.
        """

        if isinstance(expr, compiler.CallSub):
            return "call"
        elif isinstance(expr, compiler.Const):
            return "const"
        elif isinstance(expr, compiler.Location):
            return "load"
        elif isinstance(expr, compiler.Reg):
            return "copy"
        elif isinstance(expr, compiler.Binary):
            return "binary"
        elif isinstance(expr, compiler.Unary):
            return "unary"
        elif isinstance(expr, compiler.IndirectRead):
            return "read"
        else:
            raise Exception(f"Unknown expr: {expr}")

    def _handle(self, ast):
        self.__getattribute__(f"handle_{ast.__class__.__name__}")(ast)


    # Override common bits:

    def preamble(self):
        self.asm.start("VM initialization")
        self.asm.instr(f"lui {SP} 256")

        # Note: this call will never return, so no need to set up a return address, or
        # even initialize ARG/LCL.
        self.asm.start("call Sys.init 0")
        self.asm.instr(f"lui {TEMP1} @sys.init")
        self.asm.instr(f"lli {TEMP1} @sys.init")
        self.asm.instr(f"jalr r0 {TEMP1}")
        self.asm.blank()


    def _return(self):
        """Override the normal sequence; much less stack adjustment required.

        The return value is in TEMP2 before and after.

        Note that r2-r6 are all available for use here, since the local scope is
        no longer needed.

        9 cycles (plus 3 to jump here from each )
        """
        # TODO: use this only for non-leaf subroutines

        label = self.asm.next_label("return_common")

        self.asm.comment(f"common return sequence")
        self.asm.label(label)

        self.asm.comment("SP (r1) = LCL (RAM[1])")
        self.asm.instr(f"lw {SP} r0 {LCL_ADDR}")

        self.asm.comment("r2 = ARG (RAM[2]; previous SP)")
        self.asm.instr(f"lw r2 r0 {ARG_ADDR}")

        self.asm.comment("restore segment pointers from stack (ARG, LCL)")
        self.asm.instr(f"lw {TEMP1} {SP} -1")
        self.asm.instr(f"sw {TEMP1} r0 {ARG_ADDR}")
        self.asm.instr(f"lw {TEMP1} {SP} -2")
        self.asm.instr(f"sw {TEMP1} r0 {LCL_ADDR}")

        self.asm.comment("r3 = saved return address from the stack")
        self.asm.instr(f"lw r3 {SP} -3")

        self.asm.comment("SP = r2 (saved ARG)")
        self.asm.instr(f"addi {SP} r2 0")

        self.asm.comment("jmp to r3 (saved return address)")
        self.asm.instr("jalr r0 r3")

        return label


    # Override some unused bits and pieces to save space:

    def _call(self):
        # not used
        return "_call_common_unused"

    def _compare(self, op):
        # This common sequence isn't used; each comparison is compiled to a custom
        # test/branch sequence.
        return f"_compare_{op}_unused"



#
# Platform:
#

def compile_compatible(ast, asm):
    """Wrap the compiler to simulate the sequence the other platforms go through.
    In this case, this phase doesn't generate VM opcodes, but instead just records
    each Class to the stream as a unit.
    """

    ir = RiSCCompiler()(ast)

    # Giant hack: write each class to the AssemblySource as if it was an instruction
    asm.add_line_raw(ir)


def parse_line_compatible(line):
    """Phony VM opcode parsing, to simulate the sequence the other platforms go through.
    These "lines" aren't really lines, and just need to get passed through to the next
    step (the translator.)
    """

    return line


RiSC_REG_PLATFORM = BUNDLED_PLATFORM._replace(
    chip=alt.risc.chip.RiSCComputer,
    assemble=alt.risc.asm.assemble,
    parse_line=parse_line_compatible,
    translator=Translator,
    compiler=compile_compatible)

if __name__ == "__main__":
    # Note: this import requires pygame; putting it here allows the tests to import the module
    import computer

    computer.main(RiSC_REG_PLATFORM)