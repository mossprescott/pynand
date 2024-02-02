#! /usr/bin/env python

"""Ribbit VM implementation.

See http://www.iro.umontreal.ca/~feeley/papers/YvonFeeleyVMIL21.pdf for the general picture.
"""

import computer
# import nand
from nand.translate import AssemblySource
from alt import big
from nand.vector import extend_sign, unsigned


TRACE_NONE = 0
"""No logging of Ribbit instructions."""
TRACE_COARSE = 1
"""Log each Ribbit instruction before it's interpreted, with a summary of the stack and heap."""
TRACE_FINE = 2
"""Log at each branch point of the interpreter loop (in addition to the COARSE logging.)"""
TRACE_ALL = 3
"""Log every CPU instruction (in addition to COARSE and FINE logging.)"""


def run(program, print_asm=True, trace_level=TRACE_FINE, verbose_tty=True):

    encoded = compile(program)
    # print(f"encoded program: {repr(encoded)}")

    asm = AssemblySource()

    interpreter(asm)

    decode(encoded, asm)

    instrs, symbols, statics = big.assemble(asm.lines, min_static=None, builtins=BUILTINS)

    assert symbols["start"] == big.ROM_BASE


    if print_asm:
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


        def show_map(label, m):
            print("\n".join(
                [ f"{label}:" ] +
                [ f"  {addr:5d}: {name}"
                  for name, addr in sorted(m.items(), key=lambda t: t[1])
                ] +
                [""]
            ))

        show_map("Symbols", symbols)

        if statics != {}:
            show_map("Statics", statics)


    last_traced_exec = None
    symbols_by_addr = { addr: name for (name, addr) in symbols.items() }

    def trace(computer, cycles):
        nonlocal last_traced_exec

        # Only log on one of the half-cycles:
        if not computer.fetch:
            return

        def peek(addr):
            """Read from RAM or ROM."""
            if big.ROM_BASE <= addr < big.HEAP_BASE:
                return computer._rom.storage[addr]
            else:
                return computer.peek(addr)

        def show_instr(addr):
            def show_target(val):
                if val <= BUILTINS["MAX_SLOT"]:
                    return f"#{val}"
                else:
                    return show_addr(val)

            x, y, z = peek(addr), peek(addr+1), peek(addr+2)
            if x == 0 and z == 0:
                return f"jump {show_target(y)}"
            elif x == 0:
                return f"call {show_target(y)} -> {show_addr(z)}"
            elif x == 1:
                return f"set {show_target(y)} -> {show_addr(z)}"
            elif x == 2:
                return f"get {show_target(y)} -> {show_addr(z)}"
            elif x == 3:
                return f"const {show_obj(y)} -> {show_addr(z)}"
            elif x == 4:
                return f"if -> {show_addr(y)} else {show_addr(z)}"
            else:
                return f"not an instr: {(x, y, z)}"

        def show_obj(val, deep=True):
            # FIXME: check tag
            if -big.ROM_BASE < extend_sign(val) < big.ROM_BASE:
                return f"{extend_sign(val)}"
            else:
                x, y, z = peek(val), peek(val+1), peek(val+2)
                if deep:
                    return f"({show_obj(x, False)}, {show_obj(y, False)}, {show_obj(z, False)})"
                else:
                    # return f"{x, y, z}"
                    return f"(@{unsigned(x)}, @{unsigned(y)}, @{unsigned(z)})"

        def show_stack(addr):
            def go(addr):
            if addr == symbols["rib_nil"]:
                    return []
            elif peek(addr+2) == 0:  # pair
                    return go(peek(addr+1)) + [show_obj(peek(addr))]
            return ", ".join(go(addr))

        def show_addr(addr):
            """Show an address (with "@"), using the symbol for addresses in ROM."""
            if addr in symbols_by_addr:
                return f"@{symbols_by_addr[addr]}"
            else:
                return f"@{unsigned(addr)}"

        if trace_level >= TRACE_COARSE and computer.pc == symbols["exec_loop"]:
            if last_traced_exec is None:
                print(f"{cycles:,d}:")
            else:
                print(f"{cycles:,d} (+{cycles - last_traced_exec:,d}):")
            last_traced_exec = cycles

            print(f"  stack: ({show_addr(peek(0))}) {show_stack(peek(0))}")

            next_rib = unsigned(peek(2))
            current_ribs = (next_rib - big.HEAP_BASE)//3
            max_ribs = (big.HEAP_TOP - big.HEAP_BASE)//3
            print(f"  heap: {current_ribs:3,d} ({100*current_ribs/max_ribs:0.1f}%)")
            print(f"  PC: {show_addr(peek(1))}")

            # HACK?
            print(f"  symbols (n..0): ({show_addr(peek(4))}) {show_stack(peek(4))}")
            print(f"  ribs:")
            for addr in range(big.HEAP_BASE, unsigned(computer.peek(BUILTINS["NEXT_RIB"])), 3):
                print(f"    @{addr}; {show_obj(addr, deep=False)}")

            print(f"  {show_instr(peek(1))}")
        elif trace_level >= TRACE_FINE and computer.pc in symbols_by_addr:
            print(f"{cycles:3,d}: ({symbols_by_addr[computer.pc]})")
        elif trace_level >= TRACE_ALL:
            print(f"{cycles:3,d}: {computer.pc}")

    big.run(program=instrs,
            name="Scheme",
            halt_addr=symbols["halt_loop"],
            trace=trace if trace_level > TRACE_NONE else None,
            verbose_tty=verbose_tty)


