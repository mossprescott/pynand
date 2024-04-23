#! /usr/bin/env python

"""Ribbit VM implementation.

Two interpreters are currently implemented:
- a faster, more compact, but incomplete interpreter, in hand-rolled assembly
- a slightly slower, larger, but almost completely functional version in Jack using the compiler
  in reg.py, which has been significantly enhanced for this purpose.

Neither interpreter provides garbage-collection yet.

RSC's encoded instruction stream is decoded (in Python) into ribs directly in the ROM, which
is both relatively efficient in time and space, and more realistic than loading a complex program
from some kind of I/O.

See http://www.iro.umontreal.ca/~feeley/papers/YvonFeeleyVMIL21.pdf for the general picture.
"""

from nand.translate import AssemblySource
from alt import big
from nand.vector import extend_sign, unsigned
from alt.scheme.inspector import Inspector
from alt.scheme import asm
from alt.scheme.tag import *

TRACE_NONE = 0
"""No logging of Ribbit instructions."""
TRACE_COARSE = 1
"""Log each Ribbit instruction before it's interpreted, with a summary of the stack and heap."""
TRACE_FINE = 2
"""Log at each branch point of the interpreter loop (in addition to the COARSE logging.)"""
TRACE_ALL = 3
"""Log every CPU instruction (in addition to COARSE and FINE logging.)"""

DEFAULT_PRINT_ASM = False
DEFAULT_TRACE_LEVEL = TRACE_COARSE


def run(program, interpreter, simulator, print_asm=DEFAULT_PRINT_ASM, trace_level=DEFAULT_TRACE_LEVEL, verbose_tty=True):
    encoded = compile(program)

    if print_asm:
        print(f"encoded program: {repr(encoded)}")

    run_compiled(encoded, interpreter, simulator, print_asm, trace_level, verbose_tty)

def assemble(encoded, interpreter, print_asm):
    if interpreter == "assembly":
        asm = asm_interpreter()
    elif interpreter == "jack":
        asm = jack_interpreter()
    else:
        raise Exception(f"Unknown interpreter: {interpreter}")

    decode(encoded, asm)

    if print_asm:
        for l in asm.pretty(big.ROM_BASE): print(l)
        print()

    if interpreter == "assembly":
        instrs, symbols, statics = big.assemble(asm.lines, min_static=None, builtins=BUILTINS)
        stack_loc =    BUILTINS["SP"]
        pc_loc =       BUILTINS["PC"]
        next_rib_loc = BUILTINS["NEXT_RIB"]
        interp_loop_addr = symbols.get("exec_loop")
        halt_loop_addr =   symbols.get("halt_loop")
    elif interpreter == "jack":
        from nand.solutions import solved_06
        builtins = {
            **solved_06.BUILTIN_SYMBOLS,
            **big.BUILTIN_SYMBOLS,
        }
        instrs, symbols, statics = big.assemble(asm.lines, builtins=builtins)
        stack_loc =    statics["interpreter.static_stack"]
        pc_loc =       statics["interpreter.static_pc"]
        next_rib_loc = statics["interpreter.static_nextRib"]
        interp_loop_addr = first_loop_in_function(symbols, "Interpreter", "main")
        halt_loop_addr =   first_loop_in_function(symbols, "Interpreter", "halt")
        unexpected_statics = [s for s in statics if (".static_" not in s)]
        if unexpected_statics != []:
            raise Exception(f"unexpected statics: {unexpected_statics}")

    assert symbols["start"] == big.ROM_BASE

    if print_asm:
        def show_map(label, m):
            print("\n".join(
                [ f"{label}:" ] +
                [ f"{addr:5d}:   {name}"
                  for name, addr in sorted(m.items(), key=lambda t: t[1])
                ] +
                [""]
            ))

        # show_map("Symbols", symbols)

        if statics != {}:
            show_map("Statics", statics)

    print_summary = True
    if print_summary:
        interpreter_words = symbols["interpreter_end"] - big.ROM_BASE
        program_words = len(instrs) - symbols["interpreter_end"]  # Note: includes at least 5 pre-defined ribs
        total_words = len(instrs) - big.ROM_BASE
        rom_capacity = big.HEAP_BASE - big.ROM_BASE
        print(f"Interpreter: {interpreter_words:5,d} ({100*interpreter_words/rom_capacity:2.1f}%)")
        print(f"Program:     {program_words:5,d} ({100*program_words/rom_capacity:2.1f}%)")
        print(f"Total ROM:   {total_words:5,d} ({100*total_words/rom_capacity:2.1f}%)")
        print()

    return instrs, symbols, stack_loc, pc_loc, next_rib_loc, interp_loop_addr, halt_loop_addr


