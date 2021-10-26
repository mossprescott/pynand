#! /usr/bin/env pytest

import pytest

from nand import run
from nand.solutions import solved_05, solved_06, solved_10, solved_12
from nand.translate import translate_jack
import test_12, test_optimal_08

import alt.reg
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

    liveness, live_at_start = analyze_liveness(ir.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    if_stmt, = [s for s in liveness if isinstance(s.statement, If)]

    assert if_stmt.before == {"x", "y"}
    assert all([s.before == {"x"} for s in if_stmt.statement.when_true])
    assert all([s.before == {"y"} for s in if_stmt.statement.when_false])
    assert live_at_start == set()


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

    liveness, live_at_start = analyze_liveness(ir.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    x = {"x"}  # x is live
    no_x = set()  # nothing live

    while_stmt, = [s for s in liveness if isinstance(s.statement, While)]

    assert while_stmt.before == x
    assert all([s.before == x for s in while_stmt.statement.body])
    assert live_at_start == set()


def test_degenerate_loop_liveness():
    """Taken directly from KeyboardTest.jack, and answering the question, "Does anybody rely
    on local variables being initialized to zero?"
    """
    src = """
class Main {
    function void main() {
        var char key;
        var int x;

        // key is never initialized, and referred to only in the loop test.
        while (key = 0) {
            let key = Keyboard.keyPressed();
        }

        return;
    }
}"""

    ast = solved_10.parse_class(src)

    ir = flatten_class(ast)

    liveness, live_at_start = analyze_liveness(ir.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    key = {"key"}  # key is live
    no_key = set()  # nothing live

    while_stmt, = [s for s in liveness if isinstance(s.statement, While)]

    assert while_stmt.before == key
    assert all([s.before == no_key for s in while_stmt.statement.body])
    assert live_at_start == key


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

    sub = phase_two(flat_class.subroutines[0],  [Reg(i, "R", "?") for i in range(2)])

    print(sub)

    assert sub.num_vars == 0, "No locals on the stack"
    assert sub.body[-1] == Return(Reg(0, "R", "y")), "y is assigned to the first register"

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

    sub = phase_two(flat_class.subroutines[0], [Reg(i, "R", "?") for i in range(2)])

    print(sub)

    assert sub.num_vars == 0, "No locals on the stack"
    assert sub.body[0] == Eval(Reg(0, "R", "x"), Const(0)), "x is assigned to the first register"


def test_compare_edge_cases(platform=REG_PLATFORM, simulator='codegen'):
    """See test_07.test_compare_edge_cases, which uses naked VM ops, so has to be reproduced here."""

    def gen_expr(dst, left, op, right):
        return f"""
        let x = {left};
        let y = {right};
        let RAM[{dst}] = x {op} y;
"""

    def gen_test(dst, left, op, right):
        return f"""
        let x = {left};
        let y = {right};
        if (x {op} y) {{
            let RAM[{dst}] = true;
        }}
"""

    src = ("""
class Main {
    function void main() {
        var Array RAM;
        var int x, y;

        let RAM = 0;
"""
    + gen_expr(8000, -1000, "<", 2000)
    + gen_expr(8001, -20000, "<", 30000)  # overflows
    + gen_expr(8002, -1000, ">", 2000)
    + gen_expr(8003, -20000, ">", 30000)  # overflows

    + gen_test(8010, -1000, "<", 2000)
    + gen_test(8011, -20000, "<", 30000)  # overflows
    + gen_test(8012, -1000, ">", 2000)
    + gen_test(8013, -20000, ">", 30000)  # overflows

    # Finally, a spot-check for the pattern that gets translated to "<="
    + """
        let x = -20000;
        let y = 30000;
        let RAM[8021] = ~(x > y);  // x <= y

        if (~(x > y)) {  // x <= y
            let RAM[8031] = true;
        }

        return;
    }
}
""")

    print(src)

    # HACK: turn on the necessary option, in a gross way. If we had some kind of "compiler flags"
    # mechanism, this wouldn't be needed.
    saved_flag = alt.reg.PRECISE_COMPARISON
    alt.reg.PRECISE_COMPARISON = True
    try:
        translator = platform.translator()

        translator.preamble()

        translate_jack(translator, platform, src)

        test_12._translate_dependencies(translator, platform, [])

        translator.finish()

        translator.check_references()
    finally:
        alt.reg.PRECISE_COMPARISON = saved_flag


    computer = run(platform.chip, simulator=simulator)
    translator.asm.run(platform.assemble, computer, stop_cycles=10_000, debug=True)

    assert computer.peek(8000) == -1  # -1000 < 2000
    assert computer.peek(8001) == -1  # -20000 < 30000  (overflows)
    assert computer.peek(8002) == 0  # -1000 > 2000
    assert computer.peek(8003) == 0  # -20000 > 30000  (overflows)

    assert computer.peek(8010) == -1  # -1000 < 2000
    assert computer.peek(8011) == -1  # -20000 < 30000  (overflows)
    assert computer.peek(8012) == 0  # -1000 > 2000
    assert computer.peek(8013) == 0  # -20000 > 30000  (overflows)

    assert computer.peek(8021) == -1  # -20000 <= 30000  (overflows)
    assert computer.peek(8031) == -1  # -20000 <= 30000  (overflows)


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

    assert instruction_count < 21_550


def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(REG_PLATFORM)

    assert cycles < 19_200


def test_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(REG_PLATFORM)

    assert cycles < 60_000
