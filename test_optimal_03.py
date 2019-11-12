"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_03 import *

def test_dff():
    assert gate_count(DFF) == 9  # ?

def test_bit():
    assert gate_count(Bit) == 13  # ?

def test_register():
    assert gate_count(Register) == 208  # ?

def test_ram8():
    assert gate_count(RAM8) == 2050  # ?

def test_ram64():
    assert gate_count(RAM64) == 16786  # ?

def test_ram512():
    assert gate_count(RAM512) == -1  # ?

def test_ram4k():
    assert gate_count(RAM4K) == -1  # ?

def test_ram16k():
    assert gate_count(RAM16K) == -1  # ?