def run_compiled(encoded, interpreter, simulator, print_asm=DEFAULT_PRINT_ASM, trace_level=DEFAULT_TRACE_LEVEL, verbose_tty=True):

    # FIXME: Ug
    instrs, symbols, stack_loc, pc_loc, next_rib_loc, interp_loop_addr, halt_loop_addr = assemble(encoded, interpreter, print_asm)

    symbols_by_addr = { addr: name for (name, addr) in symbols.items() }
    last_traced_exec = None
    ribs = 0

    def trace(computer, cycles):
        nonlocal last_traced_exec, ribs

        inspector = Inspector(computer, symbols, stack_loc)

        if (trace_level >= TRACE_COARSE
                and (computer.pc == interp_loop_addr or computer.pc == halt_loop_addr)):
            if last_traced_exec is None:
                print(f"{ribs:,d}; cycle {cycles:,d}:")
            else:
                print(f"{ribs:,d}; cycle {cycles:,d} (+{cycles - last_traced_exec:,d}):")
            last_traced_exec = cycles
            ribs += 1

            print(f"  stack ({inspector.show_addr(inspector.peek(stack_loc))}): {inspector.show_stack()}")

            next_rib = unsigned(inspector.peek(next_rib_loc))
            current_ribs = (next_rib - big.HEAP_BASE)//3
            max_ribs = (big.HEAP_TOP - big.HEAP_BASE)//3
            print(f"  heap: {current_ribs:3,d} ({100*current_ribs/max_ribs:0.1f}%)")
            print(f"  PC: {inspector.show_addr(inspector.peek(pc_loc))}")

            # # HACK?
            # print(f"  symbols (n..0): ({inspector.show_addr(inspector.peek(symbol_table_loc))}) {inspector.show_stack(inspector.peek(symbol_table_loc))}")
            # print(f"  ribs:")
            # for addr in range(big.HEAP_BASE, unsigned(inspector.peek(next_rib_loc)), 3):
            #     print(f"    @{addr}; {inspector.show_obj(addr, deep=False)}")

            print(f"  {inspector.show_instr(inspector.peek(pc_loc))}")
        elif trace_level >= TRACE_FINE and computer.pc in symbols_by_addr and computer.pc != halt_loop_addr:
            print(f"{cycles:3,d}: ({symbols_by_addr[computer.pc]})")
        elif trace_level >= TRACE_ALL:
            print(f"{cycles:3,d}: {computer.pc}")

    def meters(computer, cycles):
        inspector = Inspector(computer, symbols, stack_loc)
        next_rib = unsigned(inspector.peek(next_rib_loc))
        current_ribs = (next_rib - big.HEAP_BASE)//3
        max_ribs = (big.HEAP_TOP - big.HEAP_BASE)//3
        return {
            f"mem: {100*current_ribs/max_ribs:0.1f}%"
        }


    big.run(program=instrs,
            simulator=simulator,
            name="Scheme",
            halt_addr=halt_loop_addr,
            trace=trace if trace_level > TRACE_NONE else None,
            verbose_tty=verbose_tty,
            meters=meters)


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

    asm.comment("===  Data  ===")

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

    def current_address():
        return big.ROM_BASE + asm.instruction_count

    def pad_to_3():
        "Pad the instruction stream to a multiple of 3."
        needed = (3 - (current_address() % 3)) % 3
        if needed > 0:
            asm.comment("padding")
            for _ in range(needed): asm.instr("#0")
            asm.blank()

    def emit_rib(lbl, x, y, z, comment=None):
        pad_to_3()

        obj = tag_rib(current_address())

        asm.label(lbl)
        if comment:
            asm.comment(f"{comment} (r{abs(obj)})")
        else:
            asm.comment(f"(r{abs(obj)})")
        asm.instr(x)
        asm.instr(y)
        asm.instr(z)

        return obj

    def emit_pair(lbl, car, cdr, comment):             return emit_rib(lbl, car, cdr, "#0", comment)
    def emit_string(lbl, chars, count: int, comment):  return emit_rib(lbl, chars, f"#{count}", "#3", comment)

    # Three constants the runtime can refer to by name:
    def special(name):
        return emit_rib(name, "#0", "#0", "#5")
    false_obj = special("rib_false")
    true_obj = special("rib_true")
    nil_obj = special("rib_nil")
    asm.blank()


    # Strings for the symbol table, as constant ribs directly in the ROM:

    # One empty string that can be shared:
    string_empty_obj = emit_string("rib_string_empty", f"#{nil_obj}", 0, '""')

    # First byte(s): number of symbols without names
    n = get_int(0)
    sym_names = n*[("rib_string_empty", "")]

    asm.blank()

    accum = nil_obj
    acc_str = ""
    idx = 0
    while True:
        c = get_byte()
        if c == ord(",") or c == ord(";"):
            if acc_str == "":
                obj = string_empty_obj
            else:
                lbl = f"string_{idx}"
                obj = emit_string(lbl, f"#{accum}", len(acc_str), f'"{acc_str}"')
                idx += 1
            sym_names.insert(0, (obj, acc_str))

            accum = nil_obj
            acc_str = ""

            if c == ord(";"):
                break
        else:
            lbl = asm.next_label("char")
            char_obj = emit_pair(lbl, f"#{c}", f"#{accum}", f"'{chr(c)}'")
            accum = char_obj
            acc_str = chr(c) + acc_str

    asm.blank()

    # Pad the heap base to a multiple of three, and encode it:
    HEAP_BASE_OBJ = -((big.HEAP_BASE + 2) // 3)

    # Exactly one primitive proc rib is pre-defined: `rib`
    # As a completely over-the-top hack, the location of the symbol table in RAM is stashed in
    # the otherwise-unused second field.
    # Note: can't emit this rib until the size of the symbol_table is known, hence the odd sequence.
    rib_obj = tag_rib(current_address())
    asm.label("rib_rib")
    asm.instr("#0")
    asm.comment("Location of symtbl:")
    asm.instr(f"#{HEAP_BASE_OBJ - 2*len(sym_names) + 1}")
    asm.instr("#1")
    asm.blank()

    # TODO: move this table elsewhere, so the ribs for strings and instructions form a monolithic
    # block of address space?
    asm.comment("Table of pointers to symbol name and initial value ribs in ROM:")
    asm.label("symbol_names_start")
    sym_names_and_values = list(zip(
        sym_names,
        [rib_obj, false_obj, true_obj, nil_obj] + [false_obj]*(len(sym_names)-4)))
    for i in reversed(range(len(sym_names_and_values))):
        (obj, s), val = sym_names_and_values[i]
        asm.comment(f'{i}: "{s}" (r{abs(obj)} = r{abs(val)})')
        asm.instr(f"#{obj}")
        asm.instr(f"#{val}")
    asm.label("symbol_names_end")

    asm.blank()


    asm.blank()

    # Decode RVM instructions:

    pad_to_3()

    asm.comment("Instructions:")

    halt_obj = emit_rib("instr_halt", "#5", "#0", "#0", "halt (secret opcode)")

    # Primordial continuation:
    # x (stack) = []
    # y (proc) = 0
    # z (instr) = halt
    emit_rib("rib_outer_cont", f"#{nil_obj}", "#0", f"#{halt_obj}", "Bottom of stack: continuation to halt")


    stack = None
    def pop():
        nonlocal stack
        x, stack = stack
        return x
    def push(x):
        nonlocal stack
        stack = (x, stack)

    def symbol_ref(idx):
        """Statically resolve a reference to the symbol table, to an (encoded0 address in RAM where
        that rib will be allocated during initialization.

        The table is written from the end, and each entry is made of of two ribs, the `symbol`
        and a `pair`.
        """
        name = sym_names[idx][1]
        description = f'"{name}"({idx})'
        return HEAP_BASE_OBJ - 2*(len(sym_names) - idx - 1), description

    def emit_instr(op: int, arg: int, next: int, sym):
        obj = tag_rib(current_address())
        lbl = f"instr{abs(obj)}"

        asm.label(lbl)

        if sym is not None:
            target = sym
        else:
            target = arg

        if op == 0 and next == 0:
            asm.comment(f"jump {target}")
        elif op == 0:
            asm.comment(f"call {target} -> r{abs(next)}")
        elif op == 1:
            asm.comment(f"set {target} -> r{abs(next)}")
        elif op == 2:
            asm.comment(f"get {target} -> r{abs(next)}")
        elif op == 3:
            asm.comment(f"const {target} -> r{abs(next)}")
        elif op == 4:
            asm.comment(f"if -> r{abs(arg)} else r{abs(next)}")
        else:
            raise Exception(f"Unknown op: {op} ({arg}, {next})")

        asm.instr(f"#{op}")
        asm.instr(f"#{arg}")
        asm.instr(f"#{next}")

        return obj


    # For each encoded instruction, emit three words of data into the ROM:
    # - references to symbols are statically resolved to addresses in *RAM*,
    #   where the symbols will reside after initialization

    # ripped off from https://github.com/udem-dlteam/ribbit/blob/dev/src/host/py/rvm.py directly
    while True:
        if pos >= len(input)-1: break  # TEMP

        x = get_code()
        n = x
        d = 0
        op = 0

        sym = None

        while True:
            d = [20, 30, 0, 10, 11, 4][op]
            if n <= 2+d: break
            n -= d+3; op += 1

        if x > 90:
            n = pop()
        else:
            if op == 0:
                push(0)
                op += 1

            if n == d:
                n = get_int(0)
            elif n >= d:
                idx = get_int(n-d-1)
                n, sym = symbol_ref(idx)
            elif op < 3:
                n, sym = symbol_ref(n)

            if op > 4:
                # This is either a lambda, or the outer proc that wraps the whole program.
                body = pop()
                if not stack:
                    n = body
                    break
                else:
                    params_lbl = asm.next_label("params")
                    params_obj = emit_rib(params_lbl, f"#{n}", "#0", f"#{body}")
                    proc_label = asm.next_label("proc")
                    proc_obj = emit_rib(proc_label, f"#{params_obj}", f"#{nil_obj}", "#1")
                    n = proc_obj
                    op = 4

        instr_obj = emit_instr(op-1, n, pop(), sym)
        push(instr_obj)

        sym = None

    # This label _follows_ the start instruction:
    asm.label("main")


BUILTINS = {
    **big.BUILTIN_SYMBOLS,

    # Low-memory "registers":
    "SP": 0,
    "PC": 1,
    "NEXT_RIB": 2,   # TODO: "LAST_RIB" is more often useful; you write some values, then you save the address somewhere

    "PRIMITIVE_CONT": 3,  # where to go when primitive handler is done

    "SYMBOL_TABLE": 4,  # Only used during intiialization?

    # General-purpose temporary storage for the interpreter/primitives:
    "TEMP_0": 5,
    "TEMP_1": 6,
    "TEMP_2": 7,
    "TEMP_3": 8,

    # Useful values/addresses:
    "FIRST_RIB_MINUS_ONE": big.HEAP_BASE-1,
    "MAX_RIB": big.HEAP_TOP,

    # The largest value that can ever be the index of a slot, as opposed to the address of a global (symbol)
    # TODO: adjust for encoded rib pointers
    "MAX_SLOT": big.ROM_BASE-1,
}
"""Constants (mostly addresses) that are used in the generated assembly."""



def pad_addr(addr):
    """Pad an address to the nearest valid pointer (i.e. multiple of 3)."""

    return ((addr + 2) // 3) * 3


FIRST_RIB = pad_addr(BUILTINS["FIRST_RIB_MINUS_ONE"] + 1)
# assert BUILTINS["MAX_SLOT"] < tag_rib(FIRST_RIB)


def asm_interpreter():
    return asm.interpreter()


def jack_interpreter():
    from nand.solutions import solved_10
    from alt import reg

    asm = AssemblySource()

    def init_global(comment, addr, value):
        asm.comment(comment)
        if isinstance(value, int) and -1 <= value <= 1:
            asm.instr(f"@{addr}")
            asm.instr(f"M={value}")
        else:
            asm.instr(f"@{value}")
            asm.instr("D=A")
            asm.instr(f"@{addr}")
            asm.instr("M=D")

    # Because the base of the ROM isn't at address 0, we make it explicit for the assembler:
    asm.label("start")

    init_global("Jack stack pointer", "SP", 256)
    # Note: these two probably don't actually need to be initialized, but might contain garbage
    # and confuse debugging
    init_global("Jack frame pointer", "LCL", 0)
    init_global("Jack arg pointer", "ARG", 0)
    # THIS and THAT definitely don't need to be set up before the first function call
    asm.blank()

    translator = reg.Translator(asm)

    def load_class(path):
        with open(path) as f:
            src_lines = f.readlines()
        ast = solved_10.parse_class("".join(src_lines))

        ir = reg.compile_class(ast)

        translator.translate_class(ir)

    for cl in "Interpreter", "Obj", "Rib":
        load_class(f"alt/scheme/{cl}.jack")

    asm.label("interpreter_end")
    asm.blank()

    return asm


def first_loop_in_function(symbols, class_name, function_name):
    """Address of the first instruction labeled "loop_... found (probably) within the given function."""

    function_label = f"{class_name}.{function_name}".lower()
    symbols_by_addr = sorted((addr, name) for name, addr in symbols.items())
    ptr = 0
    while symbols_by_addr[ptr][1] != function_label:
        ptr += 1
    ptr += 1
    while not symbols_by_addr[ptr][1].startswith("loop_"):
        ptr += 1
    return symbols_by_addr[ptr][0]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Scheme source with text-mode display and keyboard")
    parser.add_argument("path", nargs=argparse.ONE_OR_MORE, help="Path to source (<file>.scm)")
    parser.add_argument("--simulator", action="store", default="codegen", help="One of 'vector' (slower, more precise); 'codegen' (faster, default); 'compiled' (experimental)")
    parser.add_argument("--trace", action="store_true", help="Print each Ribbit instruction as it is interpreted. Note: runs almost 3x slower.")
    parser.add_argument("--print", action="store_true", help="Print interpreter assembly and compiled instructions.")
    # TEMP: experimental for now
    parser.add_argument("--asm", action="store_true", help="Use the (partially-implemented) assembly interpreter.")

    args = parser.parse_args()

    src_lines = []
    for p in args.path:
        with open(p) as f:
            src_lines += [] + f.readlines()

    run("".join(src_lines),
        interpreter="jack" if not args.asm else "assembly",
        simulator=args.simulator,
        print_asm=args.print,
        trace_level=TRACE_COARSE if args.trace else TRACE_NONE)
        # trace_level=TRACE_FINE if args.trace else TRACE_NONE)


if __name__ == "__main__":
    main()
