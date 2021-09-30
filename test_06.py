#! /usr/bin/env pytest

from nand import run
from project_05 import CPU
from test_05 import ADD_PROGRAM, MAX_PROGRAM
import project_06

def test_asm_ops_add(parse_op=project_06.parse_op):
    ADD_ASM = [
        "@2",
        "D=A",
        "@3",
        "D=D+A",
        "@1",
        "M=D",
    ]
    for string, word in zip(ADD_ASM, ADD_PROGRAM):
        assert parse_op(string) == word


def test_asm_ops_max(parse_op=project_06.parse_op):
    MAX_ASM = [
        "@1",
        "D=M",
        "@2",
        "D=D-M",
        "@10",
        "D;JGT",
        "@2",
        "D=M",
        "@12",
        "0;JMP",
        "@1",
        "D=M",
        "@3",
        "M=D",
        "@14",
        "0;JMP",
    ]
    for string, word in zip(MAX_ASM, MAX_PROGRAM):
        assert parse_op(string) == word


def test_ops(parse_op=project_06.parse_op):
    """Test generated opcodes against the actual simulated CPU."""

    cpu = run(CPU)

    cpu.instruction = parse_op("@100")
    cpu.tick(); cpu.tock()
    assert cpu.addressM == 100

    cpu.instruction = parse_op("0;JMP")
    cpu.tick(); cpu.tock()
    assert cpu.pc == 100

    def compute(expr, d, a):
        cpu.instruction = parse_op(f"@{d}")
        cpu.tick(); cpu.tock()
        cpu.instruction = parse_op(f"D=A")
        cpu.tick(); cpu.tock()
        cpu.instruction = parse_op(f"@{a}")
        cpu.tick(); cpu.tock()
        cpu.instruction = parse_op(f"M={expr}")
        return cpu.outM

    assert compute("0",   12345, 23456) ==      0
    assert compute("1",   12345, 23456) ==      1
    assert compute("-1",  12345, 23456) ==     -1
    assert compute("D",   12345, 23456) ==  12345
    assert compute("A",   12345, 23456) ==  23456
    assert compute("!D",  12345, 23456) == -12346
    assert compute("!A",  12345, 23456) == -23457
    assert compute("-D",  12345, 23456) == -12345
    assert compute("-A",  12345, 23456) == -23456
    assert compute("D+1", 12345, 23456) ==  12346
    assert compute("A+1", 12345, 23456) ==  23457
    assert compute("D-1", 12345, 23456) ==  12344
    assert compute("A-1", 12345, 23456) ==  23455
    assert compute("D-A", 12345, 23456) == -11111
    assert compute("A-D", 12345, 23456) ==  11111
    assert compute("D+A", 12345, 23456) == -29735
    assert compute("D&A", 0b0011, 0b0101) == 0b0001
    assert compute("D|A", 0b0011, 0b0101) == 0b0111


def test_load_add():
    with open("examples/Add.asm") as f:
        ops, symbols, statics = project_06.assemble(f)
    assert ops == ADD_PROGRAM
    assert symbols == {}
    assert statics == {}


def test_load_max_no_symbols():
    with open("examples/MaxL.asm") as f:
        ops, symbols, statics = project_06.assemble(f)
    assert ops == MAX_PROGRAM
    assert symbols == {}
    assert statics == {}


def test_load_max():
    with open("examples/Max.asm") as f:
        ops, symbols, statics = project_06.assemble(f)
    assert ops == MAX_PROGRAM
    assert symbols == {"OUTPUT_FIRST": 10, "OUTPUT_D": 12, "INFINITE_LOOP": 14}
    assert statics == {}


def test_load_rect():
    with open("examples/RectL.asm") as f:
        ops1, symbols1, statics1 = project_06.assemble(f)
    assert len(ops1) == 25
    assert symbols1 == {}
    assert statics1 == {}

    with open("examples/Rect.asm") as f:
        ops2, symbols2, statics2 = project_06.assemble(f)
    assert len(ops2) == 25
    assert symbols2 == {"LOOP": 10, "INFINITE_LOOP": 23}
    assert statics2 == {"counter": 16, "address": 17}

    assert ops2 == ops1


def test_load_pong():
    with open("examples/PongL.asm") as f:
        ops1, symbols1, statics1 = project_06.assemble(f)
    assert len(ops1) == 27483
    assert symbols1 == {}
    assert statics1 == {}

    with open("examples/Pong.asm") as f:
        ops2, symbols2, statics2 = project_06.assemble(f)
    assert len(ops2) == 27483
    assert len(symbols2) == 882
    assert symbols2["main.main"] == 3837
    assert len(statics2) == 14
    assert statics2["ponggame.0"] == 16
    assert statics2["screen.0"] == 29

    assert ops2 == ops1
