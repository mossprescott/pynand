from project_06 import *
from test_05 import ADD_PROGRAM, MAX_PROGRAM

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


def test_load_add():
    with open("project_06/Add.asm") as f:
        add = load_file(f)
    assert add == ADD_PROGRAM


def test_load_max_no_symbols():
    with open("project_06/MaxL.asm") as f:
        max_ = load_file(f)
    assert max_ == MAX_PROGRAM


def test_load_max():
    with open("project_06/Max.asm") as f:
        max_ = load_file(f)
    assert max_ == MAX_PROGRAM


def test_load_rect():
    with open("project_06/RectL.asm") as f:
        rect1 = load_file(f)
    assert len(rect1) == 25

    with open("project_06/Rect.asm") as f:
        rect2 = load_file(f)
    assert len(rect2) == 25

    assert rect2 == rect1


def test_load_pong():
    with open("project_06/PongL.asm") as f:
        pong1 = load_file(f)
    assert len(pong1) == 27483

    with open("project_06/Pong.asm") as f:
        pong2 = load_file(f)
    assert len(pong2) == 27483

    assert pong2 == pong1
