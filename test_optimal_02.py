"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_02 import *

def test_halfAdder():
    assert gate_count(HalfAdder) == 5  # optimal, according to nandgame

def test_fullAdder():
    assert gate_count(FullAdder) == 9  # optimal, according to nandgame

def test_inc16():
    assert gate_count(Inc16) == 76  # ?

def test_add16():
    assert gate_count(Add16) == 140  # ?

def test_alu():
    assert gate_count(ALU) == 560  # ?