def compile(src):
    import subprocess
    result = subprocess.run(["python", "alt/scheme/ribbit/rsc.py"],
                            text=True,
                            input=src,
                            capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Compiler failed: {result.stdout}")
    return result.stdout


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

    asm.blank()

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


    def emit_rib(lbl, x, y, z, comment=None):
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

    asm.blank()

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

    asm.blank()

    # TODO: move this table elsewhere, so the ribs for strings and instructions form a monolithic
    # block of address space?
    asm.comment("Table of pointers to symbol name ribs in ROM:")
    asm.label("symbol_names_start")
    for lbl, s in sym_names:
        if s != "":
            asm.comment(f'"{s}"')
        asm.instr(f"@{lbl}")
    asm.label("symbol_names_end")

    asm.blank()

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
        return f"#{big.HEAP_BASE + 6*(len(sym_names) - idx)}"

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
        n = x
        d = 0
        op = 0

        while True:
            d = [20, 30, 0, 10, 11, 4][op]
            if n <= 2+d: break
            n -= d+3; op += 1

        if x > 90:
            n = pop()
        else:
            if op == 0:
                push("#0")
                op += 1

            if n == d:
                n = f"#{get_int(0)}"
            elif n >= d:
                idx = get_int(n-d-1)
                n = symbol_ref(idx)
            elif op < 3:
                n = symbol_ref(n)

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
    # emit_rib("main", "#0", start_instr, "#0", comment=f"jump {start_instr}")
    # Note: there is no true no-op, and "id" is not yet initialized. This will leave junk on the
    # stack. What we really want is to put the "main" label on start_instr when it's emitted.
    emit_rib("main", "#3", "#-42", start_instr)


BUILTINS = {
    **big.BUILTIN_SYMBOLS,

    # Low-memory "registers":
    "SP": 0,
    "PC": 1,
    "NEXT_RIB": 2,

    "SYMBOL_TABLE": 4,  # Only used during intiialization?

    # General-purpose temporary storage:
    "TEMP_0": 5,
    "TEMP_1": 6,

    # Useful values/addresses:
    "FIRST_RIB_MINUS_ONE": big.HEAP_BASE-1,
    "MAX_RIB": big.HEAP_TOP,

    # The largest value that can ever by the index of a slot, as opposed to the address of a global (symbol)
    "MAX_SLOT": big.ROM_BASE-1,
}


def interpreter(asm):
    """ROM program implementing the RVM runtime, which interprets a program stored as "ribs" in ROM and RAM.

    This part of the ROM is the same, independent of the Scheme program that's being interpreted.
    """

    # Interpreter variables in low memory:
    # SP = 0
    # PC = 1
    # NEXT_RIB = 2

    # RETURN = 3

    # used only during initialization?
    # SYMBOL_TABLE = 4

    num_primitives = 22
    # FIRST_PRIMITIVE = 8
    # LAST_PRIMITIVE = FIRST_PRIMITIVE + num_primitives

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

        asm.instr("@NEXT_RIB")
        asm.instr("M=M+1")
        asm.instr("A=M-1")
        asm.instr(f"M={val}")


    # TODO: find end of encoded program; initialize stack pointer below it
    # decode_stack_start = 16384//2 - 1
    # asm.comment("SP = below the encoded program")
    # asm.instr(f"@{decode_stack_start}")
    # asm.instr("D=A")
    # asm.instr(f"@{SP}")
    # asm.instr("M=D")

    asm.label("start")
    asm.comment("NEXT_RIB = FIRST_RIB (HEAP_BASE)")
    asm.instr("@FIRST_RIB_MINUS_ONE")  # Note: this value is one lower than the actual start of the heap, to fit in 15 bits
    asm.instr("D=A+1")                 # Tricky: add 1 to bring the address up to 0x8000
    asm.instr("@NEXT_RIB")
    asm.instr("M=D")
    asm.blank()

    asm.comment("Construct the symbol table in RAM:")
    asm.comment("SYMBOL_TABLE = '()")
    asm.instr("@rib_nil")
    asm.instr("D=A")
    asm.instr("@SYMBOL_TABLE")
    asm.instr("M=D")

    asm.comment("R5 = table start")
    asm.instr("@symbol_names_start")
    asm.instr("D=A")
    asm.instr("@TEMP_0")
    asm.instr("M=D")

    symbol_table_loop = "symbol_table_loop"
    asm.label(symbol_table_loop)

    asm.comment("DEBUG: log the pointer to tty")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@KEYBOARD")
    asm.instr("M=D")

    asm.comment("new symbol, with value = false")
    asm.instr("@rib_false")
    asm.instr("D=A")
    rib_append()
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    rib_append()
    asm.instr("@2")  # symbol
    asm.instr("D=A")
    rib_append()
    asm.blank()

    # TODO: these `pair` ribs are actually constant and could live in the ROM, with pre-computed
    # addresses pointing to the `symbol` ribs being allocated just above.
    # Actually, is this list even used by the library (`string->symbol`)?
    asm.comment("SYMBOL_TABLE = new pair")
    asm.comment("car = the rib we just wrote")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    rib_append()
    asm.comment("cdr = (old) SYMBOL_TABLE")
    asm.instr("@SYMBOL_TABLE")
    asm.instr("D=M")
    rib_append()
    rib_append("0")  # pair
    asm.blank()

    asm.comment("update SYMBOL_TABLE")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    asm.instr("@SYMBOL_TABLE")
    asm.instr("M=D")

    asm.comment("DEBUG: log NEXT_RIB to tty")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@KEYBOARD")
    asm.instr("M=D")

    asm.comment("increment R5")
    asm.instr("@TEMP_0")
    asm.instr("M=M+1")

    asm.comment("D = compare(R5, symbol_names_end)")
    asm.instr("D=M")
    asm.instr("@symbol_names_end")
    asm.instr("D=D-A")
    asm.instr(f"@{symbol_table_loop}")
    asm.instr("D;JLT")

    asm.blank()


    #
    # Initialize interpreter state:
    #

    asm.comment("SP = '()")
    asm.instr("@rib_nil")
    asm.instr("D=A")
    asm.instr("@SP")
    asm.instr("M=D")

    asm.comment("PC = @main")
    asm.instr("@main")
    asm.instr("D=A")
    asm.instr("@PC")
    asm.instr("M=D")

    asm.blank()

    #
    # Exec loop:
    #

    def pc_x_to_d():
        """Load the first field of the current instruction to D."""
        asm.instr("@PC")
        asm.instr("A=M")
        asm.instr("D=M")

    def pc_y_to_d():
        """Load the middle field of the current instruction to D."""
        asm.instr("@PC")
        asm.instr("A=M+1")
        asm.instr("D=M")

    def pc_z_to_d():
        """Load the last field of the current instruction to D."""
        # Note: could save an instruction here if the pointer pointed to the *middle* field.
        asm.instr("@PC")
        asm.instr("A=M+1")
        asm.instr("A=A+1")  # Cheeky: add two ones instead of using @2 to save a cycle
        asm.instr("D=M")

    asm.comment("First time: jump to the main loop")
    asm.instr("@exec_loop")
    asm.instr("0;JMP")

    asm.comment("Typical loop path: get the next instruction to interpret from the third field of the current instruction:")
    asm.label("continue_next")
    pc_z_to_d()
    asm.instr("@PC")
    asm.instr("M=D")

    asm.comment("sanity check: zero is never the address of a valid instr")
    asm.instr("@halt_loop")
    asm.instr("D;JEQ")
    asm.comment("...fallthrough")
    asm.blank()

    asm.label("exec_loop")

    asm.comment("Sanity check: negative instruction type is impossible")
    pc_x_to_d()
    asm.instr("@halt_loop")
    asm.instr("D;JLT")

    asm.instr("@code_gt_zero")
    asm.instr("D;JGT")

    asm.comment("type 0: jump/call")
    pc_z_to_d()
    asm.instr("@handle_call")
    asm.instr("D;JNE")
    pc_y_to_d()
    asm.instr(f"@MAX_SLOT")
    asm.instr("D=D-A")
    asm.instr("@handle_jump_to_slot")
    asm.instr("D;JLT")

    asm.comment("TODO: TEMP_? = target proc, ...")
    asm.instr("@halt_loop")
    # asm.instr("0;JMP")
    # asm.comment("HACK: PC = PC.y; bogus!")
    # y_to_d("PC")
    # asm.instr("@PC")
    # asm.instr("M=D")
    # asm.instr("@exec_loop")
    # asm.instr("0;JMP")
    asm.blank()

    asm.label("handle_jump_to_slot")
    asm.comment("TODO")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")


    asm.label("handle_call")
    asm.comment("TODO")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")


    asm.label("code_gt_zero")
    asm.instr("D=D-1")
    asm.instr("@code_gt_one")
    asm.instr("D;JGT")

    asm.comment("type 1: set")
    asm.comment("TODO")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")

    asm.label("code_gt_one")
    asm.instr("D=D-1")
    asm.instr("@code_gt_two")
    asm.instr("D;JGT")

    asm.comment("type 2: get")
    asm.comment("TODO")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")

    asm.label("code_gt_two")
    asm.instr("D=D-1")
    asm.instr("@code_gt_three")
    asm.instr("D;JGT")

    asm.comment("type 3: const")
    pc_y_to_d()
    asm.comment("TODO: check tag")
    asm.comment("Allocate rib: x = pc.y")
    rib_append()    asm.comment("y = SP")
    asm.instr("@SP")
    asm.instr("D=M")
    rib_append()
    asm.comment("z = 0 (pair)")
    rib_append("0")

    asm.comment("SP = just-allocated rib")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    asm.instr("@SP")
    asm.instr("M=D")

    asm.instr("@continue_next")
    asm.instr("0;JMP")

    asm.label("code_gt_three")
    asm.instr("D=D-1")
    asm.instr("@halt_loop")
    asm.instr("D;JGT")

    asm.comment("type 4: if")
    asm.comment("TODO")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")

    asm.blank()

    # asm.comment("TEMP: just go to 'next' no matter what")
    # asm.instr("@continue_next")
    # asm.instr("0;JMP")


    #
    # Halt:
    #

    halt_label = "halt_loop"
    asm.label(halt_label)
    asm.instr(f"@{halt_label}")
    asm.instr("0;JMP")


    #
    # Primitive handlers:
    #

    asm.label("primitive_rib")
    asm.comment("primitive 0; rib :: x y z -- rib(x, y, z)")
    asm.comment("TODO:")
    # asm.comment("- check for stack-heap collision")
    # asm.comment("- allocate space for new rib")
    # asm.comment("- pop three values and copy them into the new rib")
    asm.instr("@exec_loop")
    asm.instr("0;JMP")
    asm.blank()

    asm.comment("TODO: for now, all these just fall through to halt/unimp")
    asm.label("primitive_id")
    asm.comment("primitive 1; id :: x -- x")
    asm.label("primitive_arg1")
    asm.comment("primitive 2; arg1 :: x y -- x")
    asm.label("primitive_arg2")
    asm.comment("primitive 3; arg2 :: x y -- y")
    asm.label("primitive_close")
    asm.comment("primitive 4; close :: x -- rib(x[0], stack, 1)")
    asm.label("primitive_rib?")
    asm.comment("primitive 5; rib? :: x -- bool(x is a rib)")
    asm.label("primitive_field0")
    asm.comment("primitive 6; field0 :: rib(x, _, _) -- x")
    asm.label("primitive_field1")
    asm.comment("primitive 7; field1 :: rib(_, y, _) -- y")
    asm.label("primitive_field2")
    asm.comment("primitive 8; field2 :: rib(_, _, z) -- z")
    asm.label("primitive_field0-set!")
    asm.comment("primitive 9; field0-set! :: rib(_, y, z) x -- x (and update the rib in place: rib(x, y, z))")
    asm.label("primitive_field1-set!")
    asm.comment("primitive 10; field1-set! :: rib(x, _, z) y -- y (and update the rib in place: rib(x, y, z))")
    asm.label("primitive_field2-set!")
    asm.comment("primitive 11; field2-set! :: rib(x, y, _) z -- z (and update the rib in place: rib(x, y, z))")
    asm.label("primitive_eqv?")
    asm.comment("primitive 12; eqv? :: x y -- bool(x is identical to y)")
    asm.label("primitive_<")
    asm.comment("primitive 13; < :: x y -- bool(x < y)")
    asm.label("primitive_+")
    asm.comment("primitive 14; + :: x y -- x + y")
    asm.label("primitive_-")
    asm.comment("primitive 15; - :: x y -- x - y")
    asm.label("primitive_*")
    asm.comment("primitive 16; - :: x y -- x * y")
    asm.label("primitive_peek")
    asm.comment("primitive 19; peek :: x -- RAM[x]")
    asm.label("primitive_poke")
    asm.comment("primitive 20; poke :: x y -- y (and write the value y at RAM[x])")

    asm.label("primitive_halt")
    asm.comment("primitive 21; halt :: -- (no more instructions are executed)")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")

    asm.label("primitive_unimp")
    asm.comment("Note: the current instr will be logged if tracing is enabled")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")

    asm.comment("=== Primitive vectors ===")
    asm.label("primitive_vector_table_start")
    asm.comment("0")
    asm.instr("@primitive_rib")
    asm.comment("1")
    asm.instr("@primitive_id")
    asm.comment("2")
    asm.instr("@primitive_arg1")
    asm.comment("3")
    asm.instr("@primitive_arg2")
    asm.comment("4")
    asm.instr("@primitive_close")
    asm.comment("5")
    asm.instr("@primitive_rib?")
    asm.comment("6")
    asm.instr("@primitive_field0")
    asm.comment("7")
    asm.instr("@primitive_field1")
    asm.comment("8")
    asm.instr("@primitive_field2")
    asm.comment("9")
    asm.instr("@primitive_field0-set!")
    asm.comment("10")
    asm.instr("@primitive_field1-set!")
    asm.comment("11")
    asm.instr("@primitive_field2-set!")
    asm.comment("12")
    asm.instr("@primitive_eqv?")
    asm.comment("13")
    asm.instr("@primitive_<")
    asm.comment("14")
    asm.instr("@primitive_+")
    asm.comment("15")
    asm.instr("@primitive_-")
    asm.comment("16")
    asm.instr("@primitive_*")
    asm.comment("17 (quotient: not implemented)")
    asm.instr("@primitive_unimp")
    asm.comment("18 (getchar: not implemented)")
    asm.instr("@primitive_unimp")
    asm.comment("19 (putchar: not implemented)")
    asm.instr("@primitive_unimp")
    asm.comment("20")
    asm.instr("@primitive_peek")
    asm.comment("21")
    asm.instr("@primitive_poke")
    asm.comment("22")
    asm.instr("@primitive_halt")
    # fatal?
    asm.label("primitive_vectors_end")

    asm.blank()