"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_03 import *

def test_dff():
    assert gate_count(DFF) == {
        'nands': 9,  # ?
        'flip_flops': 0
    }

def test_dynamic_dff():
    assert gate_count(DynamicDFF) == {
        'nands': 0,
        'flip_flops': 1
    }

def test_bit():
    assert gate_count(Bit) == {
        'nands': 4,  # ?
        'flip_flops': 1
    }

def test_register():
    assert gate_count(Register) == {
        'nands': 64,  # ?
        'flip_flops': 16
    }

def test_ram8():
    assert gate_count(RAM8) == {
        'nands': 898,  # ?
        'flip_flops': 128
    }

def test_ram64():
    assert gate_count(RAM64) == {
        'nands': 7570,  # ?
        'flip_flops': 1_024
    }

def test_ram512():
    assert gate_count(RAM512) == {
        'nands': -1,  # ?
        'flip_flops': 8_192
    }

def test_ram4k():
    assert gate_count(RAM4K) == {
        'nands': -1,  # ?
        'flip_flops': 65_536
    }

def test_ram16k():
    assert gate_count(RAM16K) == {
        'nands': -1,  # ?
        'flip_flops': 262_144
    }

