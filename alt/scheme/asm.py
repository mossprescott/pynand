"""Ribbit interpreter, in hand-coded assembly.

This implementation is faster, but incomplete:
- missing primitives: *, quotient, ...
- no garbage-collector

Once the Jack interpreter is fully functional, this will probably just get deleted.
"""

from nand.translate import AssemblySource


def interpreter():
    """ROM program implementing the RVM runtime, which interprets a program stored as "ribs" in ROM and RAM.

    This part of the ROM is the same, independent of the Scheme program that's being interpreted.
    """

    asm = AssemblySource()

    RIB_PROC = "rib_rib"
    FALSE = "rib_false"
    TRUE = "rib_true"
    NIL = "rib_nil"

    def rib_append(val="D"):
        """Add a word to the rib currently being constructed.

        Always called three times in succession to construct a full rib.
        The value is either "D" (the default), or a value the ALU can produce (0 or 1, basically).
        """

        asm.instr("@NEXT_RIB")
        asm.instr("M=M+1")
        asm.instr("A=M-1")
        asm.instr(f"M={val}")

    def pop(dest):
        """Remove the top entry from the stack, placing the value in `dest`.

        Updates only SP and `dest`.
        """
        asm.comment("TODO: check SP.z == 0")
        asm.comment(f"{dest} = SP.x")
        asm.instr("@SP")
        asm.instr("A=M")
        asm.instr("D=M")
        asm.instr(f"@{dest}")
        asm.instr("M=D")
        asm.comment("SP = SP.y")
        asm.instr("@SP")
        asm.instr("A=M+1")
        asm.instr("D=M")
        asm.instr("@SP")
        asm.instr("M=D")

    def push(val="D"):
        """Add a new entry to the stack with the value from D (or 0 or 1, in case that's ever useful.)

        Updates SP and NEXT_RIB.
        """
        rib_append(val)
        asm.instr("@SP")
        asm.instr("D=M")
        rib_append()
        rib_append(0)  # pair
        asm.instr("@NEXT_RIB")
        asm.instr("D=M")
        asm.instr("@3")
        asm.instr("D=D-A")
        asm.instr("@SP")
        asm.instr("M=D")


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

    # asm.comment("DEBUG: log the pointer to tty")
    # asm.instr("@TEMP_0")
    # asm.instr("D=M")
    # asm.instr("@KEYBOARD")
    # asm.instr("M=D")
    # asm.instr("A=D")
    # asm.instr("D=M")
    # asm.instr("@KEYBOARD")
    # asm.instr("M=D")

    asm.comment("new symbol, with value = MEM(R5+1) and name = MEM(R5)")
    asm.instr("@TEMP_0")
    asm.instr("A=M+1")
    asm.instr("D=M")
    rib_append()
    asm.instr("@TEMP_0")
    asm.instr("A=M")
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

    # asm.comment("DEBUG: log NEXT_RIB to tty")
    # asm.instr("@NEXT_RIB")
    # asm.instr("D=M")
    # asm.instr("@KEYBOARD")
    # asm.instr("M=D")

    asm.comment("increment R5 (by 2)")
    asm.instr("@2")
    asm.instr("D=A")
    asm.instr("@TEMP_0")
    asm.instr("M=M+D")

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

    asm.comment("SP = primordial continuation rib")
    asm.instr("@rib_outer_cont")
    asm.instr("D=A")
    asm.instr("@SP")
    asm.instr("M=D")

    asm.blank()

    # Note: main is a meaningless instruction with its next the actual entry point, so it's actually
    # skipped on the way into the interpreter loop.
    asm.comment("PC = @main")
    asm.instr("@main")
    asm.instr("D=A")
    asm.instr("@PC")
    asm.instr("M=D")

    asm.blank()

    #
    # Exec loop:
    #

    def x_to_d(rib_addr_loc):
        """Load the first field of a rib to D."""
        asm.instr(f"@{rib_addr_loc}")
        asm.instr("A=M")
        asm.instr("D=M")

    def y_to_d(rib_addr_loc):
        """Load the middle field of a rib to D."""
        asm.instr(f"@{rib_addr_loc}")
        asm.instr("A=M+1")
        asm.instr("D=M")

    def z_to_d(rib_addr_loc):
        """Load the last field of a rib to D."""
        # Note: could save an instruction here if the pointer pointed to the *middle* field.
        asm.instr(f"@{rib_addr_loc}")
        asm.instr("A=M+1")
        asm.instr("A=A+1")  # Cheeky: add two ones instead of using @2 to save a cycle
        asm.instr("D=M")

    def d_is_not_slot():
        """Test if the value in D is a slot index, leaving 0 in D if so."""
        # FIXME: choose the correct boundary when tagged ints and pointers are implemented
        asm.instr("@0x03FF")  # Mask for bits that can be set in a number less than 2^10 = 1024
        asm.instr("A=!A")
        asm.instr("D=D&A")

    def find_cont(dest):
        """Loop over the stack to find the first continuation (a non-pair.)

        No registers are affected except `dest`.
        """

        cont_loop_test = asm.next_label("cont_loop_test")
        cont_loop_end = asm.next_label("cont_loop_end")

        asm.comment("R5 = RAM[SP]")
        asm.instr("@SP")
        asm.instr("D=M")
        asm.instr(f"@{dest}")
        asm.instr("M=D")
        asm.label(cont_loop_test)
        z_to_d(dest)
        asm.instr(f"@{cont_loop_end}")
        asm.instr("D;JNE")

        asm.comment("R5 = R5.y")
        y_to_d(dest)
        asm.instr(f"@{dest}")
        asm.instr("M=D")
        asm.instr(f"@{cont_loop_test}")
        asm.instr("0;JMP")

        asm.label(cont_loop_end)

    def find_slot(dest):
        """Loop over the stack to find the slot referred to by the current instruction, and placing
        the location of the object in the supplied destination.

        Overwrites TEMP_0.
        """
        assert dest != "TEMP_0"

        test_label = asm.next_label("slot_test")
        end_label = asm.next_label("slot_end")

        asm.comment("R5 = idx")
        y_to_d("PC")
        asm.instr("@TEMP_0")
        asm.instr("M=D")

        asm.comment(f"{dest} = SP")
        asm.instr("@SP")
        asm.instr("D=M")
        asm.instr(f"@{dest}")
        asm.instr("M=D")

        asm.label(test_label)
        asm.instr("@TEMP_0")
        asm.instr("D=M")
        asm.instr(f"@{end_label}")
        asm.instr("D;JLE")

        asm.comment(f"{dest} = cdr({dest})")
        asm.instr(f"@{dest}")
        asm.instr("A=M+1")
        asm.instr("D=M")
        asm.instr(f"@{dest}")
        asm.instr("M=D")
        # asm.instr("@KEYBOARD"); asm.instr("M=D") # DEBUG

        asm.comment("TEMP_0 -= 1")
        asm.instr("@TEMP_0")
        asm.instr("M=M-1")
        asm.instr(f"@{test_label}")
        asm.instr("0;JMP")

        asm.label(end_label)


    def unimp():
        asm.comment("TODO")
        asm.instr("@halt_loop")
        asm.instr("0;JMP")
        asm.blank()


    asm.comment("First time: start with the 'next' of main (by falling through to continue_next)")

    asm.comment("Typical loop path: get the next instruction to interpret from the third field of the current instruction:")
    asm.label("continue_next")
    z_to_d("PC")
    asm.instr("@PC")
    asm.instr("M=D")

    asm.comment("sanity check: zero is never the address of a valid instr")
    asm.instr("@halt_loop")
    asm.instr("D;JEQ")
    asm.comment("...fallthrough")
    asm.blank()

    asm.label("exec_loop")

    # TODO: if CHECK:
    asm.comment("Sanity check: instruction type between 0 and 5")
    x_to_d("PC")
    asm.instr("@halt_loop")
    asm.instr("D;JLT")
    asm.instr("@5")
    asm.instr("D=D-A")
    asm.instr("@halt_loop")
    asm.instr("D;JGT")

    # Note: this indexed jump doesn't seem to save any cycles vs 5 branches, but it's parallel
    # to the primitive handler dispatcher, so maybe easier to follow?
    asm.comment("indexed jump to instruction handler")
    x_to_d("PC")
    asm.instr("@opcode_handler_table")
    asm.instr("A=A+D")
    asm.instr("A=M")
    asm.instr("0;JMP")
    asm.blank()

    asm.label("opcode_handler_table")
    asm.instr("@opcode_0")
    asm.instr("@opcode_1")
    asm.instr("@opcode_2")
    asm.instr("@opcode_3")
    asm.instr("@opcode_4")
    asm.instr("@opcode_5")
    asm.blank()

    asm.label("opcode_0")
    asm.comment("type 0: jump/call")

    asm.comment("TEMP_3 = address of the proc rib")
    y_to_d("PC")
    d_is_not_slot()
    asm.instr("@proc_from_slot")
    asm.instr("D;JEQ")

    asm.label("proc_from_global")
    asm.comment("TEMP_3 = proc rib from symbol")
    y_to_d("PC")
    asm.instr("A=D")  # HACK: just load it to A from the instr?
    asm.instr("D=M")
    asm.instr("@TEMP_3")
    asm.instr("M=D")
    asm.instr("@handle_proc_start")
    asm.instr("0;JMP")
    asm.blank()

    asm.label("proc_from_slot")
    asm.comment("TEMP_3 = proc rib from stack")
    find_slot("TEMP_3")
    asm.instr("@TEMP_3")  # This has the address of the symbol
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr("@TEMP_3")  # Now update to the value (the proc)
    asm.instr("M=D")
    asm.blank()

    asm.label("handle_proc_start")
    asm.instr("D=D")  # no-op to make the label traceable

    # TODO: if type_checking:
    asm.label("check_proc_rib")
    # asm.instr("@TEMP_3"); asm.instr("D=M"); asm.instr("@KEYBOARD"); asm.instr("M=D")  # DEBUG
    z_to_d("TEMP_3")
    asm.instr("D=D-1")
    asm.instr("@halt_loop")
    asm.instr("D;JNE")
    asm.blank()

    asm.comment("Now if next is 0 -> jump; otherwise -> call")
    z_to_d("PC")
    asm.instr("@handle_call")
    asm.instr("D;JNE")

    asm.label("handle_jump")

    asm.comment("Check primitive or closure:")
    asm.instr("@TEMP_3")
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr("@0x1F")  # Mask off bits that are zero iff it's a primitive
    asm.instr("A=!A")
    asm.instr("D=D&A")
    asm.instr("@handle_jump_to_closure")
    asm.instr("D;JNE")

