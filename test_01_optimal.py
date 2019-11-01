"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_01 import *

def test_nand():
    assert gate_count(Nand) == 1
    pass

def test_not():
    assert gate_count(Not) == 1

def test_or():
    assert gate_count(Or) == 3

def test_and():
    assert gate_count(And) == 2

def test_xor():
    assert gate_count(Xor) == 4

def test_mux():
    assert gate_count(Mux) == 4

def test_dmux():
    assert gate_count(DMux) == 5

def test_dmux4way():
    assert gate_count(DMux4Way) == 20  #?

def test_dmux8way():
    assert gate_count(DMux8Way) == 40  #?

def test_not16():
    assert gate_count(Not16) == 16

def test_and16():
    assert gate_count(And16) == 32

def test_mux16():
    assert gate_count(Mux16) == 64

def test_mux4Way16():
    assert gate_count(Mux4Way16) == 4*32 #?

def test_mux8Way16():
    assert gate_count(Mux8Way16) == 8*32 #?
