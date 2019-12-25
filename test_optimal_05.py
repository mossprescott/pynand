"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_05 import *

def test_memory_system():
    assert gate_count(MemorySystem) == {
        'nands': 171,  # ?
        'memories': 2,
    }

def test_cpu():
    assert gate_count(CPU) == {
        'nands': 1099,  # ?
        'flip_flops': 48,  # 3 registers
    }

def test_computer():
    assert gate_count(Computer) == {
        'nands': 1270,  # ?
        'flip_flops': 48,  # 3 registers
        'memories': 3,
        # 'keyboards': 1,
        # 'roms': 1,
    }