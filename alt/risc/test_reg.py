#! /usr/bin/env pytest

from alt.risc.chip import RiSCComputer
import alt.risc.main
import alt.risc.reg
import test_07, test_08, test_12, test_optimal_08

import alt.reg as compiler
from nand import jack_ast


# Some simple statments should get translated with no extraneous copying:

def test_translate_simple_copy():
    x_reg = compiler.Reg(2, "r", "x")
    y_reg = compiler.Reg(3, "r", "y")
    stmt = compiler.Eval(y_reg, x_reg)
    assert translate_stmt(stmt) == ["addi r3 r2 0"]

def test_translate_copy_from_mem_reg():
    x_reg = compiler.Reg(2, "r", "x")
    sum_loc = compiler.Reg(12, "R", "sum")
    stmt = compiler.Eval(x_reg, sum_loc)
    assert translate_stmt(stmt) == ["lw r2 r0 12"]

def test_translate_copy_to_mem_reg():
    x_reg = compiler.Reg(2, "r", "x")
    sum_loc = compiler.Reg(12, "R", "sum")
    stmt = compiler.Eval(sum_loc, x_reg)
    assert translate_stmt(stmt) == ["sw r2 r0 12"]

def test_translate_simple_constant():
    x_reg = compiler.Reg(2, "r", "x")
    stmt = compiler.Eval(x_reg, compiler.Const(42))
    assert translate_stmt(stmt) == ["addi r2 r0 42"]

def test_translate_simple_load():
    """Note: no registers except the target are used."""
    x_reg = compiler.Reg(2, "r", "x")
    start_loc = compiler.Location("argument", 1, "start")
    stmt = compiler.Eval(x_reg, start_loc)
    assert translate_stmt(stmt) == ["lw r2 r0 2", "lw r2 r2 1"]

def test_translate_simple_store():
    """Note: using r7 as a temp."""
    x_reg = compiler.Reg(2, "r", "x")
    ptr_loc = compiler.Location("local", 3, "ptr")
    stmt = compiler.Store(ptr_loc, x_reg)
    assert translate_stmt(stmt) == ["lw r7 r0 1", "sw r2 r7 3"]

def test_translate_load_store():
    """Note: using r6 and r7 as temps, one of the few cases where that happens.
    If we want to avoid reserving two registers for temps, we would have to eliminate cases like
    this (by introducing a temp variable and allocating it to a register.)
    """
    start_loc = compiler.Location("argument", 2, "start")
    ptr_loc = compiler.Location("local", 3, "ptr")
    stmt = compiler.Store(ptr_loc, start_loc)
    assert translate_stmt(stmt) == [
        "lw r6 r0 2",  # r6 = ARG
        "lw r6 r6 2",  # r6 = start
        "lw r7 r0 1",  # r7 = LCL
        "sw r6 r7 3",  # ptr = r6
    ]

def test_translate_add_small_int():
    x_reg = compiler.Reg(2, "r", "x")
    stmt = compiler.Eval(x_reg, compiler.Binary(x_reg, jack_ast.Op("+"), compiler.Const(1)))
    assert translate_stmt(stmt) == ["addi r2 r2 1"]

def test_translate_subtract_small_int():
    x_reg = compiler.Reg(2, "r", "x")
    stmt = compiler.Eval(x_reg, compiler.Binary(x_reg, jack_ast.Op("-"), compiler.Const(13)))
    assert translate_stmt(stmt) == ["addi r2 r2 -13"]

def test_translate_subtract():
    """Note: using r7 as a temp, although it doesn't have to, but it doesn't add any cycles."""
    x_reg = compiler.Reg(2, "r", "x")
    y_reg = compiler.Reg(3, "r", "y")
    diff_reg = compiler.Reg(4, "r", "diff")
    stmt = compiler.Eval(diff_reg, compiler.Binary(x_reg, jack_ast.Op("-"), y_reg))
    assert translate_stmt(stmt) == [
        "nand r7 r3 r3",
        "addi r7 r7 1",
        "add r4 r2 r7",
    ]


def test_translate_simple_compare():
    """Note: using no temps."""
    x_reg = compiler.Reg(3, "r", "x")
    b_reg = compiler.Reg(5, "r", "x")
    stmt = compiler.Eval(b_reg, compiler.Binary(x_reg, jack_ast.Op("="), compiler.Const(0)))
    assert translate_stmt(stmt) == [
        "beq r3 r0 +2",   # compare with 0
        "addi r5 r0 0",   # result = false
        "beq r0 r0 +1",   # skip true case
        "addi r5 r0 -1",  # result = true
    ]

