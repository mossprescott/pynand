#! /usr/bin/env pytest

from alt.reg import *
from alt.reg import _Stmt_str
from nand.solutions import solved_10


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

            do Sys.wait();
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


def test_compile_average():
    with open("examples/project_11/Average/Main.jack") as f:
        src = "\n".join(f.readlines())
        average = solved_10.parse_class(src)

    main = average.subroutineDecs[0]
    # print(pprint_subroutine_dec(main))

    result = flatten_class(average)
    print(result)
    # print(pprint_subroutine_dec(result))

    liveness = analyze_liveness(result.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    print(f"need saving: {need_saving(liveness)}")

    assert False


def test_compile_arraytest():
    with open("examples/project_12/ArrayTest.jack") as f:
        src = "\n".join(f.readlines())
        array_test = solved_10.parse_class(src)

    main = array_test.subroutineDecs[0]
    print(pprint_subroutine_dec(main))

    result = flatten_class(array_test)
    print(result)
    # print(pprint_subroutine_dec(result))

    liveness = analyze_liveness(result.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    print(f"need saving: {need_saving(liveness)}")

    assert False


def test_compile_stringtest():
    with open("examples/project_12/StringTest.jack") as f:
        src = "\n".join(f.readlines())
        string_test = solved_10.parse_class(src)

    main = string_test.subroutineDecs[0]
    print(pprint_subroutine_dec(main))

    result = flatten_class(string_test)
    print(result)
    # print(pprint_subroutine_dec(result))

    liveness = analyze_liveness(result.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    print(f"need saving: {need_saving(liveness)}")

    assert False

def test_compile_mathtest():
    with open("examples/project_12/MathTest.jack") as f:
        src = "\n".join(f.readlines())
        math_test = solved_10.parse_class(src)

    main = math_test.subroutineDecs[0]
    # print(pprint_subroutine_dec(main))
    print(main)

    result = flatten_class(math_test)
    print(result)
    # print(pprint_subroutine_dec(result))

    liveness = analyze_liveness(result.subroutines[0].body)
    for s in liveness:
        print(_Stmt_str(s))

    print(f"need saving: {need_saving(liveness)}")

    promoted = Subroutine(result.subroutines[0].name,
        promote_locals(result.subroutines[0].body,
                        {Local("r"): Location("local", 0, "r")},
                        "p"))
    print(promoted)

    liveness2 = analyze_liveness(promoted.body)
    for s in liveness2:
        print(_Stmt_str(s))

    assert False
