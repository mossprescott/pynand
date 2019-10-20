"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_02 import *

def test_halfAdder():
    assert gate_count(HalfAdder) == 6  # ?

def test_fullAdder():
    assert gate_count(FullAdder) == 15  # ?

def test_inc16():
    assert gate_count(Inc16) == 96  # ?

def test_add16():
    assert gate_count(Add16) == 1  # ?

def test_alu():
    assert gate_count(ALU) == 1  # ?
