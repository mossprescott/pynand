from nand import run
from project_06 import *
from test_05 import CPU, ADD_PROGRAM, MAX_PROGRAM

def test_asm_ops_add():
    ADD_ASM = [
        "@2",
        "D=A",
        "@3",
        "D=D+A",
        "@0",
        "M=D",
    ]
    for string, word in zip(ADD_ASM, ADD_PROGRAM):
        assert parse_op(string) == word


def test_asm_ops_max():
    MAX_ASM = [
        "@0",
        "D=M",
        "@1",
        "D=D-M",
        "@10",
        "D;JGT",
        "@1",
        "D=M",
        "@12",
        "0;JMP",
        "@0",
        "D=M",
        "@2",
        "M=D",
        "@14",
        "0;JMP",
    ]
    for string, word in zip(MAX_ASM, MAX_PROGRAM):
        assert parse_op(string) == word


def test_ops():
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
        add = assemble(f)
    assert add == ADD_PROGRAM


def test_load_max_no_symbols():
    with open("examples/MaxL.asm") as f:
        max_ = assemble(f)
    assert max_ == MAX_PROGRAM


def test_load_max():
    with open("examples/Max.asm") as f:
        max_ = assemble(f)
    assert max_ == MAX_PROGRAM


def test_load_rect():
    with open("examples/RectL.asm") as f:
        rect1 = assemble(f)
    assert len(rect1) == 25

    with open("examples/Rect.asm") as f:
        rect2 = assemble(f)
    assert len(rect2) == 25

    assert rect2 == rect1


def test_load_pong():
    with open("examples/PongL.asm") as f:
        pong1 = assemble(f)
    assert len(pong1) == 27483

    with open("examples/Pong.asm") as f:
        pong2 = assemble(f)
    assert len(pong2) == 27483

    assert pong2 == pong1
