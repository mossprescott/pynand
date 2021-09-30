#! /usr/bin/env pytest

import pytest

from nand import run, jack_ast
from nand.solutions import solved_05, solved_06, solved_10, solved_12
import test_12, test_optimal_08

from alt.reduce import *


def test_unroll_multiply_10():
    src = jack_ast.BinaryExpression(
        jack_ast.VarRef("foo"),
        jack_ast.Op("*"),
        jack_ast.IntegerConstant(10))
    vars, stmts, expr = MultiplyByConstant().expression(src, name_gen)

    assert len(vars) == 1
    assert len(vars[0].names) == 2

    x = vars[0].names[0]
    x_ref = jack_ast.VarRef(x)
    acc = vars[0].names[1]
    acc_ref = jack_ast.VarRef(acc)
    assert stmts == [
        jack_ast.LetStatement(name=x, array_index=None, expr=jack_ast.VarRef("foo")),               # x = foo
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(x_ref, x_ref)),                 # acc = 2x
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(x_ref, plus(acc_ref, acc_ref))), # acc = x + 4x = 5x
    ]
    assert expr == plus(acc_ref, acc_ref)   # 10x

def test_unroll_multiply_minus_97():
    """In this case, we negate the result at the point of use, and we have to handle two leading
    one-bits.

    This choice of how to assemble the operations into statements is fairly arbitrary.

    For one thing, in a case like this it's not obvious whether it's better to add a tmp for the
    operand value or just use the variable we're given. But we happen to know that some compilers
    will generate more efficient code for a new temp than for, say, referring to an argument or
    field, so might as well give them the chance.
    """

    src = jack_ast.BinaryExpression(
        jack_ast.IntegerConstant(-97),
        jack_ast.Op("*"),
        jack_ast.VarRef("foo"))
    vars, stmts, expr = MultiplyByConstant().expression(src, name_gen)

    assert len(vars) == 1
    assert len(vars[0].names) == 2

    x = vars[0].names[0]
    x_ref = jack_ast.VarRef(x)
    acc = vars[0].names[1]
    acc_ref = jack_ast.VarRef(acc)
    assert stmts == [
        jack_ast.LetStatement(name=x, array_index=None, expr=jack_ast.VarRef("foo")),            # x = foo
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(x_ref, plus(x_ref, x_ref))), # acc = 3x
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(acc_ref, acc_ref)),          # acc = 6x
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(acc_ref, acc_ref)),          # acc = 12x
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(acc_ref, acc_ref)),          # acc = 24x
        jack_ast.LetStatement(name=acc, array_index=None, expr=plus(acc_ref, acc_ref)),          # acc = 48x
    ]
    assert expr == jack_ast.UnaryExpression(jack_ast.Op("-"), plus(x_ref, plus(acc_ref, acc_ref)))  # -(x + 96x)

def plus(l, r):
    return jack_ast.BinaryExpression(l, jack_ast.Op("+"), r)


# Note: the tests for project 12 are set up to test alternative Jack implementations;
# have to explicitly transform each one here.
def reduced(class_ast):
    return all_transforms.transform(inject_defs(class_ast, EXTRA_MATH), name_gen)


def test_array_lib():
    test_12.test_array_lib(array_class=reduced(solved_12._ARRAY_CLASS), platform=REDUCE_PLATFORM)

def test_string_lib():
    test_12.test_string_lib(string_class=reduced(solved_12._STRING_CLASS), platform=REDUCE_PLATFORM)

def test_memory_lib():
    test_12.test_memory_lib(memory_class=reduced(solved_12._MEMORY_CLASS), platform=REDUCE_PLATFORM)

def test_keyboard_lib():
    test_12.test_keyboard_lib(keyboard_class=reduced(solved_12._KEYBOARD_CLASS), platform=REDUCE_PLATFORM)

def test_output_lib():
    test_12.test_output_lib(output_class=reduced(solved_12._OUTPUT_CLASS), platform=REDUCE_PLATFORM)

def test_math_lib():
    test_12.test_math_lib(math_class=reduced(solved_12._MATH_CLASS), platform=REDUCE_PLATFORM)

def test_screen_lib():
    test_12.test_screen_lib(screen_class=reduced(solved_12._SCREEN_CLASS), platform=REDUCE_PLATFORM)

@pytest.mark.skip(reason="It's not clear what to assert here that proves anything.")
def test_sys_lib():
    test_12.test_sys_lib(platform=REDUCE_PLATFORM)


def test_pong_instructions():
    instruction_count = test_optimal_08.count_pong_instructions(REDUCE_PLATFORM)

    # compare to the project_08 solution (about 27k)
    assert instruction_count < 27_400


def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(REDUCE_PLATFORM)

    # Note: this isn't deterministic, but it
    assert cycles < 20_300


def test_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(REDUCE_PLATFORM)

    # compare to the project_08 solution (about 130k)
    assert cycles < 130_000
