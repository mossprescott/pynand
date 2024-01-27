#! /usr/bin/env python

"""Ribbit VM implementation.
"""

import computer
# import nand
from nand.translate import AssemblySource
from alt import big
from nand.vector import unsigned

def run(program):

    encoded = compile(program)
    print(f"encoded program: {repr(encoded)}")

    asm = AssemblySource()

    interpreter(asm)

    decode(encoded, asm)

    # TODO: how many statics?
    # TODO: custom BUILTIN_SYMBOLS
    # min_static =
    # max_static =
    instrs, symbols, statics = big.assemble(asm.lines)



# Example: "(poke 16384 21845)"
# proc(nil):
#   call(#0)
#   const(#21)
#   const(#0)
#   const(#1)
#   call(symbol(#f, 'rib')@4378049088)
#   set(symbol(#f, 'poke')@4378050432)
#   const(#16384)
#   const(#21845)
#   jump(symbol(#f, 'poke')@4378050432)


    PRINT = True
    if PRINT:
        for l in asm.lines: print(l)
        print()

        runtime_words = len(instrs) - big.ROM_BASE
        total_rom = big.HEAP_BASE - big.ROM_BASE
        # TODO: count ribs in the ROM separate from the fixed runtime
        # program_words = len(encoded)
        reserved_words = 8 + 22  # Interpreter/decoder state, and the primitive vectors
        # available_ram = 0x4000 - reserved_words
        print(f"ROM: {runtime_words:,d} ({100*runtime_words/total_rom:0.2f}%)")
        # print(f"Encoded program: {program_words} ({100*program_words/available_ram:0.2f}%)")
        print()

        for name, addr in sorted(symbols.items(), key=lambda t: t[1]):
            print(f"  {name}: {addr}")

    # # This is enough to get minimal tracing from the standard driver in computer.py.
    # # It will just log the cycle count each time we go through each of the main loops.
    # src_map = {
    #     # symbols["decode_loop"]: "decode",
    #     symbols["exec_loop"]: "exec"
    # }

    def trace(computer, cycles):
        if computer.fetch and computer.pc == symbols["exec_loop"]:
            print(f"{cycles:3,d}:")

            # TODO: decode these ribs/values
            print(f"  PC: @{computer.peek(0)}")
            print(f"  SP: @{computer.peek(1)}, ...")

            next_rib = unsigned(computer.peek(2))
            current_ribs = (next_rib - big.HEAP_BASE)//3
            max_ribs = (big.HEAP_TOP - big.HEAP_BASE)//3
            print(f"  heap: {current_ribs:3,d} ({100*current_ribs/max_ribs:0.1f}%)")


    big.run(program=instrs,
            name="Scheme",
            halt_addr=symbols["halt_loop"],
            trace=trace)


