from project_01 import *

def test_nand():
    assert eval(Nand, a=0, b=0).out == 1
    assert eval(Nand, a=0, b=1).out == 1
    assert eval(Nand, a=1, b=0).out == 1
    assert eval(Nand, a=1, b=1).out == 0

def test_not():
    assert eval(Not, in_=0).out == 1
    assert eval(Not, in_=1).out == 0

def test_or():
    assert eval(Or, a=0, b=0).out == 0
    assert eval(Or, a=0, b=1).out == 1
    assert eval(Or, a=1, b=0).out == 1
    assert eval(Or, a=1, b=1).out == 1

def test_and():
    assert eval(And, a=0, b=0).out == 0
    assert eval(And, a=0, b=1).out == 0
    assert eval(And, a=1, b=0).out == 0
    assert eval(And, a=1, b=1).out == 1

def test_xor():
    assert eval(Xor, a=0, b=0).out == 0
    assert eval(Xor, a=0, b=1).out == 1
    assert eval(Xor, a=1, b=0).out == 1
    assert eval(Xor, a=1, b=1).out == 0

def test_mux():
    assert eval(Mux, a=0, b=0, sel=0).out == 0
    assert eval(Mux, a=0, b=0, sel=1).out == 0
    assert eval(Mux, a=0, b=1, sel=0).out == 0
    assert eval(Mux, a=0, b=1, sel=1).out == 1
    assert eval(Mux, a=1, b=0, sel=0).out == 1
    assert eval(Mux, a=1, b=0, sel=1).out == 0
    assert eval(Mux, a=1, b=1, sel=0).out == 1
    assert eval(Mux, a=1, b=1, sel=1).out == 1

def test_dmux():
    dmux00 = eval(DMux, in_=0, sel=0)
    assert dmux00.a == 0 and dmux00.b == 0

    dmux01 = eval(DMux, in_=0, sel=1)
    assert dmux00.a == 0 and dmux00.b == 0

    dmux10 = eval(DMux, in_=1, sel=0)
    assert dmux00.a == 1 and dmux00.b == 0

    dmux11 = eval(DMux, in_=1, sel=1)
    assert dmux00.a == 0 and dmux00.b == 1

# TODO: these require multi-bit inputs/outputs:
# DMux4Way
# DMux8Way
# Not16
# And16
# Mux16
# Mux4Way16
# Mux8Way16