def test_translate_simple_write():
    """Note: using no temps."""
    x_reg = compiler.Reg(2, "r", "x")
    ptr_reg = compiler.Reg(3, "r", "ptr")
    stmt = compiler.IndirectWrite(ptr_reg, x_reg)
    assert translate_stmt(stmt) == ["sw r2 r3 0"]

def test_translate_write_lomem_addr():
    """Note: using r7."""
    x_reg = compiler.Reg(2, "r", "x")
    ptr_reg = compiler.Reg(11, "R", "ptr")
    stmt = compiler.IndirectWrite(ptr_reg, x_reg)
    assert translate_stmt(stmt) == [
        "lw r7 r0 11",
        "sw r2 r7 0",
    ]

def test_translate_write_lomem_value():
    """Note: using r6."""
    x_reg = compiler.Reg(12, "R", "x")
    ptr_reg = compiler.Reg(3, "r", "ptr")
    stmt = compiler.IndirectWrite(ptr_reg, x_reg)
    assert translate_stmt(stmt) == [
        "lw r6 r0 12",
        "sw r6 r3 0",
    ]

def test_translate_write_lomem_both():
    """Note: using r6 and r7."""
    x_reg = compiler.Reg(12, "R", "x")
    ptr_reg = compiler.Reg(9, "R", "ptr")
    stmt = compiler.IndirectWrite(ptr_reg, x_reg)
    assert translate_stmt(stmt) == [
        "lw r6 r0 12",  # r6 = R12 (x)
        "lw r7 r0 9",   # r7 = R9 (ptr)
        "sw r6 r7 0",   # mem[ptr] = x
    ]

def test_translate_push_small_int():
    """Note: using r6 as a temp."""
    stmt = compiler.Push(compiler.Const(31))
    assert translate_stmt(stmt) == [
        "addi r6 r0 31",
        "sw r6 r1 0",
        "addi r1 r1 1",
    ]

def test_translate_push_large_int():
    """One more cycle to load the high bits. Note: using r6 as a temp."""
    stmt = compiler.Push(compiler.Const(64+31))
    assert translate_stmt(stmt) == [
        "lui r6 64",
        "addi r6 r6 31",
        "sw r6 r1 0",
        "addi r1 r1 1",
    ]

def test_translate_push_large_round_int():
    """One less cycle to not load the low bits. Note: using r6 as a temp."""
    stmt = compiler.Push(compiler.Const(128))
    assert translate_stmt(stmt) == [
        "lui r6 128",
        "sw r6 r1 0",
        "addi r1 r1 1",
    ]

def test_translate_push_zero():
    """No temps; one less cycle."""
    stmt = compiler.Push(compiler.Const(0))
    assert translate_stmt(stmt) == [
        "sw r0 r1 0",
        "addi r1 r1 1",
    ]


def translate_stmt(stmt):
    """Run the translator with a single statement and extract just the fragment of assembly that
    was generated for it, not including any preamble or comments.
    """

    translator = alt.risc.reg.Translator()
    translator._handle(stmt)
    lines = translator.asm.lines

    start_index, = [i for (i, l) in enumerate(lines) if l.startswith("(start")]

    return [ l.strip() for l in lines[start_index+1:] if not l.startswith("//") ]


# All the "OS" tests work, because they compile and run complete Jack programs:

def test_array_lib():
    test_12.test_array_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_string_lib():
    test_12.test_string_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_memory_lib():
    test_12.test_memory_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_keyboard_lib():
    test_12.test_keyboard_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_output_lib():
    test_12.test_output_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_math_lib():
    test_12.test_math_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)

def test_screen_lib():
    test_12.test_screen_lib(platform=alt.risc.reg.RiSC_REG_PLATFORM)


def test_code_size_pong():
    instruction_count = test_optimal_08.count_pong_instructions(alt.risc.reg.RiSC_REG_PLATFORM)

    assert instruction_count < 10_150

def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(alt.risc.reg.RiSC_REG_PLATFORM)

    assert cycles < 11_000

def test_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(alt.risc.reg.RiSC_REG_PLATFORM)

    assert cycles < 22_500
