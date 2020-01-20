from nand import run, unsigned
from project_01 import *

def test_nand():
    assert run(Nand, a=0, b=0).out == 1
    assert run(Nand, a=0, b=1).out == 1
    assert run(Nand, a=1, b=0).out == 1
    assert run(Nand, a=1, b=1).out == 0

def test_not():
    assert run(Not, in_=0).out == 1
    assert run(Not, in_=1).out == 0

def test_or():
    assert run(Or, a=0, b=0).out == 0
    assert run(Or, a=0, b=1).out == 1
    assert run(Or, a=1, b=0).out == 1
    assert run(Or, a=1, b=1).out == 1

def test_and():
    assert run(And, a=0, b=0).out == 0
    assert run(And, a=0, b=1).out == 0
    assert run(And, a=1, b=0).out == 0
    assert run(And, a=1, b=1).out == 1

def test_xor():
    assert run(Xor, a=0, b=0).out == 0
    assert run(Xor, a=0, b=1).out == 1
    assert run(Xor, a=1, b=0).out == 1
    assert run(Xor, a=1, b=1).out == 0

def test_mux():
    assert run(Mux, a=0, b=0, sel=0).out == 0
    assert run(Mux, a=0, b=0, sel=1).out == 0
    assert run(Mux, a=0, b=1, sel=0).out == 0
    assert run(Mux, a=0, b=1, sel=1).out == 1
    assert run(Mux, a=1, b=0, sel=0).out == 1
    assert run(Mux, a=1, b=0, sel=1).out == 0
    assert run(Mux, a=1, b=1, sel=0).out == 1
    assert run(Mux, a=1, b=1, sel=1).out == 1

def test_dmux():
    dmux00 = run(DMux, in_=0, sel=0)
    assert dmux00.a == 0 and dmux00.b == 0

    dmux01 = run(DMux, in_=0, sel=1)
    assert dmux01.a == 0 and dmux01.b == 0

    dmux10 = run(DMux, in_=1, sel=0)
    assert dmux10.a == 1 and dmux10.b == 0

    dmux11 = run(DMux, in_=1, sel=1)
    assert dmux11.a == 0 and dmux11.b == 1
    
def test_dmux4way():
    for sel in range(4):
        result = run(DMux4Way, in_=0, sel=sel)
        assert result.a == 0 and result.b == 0 and result.c == 0 and result.d == 0

    result = run(DMux4Way, in_=1, sel=0b00)
    assert result.a == 1 and result.b == 0 and result.c == 0 and result.d == 0

    result = run(DMux4Way, in_=1, sel=0b01)
    assert result.a == 0 and result.b == 1 and result.c == 0 and result.d == 0

    result = run(DMux4Way, in_=1, sel=0b10)
    assert result.a == 0 and result.b == 0 and result.c == 1 and result.d == 0

    result = run(DMux4Way, in_=1, sel=0b11)
    assert result.a == 0 and result.b == 0 and result.c == 0 and result.d == 1

def test_dmux8way():
    for sel in range(8):
        result = run(DMux8Way, in_=0, sel=sel)
        assert (result.a == 0 and result.b == 0 and result.c == 0 and result.d == 0
            and result.e == 0 and result.f == 0 and result.g == 0 and result.h == 0)

    result = run(DMux8Way, in_=1, sel=0b000)
    assert (result.a == 1 and result.b == 0 and result.c == 0 and result.d == 0
        and result.e == 0 and result.f == 0 and result.g == 0 and result.h == 0)

    result = run(DMux8Way, in_=1, sel=0b001)
    assert (result.a == 0 and result.b == 1 and result.c == 0 and result.d == 0
        and result.e == 0 and result.f == 0 and result.g == 0 and result.h == 0)

    result = run(DMux8Way, in_=1, sel=0b010)
    assert (result.a == 0 and result.b == 0 and result.c == 1 and result.d == 0
        and result.e == 0 and result.f == 0 and result.g == 0 and result.h == 0)

    result = run(DMux8Way, in_=1, sel=0b011)
    assert (result.a == 0 and result.b == 0 and result.c == 0 and result.d == 1
        and result.e == 0 and result.f == 0 and result.g == 0 and result.h == 0)

    result = run(DMux8Way, in_=1, sel=0b100)
    assert (result.a == 0 and result.b == 0 and result.c == 0 and result.d == 0
        and result.e == 1 and result.f == 0 and result.g == 0 and result.h ==0)

    result = run(DMux8Way, in_=1, sel=0b101)
    assert (result.a == 0 and result.b == 0 and result.c == 0 and result.d == 0
        and result.e == 0 and result.f == 1 and result.g == 0 and result.h == 0)
        
    result = run(DMux8Way, in_=1, sel=0b110)
    assert (result.a == 0 and result.b == 0 and result.c == 0 and result.d == 0
        and result.e == 0 and result.f == 0 and result.g == 1 and result.h == 0)

    result = run(DMux8Way, in_=1, sel=0b111)
    assert (result.a == 0 and result.b == 0 and result.c == 0 and result.d == 0
        and result.e == 0 and result.f == 0 and result.g == 0 and result.h == 1)

