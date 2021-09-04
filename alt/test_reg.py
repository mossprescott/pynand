#! /usr/bin/env pytest

import pytest

from nand import run
from nand.solutions import solved_05, solved_06, solved_10, solved_12
import test_12, test_optimal_08

from alt.reg import *
from alt.reg import _Stmt_str


def test_if_liveness():
    src = """
class Main {
    function void main() {
        var int x, y;

        do Output.println();

        let x = 0;
        let y = 1;

        // One branch reads x, the other writes it.
        if (true) {
            let y = x;
        }
        else {
            let x = 2;
        }

        do Output.printInt(x);
        do Output.printInt(y);

        return;
    }
}"""

    ast = solved_10.parse_class(src)

    ir = flatten_class(ast)

    liveness = analyze_liveness(ir.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    if_stmt, = [s for s in liveness if isinstance(s.statement, If)]

    assert if_stmt.before == {"x", "y"}
    assert all([s.before == {"x"} for s in if_stmt.statement.when_true])
    assert all([s.before == {"y"} for s in if_stmt.statement.when_false])


def test_loop_liveness():
    src = """
class Main {
    function void main() {
        var int x;

        do Output.println();

        let x = 0;

        // In the body of this loop, x is first read, then assigned, then a subroutine call happens.
        // That means it's live at the end of the loop, including across the call, even though there's
        // no read below it in the code sequence.
        while (true) {
            let x = x + 1;

            do Sys.wait(x);
        }

        return;
    }
}"""

    ast = solved_10.parse_class(src)

    ir = flatten_class(ast)

    liveness = analyze_liveness(ir.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    x = {"x"}  # x is live
    no_x = set()  # nothing live

    while_stmt, = [s for s in liveness if isinstance(s.statement, While)]

    assert while_stmt.before == x
    assert all([s.before == x for s in while_stmt.statement.body])


def test_if_allocation():
    src = """
class Test {
    function void foo(int x) {
        var int y;
        let y = x + 2;
        if (y < x) {
            return x;
        }
        return y;
    }
}
"""
    ast = solved_10.parse_class(src)

    flat_class = flatten_class(ast)

    sub = phase_two(flat_class.subroutines[0])

    print(sub)

    assert sub.num_vars == 0, "No locals on the stack"
    assert sub.body[-1] == Return(Reg(0, "y")), "y is assigned to the first register"

def test_loop_allocation():
    src = """
class Test {
    function void main() {
        var int x;
        let x = 0;
        while (x < 10) {
            let x = x + 1;
        }
        return;
    }
}
"""
    ast = solved_10.parse_class(src)

    flat_class = flatten_class(ast)

    sub = phase_two(flat_class.subroutines[0])

    print(sub)

    assert sub.num_vars == 0, "No locals on the stack"
    assert sub.body[0] == Eval(Reg(0, "x"), Const(0)), "x is assigned to the first register"


def test_array_lib():
    test_12.test_array_lib(platform=REG_PLATFORM)

def test_string_lib():
    test_12.test_string_lib(platform=REG_PLATFORM)

def test_memory_lib():
    test_12.test_memory_lib(platform=REG_PLATFORM)

def test_keyboard_lib():
    test_12.test_keyboard_lib(platform=REG_PLATFORM)

def test_output_lib():
    test_12.test_output_lib(platform=REG_PLATFORM)

def test_math_lib():
    test_12.test_math_lib(platform=REG_PLATFORM)

def test_screen_lib():
    test_12.test_screen_lib(platform=REG_PLATFORM)

@pytest.mark.skip(reason="It's not clear what to assert here that proves anything.")
def test_sys_lib():
    test_12.test_sys_lib(platform=REG_PLATFORM)


def test_pong_instructions():
    instruction_count = test_optimal_08.count_pong_instructions(REG_PLATFORM)

    # compare to the project_08 solution (about 27k)
    assert instruction_count < 21_550


def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(REG_PLATFORM)

    # Note: this isn't deterministic, but it
    assert cycles < 16_600


def test_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(REG_PLATFORM)

    # compare to the project_08 solution (about 130k)
    assert cycles < 60_000