# when a primitive is called through a jump instruction, ... before the result is pushed to
# the stack the RVM’s stack and pc variables are updated according to the continuation in
# the current stack frame which contains the state of those variables when the call was
# executed (the details are given in Section 2.7).
    asm.label("handle_jump_to_primitive")
    asm.comment("set target to continue after handling the op")
    asm.instr("@after_primitive_for_jump")
    asm.instr("D=A")
    asm.instr("@PRIMITIVE_CONT")
    asm.instr("M=D")
    asm.instr("@handle_primitive")
    asm.instr("0;JMP")

    asm.label("after_primitive_for_jump")

    asm.comment("find the continuation rib: first rib on stack with non-zero third field")
    find_cont("TEMP_0")

    asm.comment("overwrite the top stack entry: SP.y = R5.x")
    x_to_d("TEMP_0")
    asm.instr("@SP")
    asm.instr("A=M+1")
    asm.instr("M=D")

    asm.comment("PC = R5.z")
    z_to_d("TEMP_0")
    asm.instr("@PC")
    asm.instr("M=D")
    asm.instr("@exec_loop")
    asm.instr("0;JMP")
    asm.blank()


    asm.label("handle_jump_to_closure")

    asm.comment("find the continuation rib: first rib on stack with non-zero third field")
    find_cont("TEMP_0")

    # New continuation rib. Can't update the existing continuation, in case it's the primordial
    # one, which is stored in ROM.
    # TODO: move it to RAM, so it can be updated in place?
    asm.comment("TEMP_1 = new continuation = (old.x, proc, old.z)")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@TEMP_1")
    asm.instr("M=D")

    asm.comment("New cont. saved stack = old.x")
    asm.instr("@TEMP_0")
    asm.instr("A=M")
    asm.instr("D=M")
    rib_append()
    asm.comment("New cont. proc = TEMP_3")
    asm.instr("@TEMP_3")
    asm.instr("D=M")
    rib_append()
    asm.comment("New cont. next instr = old.z")
    asm.instr("@TEMP_0")
    asm.instr("A=M+1")
    asm.instr("A=A+1")
    asm.instr("D=M")
    rib_append()

    def wrangle_closure_params():
        """Move num_args objects from the current stack to a new stack on top of a new continuation rib.

        The continuation rib is not modified (but the reference to it in TEMP_1 is overwritten.)

        Before:
        TEMP_3 = addr of proc rib
        TEMP_1 = addr of new continuation (just allocated)

        During:
        TEMP_2 = loop var: num args remaining
        TEMP_1 = loop var: top of new stack
        TEMP_0 = overwritten

        After:
        TEMP_1 = new top of stack
        """

        asm.comment("TEMP_2 = num_args (proc.x.x)")
        asm.instr("@TEMP_3")
        asm.instr("A=M")
        asm.instr("A=M")
        asm.instr("D=M")
        asm.instr("@TEMP_2")
        asm.instr("M=D")
        # asm.instr("@KEYBOARD"); asm.instr("M=D")  # DEBUG

        params_test = asm.next_label("params_test")
        params_end = asm.next_label("params_end")

        asm.label(params_test)
        asm.instr("@TEMP_2")
        asm.instr("D=M")
        asm.instr(f"@{params_end}")
        asm.instr("D;JLE")

        # TODO: modify the stack entry in place? And fix up SP, then
        asm.comment("pop one object and add it to the new stack")
        pop("TEMP_0")
        asm.instr("@TEMP_0")
        asm.instr("D=M")
        rib_append()
        asm.instr("@TEMP_1")
        asm.instr("D=M")
        rib_append()
        rib_append(0)

        asm.instr("@NEXT_RIB")
        asm.instr("D=M")
        asm.instr("@3")
        asm.instr("D=D-A")
        asm.instr("@TEMP_1")
        asm.instr("M=D")

        asm.instr("@TEMP_2")
        asm.instr("M=M-1")
        asm.instr(f"@{params_test}")
        asm.instr("0;JMP")
        asm.label(params_end)

    wrangle_closure_params()

    asm.comment("Put new stack in place: SP = TEMP_1")
    asm.instr("@TEMP_1")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("M=D")

    asm.comment("PC = proc.x.z")
    asm.instr("@TEMP_3")
    asm.instr("A=M")
    asm.instr("A=M+1")
    asm.instr("A=A+1")
    asm.instr("D=M")
    asm.instr("@PC")
    asm.instr("M=D")

    asm.instr("@exec_loop")
    asm.instr("0;JMP")
    asm.blank()

    # "next" is not 0, so this is a call
    asm.label("handle_call")

    asm.comment("Check primitive or closure:")
    asm.instr("@TEMP_3")
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr("@0x1F")  # Mask off bits that are zero iff it's a primitive
    asm.instr("A=!A")
    asm.instr("D=D&A")
    asm.instr("@handle_call_closure")
    asm.instr("D;JNE")

    asm.label("handle_call_primitive")
    asm.comment("set target to continue after handling the op")
    asm.instr("@continue_next")
    asm.instr("D=A")
    asm.instr("@PRIMITIVE_CONT")
    asm.instr("M=D")
    asm.instr("@handle_primitive")
    asm.instr("0;JMP")

    asm.label("handle_call_closure")

    asm.comment("R6 = new rib for the continuation")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@TEMP_1")
    asm.instr("M=D")
    rib_append(0)  # cont.x gets filled in later
    asm.instr("@TEMP_3")
    asm.instr("D=M")
    rib_append()  # cont.y = TEMP_3 (the proc rib)
    z_to_d("PC")
    rib_append()  # cont.z = pc.z (next instr after the call)
    asm.blank()

    wrangle_closure_params()

    asm.comment("TEMP_2 = SP (old stack to save)")
    asm.instr("@SP")
    asm.instr("D=M")
    asm.instr("@TEMP_2")
    asm.instr("M=D")
    asm.comment("SP = TEMP_1 (top of new stack)")
    asm.instr("@TEMP_1")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("M=D")
    asm.comment("cont.x = TEMP_2 (saved stack)")
    find_cont("TEMP_1")  # Hmm. Searching here just because we ran out of TEMPs to hold onto it
    asm.instr("@TEMP_2")
    asm.instr("D=M")
    asm.instr("@TEMP_1")
    asm.instr("A=M")
    asm.instr("M=D")

    asm.comment("PC = proc.x.z")
    asm.instr("@TEMP_3")
    asm.instr("A=M")
    asm.instr("A=M+1")
    asm.instr("A=A+1")
    asm.instr("D=M")
    asm.instr("@PC")
    asm.instr("M=D")

    asm.instr("@exec_loop")
    asm.instr("0;JMP")
    asm.blank()


    asm.label("opcode_1")
    asm.comment("type 1: set")
    y_to_d("PC")
    d_is_not_slot()
    asm.instr("@handle_set_slot")
    asm.instr("D;JEQ")

    asm.label("handle_set_global")
    asm.comment("R5 = address of symbol rib")
    y_to_d("PC")
    asm.instr("@TEMP_0")
    asm.instr("M=D")
    asm.comment("RAM[TEMP_0] = pop()")
    pop("TEMP_1")
    asm.instr("@TEMP_1")
    asm.instr("D=M")
    asm.instr("@TEMP_0")
    asm.instr("A=M")
    asm.instr("M=D")
    asm.instr("@continue_next")
    asm.instr("0;JMP")
    asm.blank()

    asm.label("handle_set_slot")
    unimp()

    asm.label("opcode_2")
    asm.comment("type 2: get")
    y_to_d("PC")
    d_is_not_slot()
    asm.instr("@handle_get_slot")
    asm.instr("D;JEQ")

    asm.label("handle_get_global")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@TEMP_0")
    asm.instr("M=D")
    y_to_d("PC")  # D = address of symbol
    asm.instr("A=D")  # TODO: load directly to A?
    asm.instr("D=M")  # D = object at symbol.x
    rib_append("D")
    asm.instr("@SP")
    asm.instr("D=M")
    rib_append("D")
    rib_append("0")  # pair
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("M=D")

    asm.instr("@continue_next")
    asm.instr("0;JMP")
    asm.blank()

    asm.label("handle_get_slot")
    find_slot("TEMP_3")
    asm.instr("@TEMP_3")  # This has the address of the stack entry
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr("@TEMP_3")  # Now update to the value
    asm.instr("M=D")
    asm.blank()

    # TODO: macro for push from TEMP
    asm.comment("push TEMP3")
    asm.instr("@TEMP_3")
    asm.instr("D=M")
    rib_append()
    asm.instr("@SP")
    asm.instr("D=M")
    rib_append()
    rib_append(0)
    asm.comment("SP = NEXT_RIB-3 (the one we just initialized)")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    asm.instr("@SP")
    asm.instr("M=D")

    asm.instr("@continue_next")
    asm.instr("0;JMP")
    asm.blank()

    asm.label("opcode_3")
    asm.comment("type 3: const")
    y_to_d("PC")
    asm.comment("TODO: check tag")
    asm.comment("Allocate rib: x = pc.y")
    rib_append()
    asm.comment("y = SP")
    asm.instr("@SP")
    asm.instr("D=M")
    rib_append()
    asm.comment("z = 0 (pair)")
    rib_append("0")
    asm.blank()

    asm.comment("SP = just-allocated rib")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    asm.instr("@SP")
    asm.instr("M=D")
    asm.blank()

    asm.instr("@continue_next")
    asm.instr("0;JMP")
    asm.blank()

    asm.label("opcode_4")
    asm.comment("type 4: if")
    pop("TEMP_0")
    asm.comment("TOS is #f; no branch")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@rib_false")
    asm.instr("D=D-A")
    asm.instr("@continue_next")
    asm.instr("D;JEQ")
    asm.comment("PC = PC.y")
    y_to_d("PC")
    asm.instr("@PC")
    asm.instr("M=D")
    asm.instr("@exec_loop")
    asm.instr("0;JMP")
    asm.blank()

    # Note: a safety check would have the same result, but this makes it explicit in case we ever
    # make those checks optional.
    asm.label("opcode_5")
    asm.comment("type 5: halt")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")
    asm.blank()

    #
    # Halt:
    #

    halt_label = "halt_loop"
    asm.label(halt_label)
    asm.instr(f"@{halt_label}")
    asm.instr("0;JMP")


    #
    # Primitive handling:
    #

    asm.label("handle_primitive")
    asm.instr("@TEMP_3")
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr("@primitive_vector_table_start")
    asm.instr("A=A+D")
    asm.instr("A=M")
    asm.instr("0;JMP")
    asm.blank()

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
    asm.comment("18")
    asm.instr("@primitive_getchar")
    asm.comment("19 (putchar: not implemented)")
    asm.instr("@primitive_unimp")
    asm.comment("20")
    asm.instr("@primitive_peek")
    asm.comment("21")
    asm.instr("@primitive_poke")
    asm.comment("22")
    asm.instr("@primitive_halt")
    # fatal?
    asm.comment("dummy handlers for 23-31 to simplify range check above:")
    for op in range(23, 32):
        asm.comment(f"{op} (dummy)")
        asm.instr("@primitive_unimp")
    asm.label("primitive_vectors_end")

    asm.blank()

    def return_from_primitive():
        asm.instr("@PRIMITIVE_CONT")
        asm.instr("A=M")
        asm.instr("0;JMP")
        asm.blank()

    asm.label("primitive_rib")
    asm.comment("primitive 0; rib :: x y z -- rib(x, y, z)")
    pop("TEMP_2")
    pop("TEMP_1")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    rib_append()
    asm.instr("@TEMP_1")
    asm.instr("D=M")
    rib_append()
    asm.instr("@TEMP_2")
    asm.instr("D=M")
    rib_append()

    # TODO: pop only two, then modify the top of stack in place to save one allocation
    asm.comment("push allocated rib")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@3")
    asm.instr("D=D-A")
    push("D")
    return_from_primitive()


    asm.label("primitive_id")
    asm.comment("primitive 1; id :: x -- x")
    asm.comment("... and, that's all folks")
    return_from_primitive()


    asm.label("primitive_arg1")
    asm.comment("primitive 2; arg1 :: x y -- x")  # i.e. "drop"
    asm.comment("Simply discard the top entry on the stack by updating SP")
    asm.instr("@SP")
    asm.instr("A=M+1")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_arg2")
    asm.comment("primitive 3; arg2 :: x y -- y")
    asm.comment("Discard the second entry on the stack by updating the top entry")
    asm.comment("D = the addr of the third entry from the top of the stack")
    asm.instr("@SP")
    asm.instr("A=M+1")
    asm.instr("A=M+1")
    asm.instr("D=M")
    asm.comment("SP.x = D")
    asm.instr("@SP")
    asm.instr("A=M+1")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_close")
    asm.comment("primitive 4; close :: x -- rib(x[0], stack, 1)")
    asm.comment("TEMP_0 = new closure/proc rib")
    asm.instr("@NEXT_RIB")
    asm.instr("D=M")
    asm.instr("@TEMP_0")
    asm.instr("M=D")
    asm.comment("TEMP_0.x = TOS.x")
    x_to_d("SP")
    asm.instr("A=D")
    asm.instr("D=M")
    rib_append()
    asm.comment("TEMP_0.y = SP.y")
    y_to_d("SP")
    rib_append()
    asm.comment("TEMP_0.z = 1 (proc type)")
    rib_append("1")
    asm.comment("Modify top stack entry in place")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_rib?")
    asm.comment("primitive 5; rib? :: x -- bool(x is a rib)")
    # FIXME: this test is super bogus. Need to implement tagged ints, and test the correct bit here.
    # For now, any value large enough to be a potential address

    is_rib_nonneg_label = asm.next_label("is_rib_nonneg")
    is_rib_true_label = asm.next_label("is_rib_true")

    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr(f"@{is_rib_nonneg_label}")
    asm.instr("D;JGE")
    asm.instr("D=-D")
    asm.label(is_rib_nonneg_label)
    asm.comment("If the (absolute) value is larger than the base address of the ROM, assume it's a rib address")
    asm.instr("@ROM")
    asm.instr("D=D-A")
    asm.instr(f"@{is_rib_true_label}")
    asm.instr("D;JGT")

    asm.instr("@rib_false")
    asm.instr("D=A")
    # FIXME: jump to shared copy of this common sequence
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()
    asm.label(is_rib_true_label)
    asm.instr("@rib_true")
    asm.instr("D=A")
    # FIXME: jump to shared copy of this common sequence
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_field0")
    asm.comment("primitive 6; field0 :: rib(x, _, _) -- x")
    asm.comment("Update in place: SP.x.x = SP.x.x.x")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("A=M")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_field1")
    asm.comment("primitive 7; field1 :: rib(_, y, _) -- y")
    asm.comment("Update in place: SP.x.x = SP.x.x.y")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("A=M+1")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_field2")
    asm.comment("primitive 8; field2 :: rib(_, _, z) -- z")
    asm.comment("Update in place: SP.x.x = SP.x.x.z")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("A=M+1")
    asm.instr("A=A+1")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_field0-set!")
    asm.comment("primitive 9; field0-set! :: rib(_, y, z) x -- x (and update the rib in place: rib(x, y, z))")
    asm.comment("TEMP_0 = pop() = x")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.comment("Update the rib in place: SP.x.x = x")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("A=M")
    asm.instr("M=D")
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_field1-set!")
    asm.comment("primitive 10; field1-set! :: rib(x, _, z) y -- y (and update the rib in place: rib(x, y, z))")
    asm.comment("TEMP_0 = pop() = y")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.comment("Update the rib in place: SP.x.y = y")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("A=M+1")
    asm.instr("M=D")
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_field2-set!")
    asm.comment("primitive 11; field2-set! :: rib(x, y, _) z -- z (and update the rib in place: rib(x, y, z))")
    asm.comment("TEMP_0 = pop() = x")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.comment("Update the rib in place: SP.x.x = x")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("A=M+1")
    asm.instr("A=A+1")
    asm.instr("M=D")
    # FIXME: jump to shared copy of this common sequence
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_eqv?")
    asm.comment("primitive 12; eqv? :: x y -- bool(x is identical to y)")
    asm.comment("TEMP_0 = pop() = y")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("D=D-M")
    eqv_true_label = asm.next_label("eqv_true")
    asm.instr(f"@{eqv_true_label}")
    asm.instr("D;JEQ")
    asm.instr("@rib_false")
    asm.instr("D=A")
    # FIXME: jump to shared copy of this common sequence
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()
    asm.label(eqv_true_label)
    asm.instr("@rib_true")
    asm.instr("D=A")
    # FIXME: jump to shared copy of this common sequence
    asm.comment("Update the top stack entry in place")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_<")
    asm.comment("primitive 13; < :: x y -- bool(x < y)")
    # TODO: if type_checking:
    asm.comment("TEMP_0 = pop() = y")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.comment("TEMP_0 -= (SP.x = x)")
    asm.instr("@SP")
    asm.instr("A=M")  # A = addr of SP.x
    asm.instr("D=D-M")  # D = y - x
    # Note: range of ints is limited, so true overflow doesn't happen?
    is_less_label = asm.next_label("is_less")
    asm.instr(f"@{is_less_label}")
    asm.instr("D;JGT")
    asm.instr("@rib_false")
    asm.instr("D=A")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()
    asm.label(is_less_label)
    asm.instr("@rib_true")
    asm.instr("D=A")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()

    asm.label("primitive_+")
    asm.comment("primitive 14; + :: x y -- x + y")
    # TODO: if type_checking:
    asm.comment("D = pop() = y")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.comment("SP.x += y")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=M+D")
    return_from_primitive()

    asm.label("primitive_-")
    asm.comment("primitive 15; - :: x y -- x - y")
    # TODO: if type_checking:
    asm.comment("D = pop() = y")
    pop("TEMP_0")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.comment("SP.x -= y")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=M-D")
    return_from_primitive()


    asm.label("primitive_*")
    asm.comment("primitive 16; * :: x y -- x * y")
    asm.comment("TEMP_0 = pop() = y")
    pop("TEMP_0")
    asm.comment("TEMP_1 = SP.x = x")
    x_to_d("SP")
    asm.instr("@TEMP_1")
    asm.instr("M=D")

    asm.comment("TEMP_2 = bit mask = 1")
    asm.instr("@TEMP_2")
    asm.instr("M=1")

    asm.comment("TEMP_3 = acc = 0")
    asm.instr("@TEMP_3")
    asm.instr("M=0")

    mul_test_label = asm.next_label("mul_test")
    mul_end_label = asm.next_label("mul_end")
    mul_next_label = asm.next_label("mul_next")

    asm.label(mul_test_label)
    asm.comment("if y == 0, exit")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr(f"@{mul_end_label}")
    asm.instr("D;JEQ")

    asm.comment("if y & mask != 0, acc += (shifted) x")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@TEMP_2")
    asm.instr("D=D&M")
    asm.instr(f"@{mul_next_label}")
    asm.instr("D;JEQ")

    asm.instr("@TEMP_1")
    asm.instr("D=M")
    asm.instr("@TEMP_3")
    asm.instr("M=D+M")

    asm.label(mul_next_label)
    asm.comment("y &= ~mask")
    asm.instr("@TEMP_2")
    asm.instr("D=!M")
    asm.instr("@TEMP_0")
    asm.instr("M=M&D")
    asm.comment("mask <<= 1")
    asm.instr("@TEMP_2")
    asm.instr("D=M")
    asm.instr("M=M+D")
    asm.comment("x <<= 1")
    asm.instr("@TEMP_1")
    asm.instr("D=M")
    asm.instr("M=M+D")

    asm.instr(f"@{mul_test_label}")
    asm.instr("0;JMP")

    asm.label(mul_end_label)
    asm.comment("SP.x = acc")
    asm.instr("@TEMP_3")
    asm.instr("D=M")
    asm.instr("@SP")
    asm.instr("A=M")
    asm.instr("M=D")
    return_from_primitive()


    asm.label("primitive_getchar")
    asm.comment("primitive 18: getchar :: -- <char from keyboard> (blocks until a key is pressed)")
    # Note: this will only catch keypresses that occur after the instruction is executed. For
    # a responsive shell, the check will have to incorporated into the interpreter loop.
    # It might even need to be be checked more often than once per instruction, since instructions
    # can take as long as hundreds of cycles.
    asm.comment("Loop until @KEYBOARD contains anything other than zero.")

    getchar_loop_label = asm.next_label("getchar_loop")

    asm.label(getchar_loop_label)
    asm.instr("@KEYBOARD")
    asm.instr("D=M")
    asm.instr(f"@{getchar_loop_label}")
    asm.instr("D;JEQ")

    push("D")
    return_from_primitive()


    asm.label("primitive_peek")
    asm.comment("primitive 19; peek :: x -- RAM[x]")
    unimp()


    asm.label("primitive_poke")
    asm.comment("primitive 20; poke :: x y -- y (and write the value y at RAM[x])")
    asm.comment("R5 = value")
    pop("TEMP_0")
    asm.comment("R6 = addr")
    pop("TEMP_1")
    asm.instr("@TEMP_0")
    asm.instr("D=M")
    asm.instr("@TEMP_1")
    asm.instr("A=M")
    asm.instr("M=D")
    push("D")
    return_from_primitive()


    asm.label("primitive_halt")
    asm.comment("primitive 21; halt :: -- (no more instructions are executed)")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")
    asm.blank()


    asm.label("primitive_unimp")
    asm.comment("Note: the current instr will be logged if tracing is enabled")
    asm.instr("@halt_loop")
    asm.instr("0;JMP")
    asm.blank()


    asm.label("interpreter_end")
    asm.blank()

    return asm
