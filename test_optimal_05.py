"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

from project_05 import *

def test_memory_system():
    assert gate_count(MemorySystem) == {
        'nands': 168,  # ?
        'memories': 2,
    }

def test_cpu():
    assert gate_count(CPU) == {
        'nands': -1,  # ?
        'flip_flops': 48,  # 3 registers
        'memories': 2,
    }