def test_not16():
    assert unsigned(run(Not16, in_=0b0000_0000_0000_0000).out) == 0b1111_1111_1111_1111
    assert unsigned(run(Not16, in_=0b1111_1111_1111_1111).out) == 0b0000_0000_0000_0000
    assert unsigned(run(Not16, in_=0b1010_1010_1010_1010).out) == 0b0101_0101_0101_0101
    assert unsigned(run(Not16, in_=0b0011_1100_1100_0011).out) == 0b1100_0011_0011_1100
    assert unsigned(run(Not16, in_=0b0001_0010_0011_0100).out) == 0b1110_1101_1100_1011

def test_and16():
    assert unsigned(run(And16, a=0b0000_0000_0000_0000, b=0b0000_0000_0000_0000).out) == 0b0000_0000_0000_0000
    assert unsigned(run(And16, a=0b0000_0000_0000_0000, b=0b1111_1111_1111_1111).out) == 0b0000_0000_0000_0000
    assert unsigned(run(And16, a=0b1111_1111_1111_1111, b=0b1111_1111_1111_1111).out) == 0b1111_1111_1111_1111
    assert unsigned(run(And16, a=0b1010_1010_1010_1010, b=0b0101_0101_0101_0101).out) == 0b0000_0000_0000_0000
    assert unsigned(run(And16, a=0b0011_1100_1100_0011, b=0b0000_1111_1111_0000).out) == 0b0000_1100_1100_0000
    assert unsigned(run(And16, a=0b0001_0010_0011_0100, b=0b1001_1000_0111_0110).out) == 0b0001_0000_0011_0100

def test_mux16():
    assert unsigned(run(Mux16, a=0b0000_0000_0000_0000, b=0b0000_0000_0000_0000, sel=0).out) == 0b0000_0000_0000_0000
    assert unsigned(run(Mux16, a=0b0000_0000_0000_0000, b=0b0000_0000_0000_0000, sel=1).out) == 0b0000_0000_0000_0000
    assert unsigned(run(Mux16, a=0b0000_0000_0000_0000, b=0b0001_0010_0011_0100, sel=0).out) == 0b0000_0000_0000_0000
    assert unsigned(run(Mux16, a=0b0000_0000_0000_0000, b=0b0001_0010_0011_0100, sel=1).out) == 0b0001_0010_0011_0100
    assert unsigned(run(Mux16, a=0b1001_1000_0111_0110, b=0b0000_0000_0000_0000, sel=0).out) == 0b1001_1000_0111_0110
    assert unsigned(run(Mux16, a=0b1001_1000_0111_0110, b=0b0000_0000_0000_0000, sel=1).out) == 0b0000_0000_0000_0000
    assert unsigned(run(Mux16, a=0b1010_1010_1010_1010, b=0b0101_0101_0101_0101, sel=0).out) == 0b1010_1010_1010_1010
    assert unsigned(run(Mux16, a=0b1010_1010_1010_1010, b=0b0101_0101_0101_0101, sel=1).out) == 0b0101_0101_0101_0101
    
def test_mux4way16():
    for i in range(4):
        assert run(Mux4Way16, a=0, b=0, c=0, d=0, sel=i).out == 0
    assert unsigned(run(Mux4Way16, a=11111, b=22222, c=33333, d=44444, sel=0b00).out) == 11111
    assert unsigned(run(Mux4Way16, a=11111, b=22222, c=33333, d=44444, sel=0b01).out) == 22222
    assert unsigned(run(Mux4Way16, a=11111, b=22222, c=33333, d=44444, sel=0b10).out) == 33333
    assert unsigned(run(Mux4Way16, a=11111, b=22222, c=33333, d=44444, sel=0b11).out) == 44444
    
def test_mux8way16():
    for i in range(4):
        assert run(Mux8Way16, a=0, b=0, c=0, d=0, e=0, f=0, g=0, h=0, sel=i).out == 0
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b000).out) == 11111
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b001).out) == 22222
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b010).out) == 33333
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b011).out) == 44444
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b100).out) == 55555
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b101).out) == 12345
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b110).out) == 23456
    assert unsigned(run(Mux8Way16, a=11111, b=22222, c=33333, d=44444, e=55555, f=12345, g=23456, h=34567, sel=0b111).out) == 34567
