#! /usr/bin/env pytest

"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from nand import gate_count
from project_02 import *

def test_halfAdder():
    assert gate_count(HalfAdder)['nands'] == 5  # optimal, according to nandgame

def test_fullAdder():
    assert gate_count(FullAdder)['nands'] == 9  # optimal, according to nandgame

def test_inc16():
    assert gate_count(Inc16)['nands'] == 76  # ?

def test_add16():
    assert gate_count(Add16)['nands'] == 140  # ?

def test_zero16():
    assert gate_count(Zero16)['nands'] == 46  # ?

def test_alu():
    assert gate_count(ALU)['nands'] == 560  # ?