def compile(src):
    import subprocess
    result = subprocess.run(["python", "alt/scheme/ribbit/rsc.py"],
                            text=True,
                            input=src,
                            capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Compiler failed: {result.stdout}")
    return result.stdout


# $2gra,ekop,,,,;'v[_LvXs+!'?X&lkv8i)!):ok:okw#!(:lkny
#
# symbol table: ","-separated, ";"-terminated:
#

def decode(input, asm):
    """Decode the compiler's output as data in ROM.

    The strings which are the names of symbols are written as ribs in the ROM.
    A table of addresses of those strings is written to ROM; it will be read by the runtime
    during initialization when the storage for symbols is allocated in RAM.

    Each encoded instruction is written as a rib in the ROM. When an instruction references
    a symbol, the reference is resolved to the address in RAM where that symbol is expected
    to be allocated at runtime.

    See https://github.com/udem-dlteam/ribbit/blob/dev/src/host/py/rvm.py#L126
    """

    # base_addr = len(big.assemble(asm.lines)[0])

    # next_rib = 0

    # def emit_rib(x, y, z):
    #     nonlocal next_rib
    #     name = f"rib{next_rib}"
    #     asm.label(name)
    #     asm.instr(x)
    #     asm.instr(y)
    #     asm.instr(z)
    #     next_rib += 1
    #     return f"@{name}"

    asm.comment("===  Data  ===")

    # Three constants the runtime can refer to by name:
    def special(name):
        asm.label(name)
        asm.instr("#0")
        asm.instr("#0")
        asm.instr("#5")
    special("rib_false")
    special("rib_true")
    special("rib_nil")

    # asm.label("input_start")

    # # TODO: decode from characters into raw byte/int values
    # for c in input:
    #     asm.instr(f"#{hex(ord(c))}")

    # asm.label("input_end")

    # def emit_cons(x, y): return emit_rib(x, y, "#0")
    # def emit_symbol(x)


    # for comprehension:
    pos = -1
    def get_byte():
        nonlocal pos
        pos += 1
        return ord(input[pos])

    def get_code():
        """Decoded value of the next single character."""
        x = get_byte() - 35
        return 57 if x < 0 else x

    def get_int(n):
        """Decoded value of sequence of characters"""
        x = get_code()
        if x < 46:
            return 46*n + x
        else:
            return get_int(46*n + x-46)
        # n *= 46
        # return n+x if x < 46 else get_int(n + x - 46)


    def emit_rib(lbl, x, y, z, comment=None):
        if lbl:
            asm.label(lbl)
        if comment:
            asm.comment(comment)
        asm.instr(x)
        asm.instr(y)
        asm.instr(z)

    def emit_pair(lbl, car, cdr):             emit_rib(lbl, car, cdr, "#0")
    def emit_proc(lbl, code, env):            emit_rib(lbl, code, env, "#1")
    def emit_symbol(lbl, value, name):        emit_rib(lbl, value, name, "#2")
    def emit_string(lbl, chars, count: int):  emit_rib(lbl, chars, f"#{count}", "#3")
    def emit_vector(lbl, elems, count: int):  emit_rib(lbl, elems, f"#{count}", "#4")




    # Strings for the symbol table, as constant ribs directly in the ROM:

    # One empty string that can be shared:
    emit_string("rib_string_empty", "@rib_nil", 0)

    # First byte(s): number of symbols without names
    n = get_int(0)
    sym_names = n*[("rib_string_empty", "")]

    accum = "@rib_nil"
    acc_str = ""
    idx = 0
    while True:
        c = get_byte()
        if c == ord(",") or c == ord(";"):
            if acc_str == "":
                lbl = "rib_string_empty"
            else:
                asm.comment(f'"{acc_str}"')
                lbl = f"rib_string_{idx}"
                emit_string(lbl, accum, len(acc_str))
                idx += 1
            sym_names.insert(0, (lbl, acc_str))

            accum = "@rib_nil"
            acc_str = ""

            if c == ord(";"):
                break
        else:
            asm.comment(f"'{chr(c)}'")
            lbl = asm.next_label("char")
            emit_pair(lbl, f"#{hex(c)}", accum)
            accum = f"@{lbl}"
            acc_str = chr(c) + acc_str


    # TODO: move this table elsewhere, so the ribs for strings and instructions form a monolithic
    # block of address space?
    asm.comment("Table of pointers to symbol name ribs in ROM:")
    asm.label("symbol_names_start")
    for lbl, s in sym_names:
        if s != "":
            asm.comment(f'"{s}"')
        asm.instr(f"@{lbl}")
    asm.label("symbol_names_end")


    # Decode RVM instructions:

    asm.comment("Instructions:")

    stack = None
    def pop():
        nonlocal stack
        x, stack = stack
        return x
    def push(x):
        nonlocal stack
        stack = (x, stack)

    def symbol_ref(idx):
        """Statically resolve a reference to the symbol table, to an address in RAM where that
        rib will be allocated during initialization.

        The table is written from the end, and each entry is made of of two ribs, the `symbol`
        and a `pair`.
        """
        # TODO: fix the inevitable of-by-one error(s) here
        asm.comment(f'symbol_ref({idx}); "{sym_names[idx][1]}"')
        return f"#{FIRST_RIB + 6*(len(sym_names) - idx)}"

    def emit_instr(op, arg, next):
        lbl = asm.next_label("instr")

        asm.label(lbl)

        if op == 0 and next == "#0":
            asm.comment(f"jump {arg} ")
        elif op == 0:
            asm.comment(f"call {arg} -> {next}")
        elif op == 1:
            asm.comment(f"set {arg} -> {next}")
        elif op == 2:
            asm.comment(f"get {arg} -> {next}")
        elif op == 3:
            asm.comment(f"const {arg} -> {next}")
        elif op == 4:
            asm.comment(f"if -> {arg} else {next}")
        else:
            raise Exception(f"Unknown op: {op} ({arg}, {next})")

        asm.instr(f"#{op}")
        asm.instr(arg)
        asm.instr(next)

        return lbl

    # For each encoded instruction, emit three words of data into the ROM:
    # - references to symbols are statically resolved to addresses in *RAM*,
    #   where the references

    # TODO: reverse the instruction stream so it reads *forward* in the commented assembly listing?

    # FIXME: this horribleness is ripped off from https://github.com/udem-dlteam/ribbit/blob/dev/src/host/py/rvm.py directly
    # What part of this happens at runtime?
    while True:
        if pos >= len(input)-1: break  # TEMP

        x = get_code()
        # asm.comment(f"x = get_code() = {x}")
        n = x
        d = 0
        op = 0

        while True:
            d = [20, 30, 0, 10, 11, 4][op]
            if n <= 2+d: break
            n -= d+3; op += 1

        # asm.comment(f"op: {op}; n: {n}")

        if x > 90:
            n = pop()
            # asm.comment(f"[if] x: {x}; n = {n}")
        else:
            if op == 0:
                push("#0")
                # stack = [0, stack]
                # asm.comment(f"op == 0; TODO: stack = cons(0, stack)")
                op += 1

            if n == d:
                n = f"#{get_int(0)}"
                # print(f"n = get_int(0) = {n}")
                # asm.comment(f"n = get_int(0) = {n}")
            elif n >= d:
                #n = symbol_ref(get_int(n-d-1))
                idx = get_int(n-d-1)
                # asm.comment(f"idx = get_int({n-d-1}) = {idx}")
                n = symbol_ref(idx)
                # asm.comment(f"{n} >= {d}; TODO: n = symbol_ref({idx})")
            elif op < 3:
                n = symbol_ref(n)
                # asm.comment(f"{op} < 3; TODO: n = {n}")

            if op > 4:
                # This is either a lambda, or the outer proc that wraps the whole program.
                body = pop()
                if not stack:
                    n = body
                    break
                else:
                    params_lbl = asm.next_label("params")
                    emit_rib(params_lbl, n, "#0", body)
                    # FIXME: is this even close?
                    proc_label = asm.next_label("proc")
                    asm.label(proc_label)
                    asm.instr(f"@{params_lbl}")
                    asm.instr("@rib_nil")
                    asm.instr("#1")
                    # n = [[n, 0, m], "@rib_nil", 1]
                    # asm.comment(f"proc: {n}, ...")
                    n = f"@{proc_label}"
                    op = 4

            # HACK: this seems to happen with integer constants and slot numbers.
            # Make it happen in the right place?
            if isinstance(n, int):
                n = f"#{n}"

            instr_lbl = emit_instr(op-1, n, pop())
            push(f"@{instr_lbl}")

    # This will be the body of the outer proc, so just "jump" straight to it:
    start_instr = n
    # Note: emit_instr would want to choose the label...
    emit_rib("main", "#0", start_instr, "#0", comment=f"jump {start_instr}")


FIRST_RIB = big.HEAP_BASE
"""Start of runtime-allocated ribs, which is the first word of RAM after the space which is mapped
to ROM.
"""

def interpreter(asm):
    """ROM program implementing the RVM runtime, which interprets a program stored as "ribs" in ROM and RAM."""

    # Interpreter variables in low memory:
    PC = 0
    SP = 1
    NEXT_RIB = 2

    # RETURN = 3

    # used only during initialization?
    SYMBOL_TABLE = 4

    num_primitives = 22
    FIRST_PRIMITIVE = 8
    LAST_PRIMITIVE = FIRST_PRIMITIVE + num_primitives

    FALSE = "rib_false"
    TRUE = "rib_true"
    NIL = "rib_nil"

    # FIXME: probably no return; jump straight to exec_loop?
    # def call_primitive(lbl):
    #     rtn_label = asm.next_label("return")
    #     asm.instr(f"@{rtn_label}")
    #     asm.instr("D=A")
    #     asm.instr(f"@{RETURN}")
    #     asm.instr("M=D")
    #     asm.instr(f"@{lbl}")
    #     asm.instr("0;JMP")
    #     asm.label(rtn_label)

    # def return_from_primitive():
    #     asm.comment("return")
    #     asm.instr(f"@{RETURN}")
    #     asm.instr("A=M")
    #     asm.instr("0;JMP")

    # def push_d():
    #     """Push the value in D onto the stack, without over-writing it."""
    #     asm.instr(f"@{SP}")
    #     asm.instr("M=M-1")
    #     asm.instr("A=M+1")  # i.e., point to the previous location
    #     asm.instr("M=D")

    # def rib(x, y, z):
    #     asm.comment(f"rib: {x}, {y}, {z}")
    #     asm.comment("TODO: D = {x}")
    #     asm.instr("@{NEXT_RIB}")
    #     asm.instr("A=M")
    #     asm.instr("M=D")
    #     asm.comment("TODO: D = {y}")
    #     asm.instr("@{NEXT_RIB}")
    #     asm.instr("AM=M+1")
    def rib_append(val="D"):
        """Add a word to the rib currently being constructed.

        Always called three times in succession to construct a full rib.
        The value is either "D" (the default), or a value the ALU can produce (0 or 1, basically).
        """

        asm.instr(f"@{NEXT_RIB}")
        asm.instr("M=M+1")
        asm.instr("A=M-1")
        asm.instr(f"M={val}")


    # TODO: find end of encoded program; initialize stack pointer below it
    decode_stack_start = 16384//2 - 1
    asm.comment("SP = below the encoded program")
    asm.instr(f"@{decode_stack_start}")
    asm.instr("D=A")
    asm.instr(f"@{SP}")
    asm.instr("M=D")
    asm.comment(f"NEXT_RIB = {FIRST_RIB} (HEAP_BASE)")
    asm.instr(f"@{FIRST_RIB-1}")
    asm.instr("D=A+1")
    asm.instr(f"@{NEXT_RIB}")
    asm.instr("M=D")

    # prim_rib_label = asm.next_label("prim_rib")

    # asm.comment("Initialize primitive vectors")
    # for i, l in enumerate([prim_rib_label]):
    #     asm.instr(f"@{l}")
    #     asm.instr("D=A")
    #     asm.instr(f"@{FIRST_PRIMITIVE + i}")
    #     asm.instr("M=D")

    # asm.comment("Initialize shared constants")
    # for n in ("false", "true", "nil"):
    #     asm.comment(f"{n} = rib(0, 0, 5)")
    #     asm.instr("D=0")
    #     push_d()
    #     push_d()
    #     asm.instr("@5")
    #     asm.instr("D=A")
    #     push_d()
    #     call_primitive(prim_rib_label)

    asm.comment("Construct the symbol table in RAM:")
    asm.comment("SYMBOL_TABLE = '()")
    asm.instr("@rib_nil")
    asm.instr("D=A")
    asm.instr(f"@{SYMBOL_TABLE}")
    asm.instr("M=D")

    asm.comment("R5 = ptr")
    asm.instr(f"@symbol_names_start")
    asm.instr("D=A")
    asm.instr("@R5")
    asm.instr("M=D")

    loop = "symbol_table_loop"
    asm.label(loop)

    asm.comment("DEBUG: log the pointer to tty")
    asm.instr("@R5")
    asm.instr("D=M")
    asm.instr("@KEYBOARD")
    asm.instr("M=D")

    asm.comment("new symbol, with value = false")
    asm.instr("@rib_false")
    asm.instr("D=A")
    rib_append()
    asm.instr("@R5")
    asm.instr("D=M")
    rib_append()
    asm.instr("@2")  # symbol
    asm.instr("D=A")
    rib_append()

    asm.comment("SYMBOL_TABLE = new pair")
    asm.comment("car = the rib we just wrote")
    asm.instr(f"@{NEXT_RIB}")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    rib_append()
    asm.comment("cdr = (old) SYMBOL_TABLE")
    asm.instr(f"@{SYMBOL_TABLE}")
    asm.instr("D=M")
    rib_append()
    rib_append("0")  # pair
    asm.instr(f"@{NEXT_RIB}")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    asm.instr(f"@{SYMBOL_TABLE}")
    asm.instr("M=D")

    asm.comment("DEBUG: log NEXT_RIB to tty")
    asm.instr(f"@{NEXT_RIB}")
    asm.instr("D=M")
    asm.instr("@KEYBOARD")
    asm.instr("M=D")

    asm.comment("increment R5")
    asm.instr("@R5")
    asm.instr("M=M+1")

    asm.comment("D = compare(R5, symbol_names_end)")
    asm.instr("D=M")
    asm.instr("@symbol_names_end")
    asm.instr("D=D-M")
    asm.instr(f"@{loop}")
    asm.instr("D;JLT")


    # decode_label = "decode_loop"
    # asm.label(decode_label)
    # asm.instr(f"@{decode_label}")
    # asm.instr("0;JMP")

    # # Now move the stack pointer to the top of memory (over-writing the encoded program)
    # asm.comment("SP = top of memory")
    # asm.instr("@16384")
    # asm.instr("D=A")
    # asm.instr(f"@{SP}")
    # asm.instr("M=D")

    asm.comment("PC = @main")
    asm.instr("@main")
    asm.instr("D=A")
    asm.instr(f"@{PC}")
    asm.instr("M=D")

    #
    # Exec loop:
    #

    exec_label = "exec_loop"
    asm.label(exec_label)
    asm.comment("TODO")
    asm.instr("D=D")
    # asm.instr(f"@{exec_label}")
    # asm.instr("0;JMP")


    #
    # Halt:
    #

    halt_label = "halt_loop"
    asm.label(halt_label)
    asm.instr(f"@{halt_label}")
    asm.instr("0;JMP")

    # asm.label("prim_rib_label")
    # asm.comment("TODO:")
    # asm.comment("- check for stack-heap collision")
    # asm.comment("- allocate space for new rib")
    # asm.comment("- pop three values and copy them into the new rib")
    # return_from_primitive()

