"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_03 import *

def test_dff():
    assert gate_count(MyDFF) == {
        'nands': 9,  # ?
    }

def test_dynamic_dff():
    assert gate_count(DFF) == {
        'dffs': 1
    }

def test_bit():
    assert gate_count(Bit) == {
        'nands': 4,  # ?
        'dffs': 1
    }

def test_register():
    assert gate_count(Register) == {
        'nands': 64,  # ?
        'dffs': 16
    }

def test_ram8():
    assert gate_count(RAM8) == {
        'nands': 881,  # ?
        'dffs': 128
    }

def test_ram64():
    assert gate_count(RAM64) == {
        'nands': 7_417,  # ?
        'dffs': 1_024
    }

# def test_ram512():
#     assert gate_count(RAM512) == {
#         'nands': 60_946,  # Uh oh.
#         'flip_flops': 8_192
#     }
#
# def test_ram4k():
#     assert gate_count(RAM4K) == {
#         'nands': -1,  # ?
#         'flip_flops': 65_536
#     }

def test_ram16k():
    assert gate_count(RAM16K) == {
        'rams': 1
    }

def test_pc():
    assert gate_count(PC) == {
        'nands': 287,
        'dffs': 16
    }
