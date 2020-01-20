"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from nand import gate_count
from project_01 import *

def test_nand():
    assert gate_count(Nand)['nands'] == 1

def test_not():
    assert gate_count(Not)['nands'] == 1

def test_or():
    assert gate_count(Or)['nands'] == 3

def test_and():
    assert gate_count(And)['nands'] == 2

def test_xor():
    assert gate_count(Xor)['nands'] == 4

def test_mux():
    assert gate_count(Mux)['nands'] == 4

def test_dmux():
    assert gate_count(DMux)['nands'] == 5

def test_dmux4way():
    assert gate_count(DMux4Way)['nands'] == 14  # optimal?

def test_dmux8way():
    assert gate_count(DMux8Way)['nands'] == 31  # optimal?

def test_not16():
    assert gate_count(Not16)['nands'] == 16

def test_and16():
    assert gate_count(And16)['nands'] == 32

def test_mux16():
    assert gate_count(Mux16)['nands'] == 49  # optimal?

def test_mux4Way16():
    assert gate_count(Mux4Way16)['nands'] == 146 # optimal?

def test_mux8Way16():
    assert gate_count(Mux8Way16)['nands'] == 339 # optimal?
