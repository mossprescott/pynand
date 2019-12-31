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
        assert asm_op(string) == word


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
        assert asm_op(string) == word
