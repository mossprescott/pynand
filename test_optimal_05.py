#! /usr/bin/env pytest

"""Tests of the efficiency/optimality of each component. Run these tests only if you're interested
in using the minimum number of gates and/or making the (theoretically) fastest circuits.
"""

import pytest

from nand import gate_count, run
from nand.syntax import chip
import project_05

def test_memory_system():
    assert gate_count(project_05.MemorySystem) == {
        'nands': 163,  # ?
        'rams': 2,
        'inputs': 1,
        'outputs': 1,
    }

@pytest.mark.parametrize("simulator", ["vector", "codegen"])
def test_memory_latency(simulator, memory=project_05.MemorySystem):
    """Verify timing constraints specified by the RAM component (and provided by the native
    implementations).
    """

    chip = run(memory, simulator=simulator)

    # Write a series of values to the first few addresses:
    # Note: all three inputs provided in the same cycle; throughput is 1 write/cycle.
    for i in range(10):
        chip.load = 1
        chip.address = i
        chip.in_ = i

        # The previous cycle's value is read:
        assert chip.out == (i-1 if i > 0 else 0)

        chip.ticktock()

    chip.load = 0
    chip.address = 0
    chip.ticktock()

    # Read each value, and verify timing:
    # Note: throughput is 1 read/cycle.
    for i in range(1, 10):
        # First, check the output when the address has not been updated since the previous cycle:
        assert chip.out == i-1

        # Now supply the address to be read on the _next_ cycle:
        chip.address = i

        # Even after applying the new address, the output still reflects the latched address:
        assert chip.out == i-1

        chip.ticktock()


def test_cpu():
    assert gate_count(project_05.CPU) == {
        'nands': 1099,  # ?
        'dffs': 48,  # 3 registers
    }

def test_computer():
    assert gate_count(project_05.Computer) == {
        'nands': 1262,  # ?
        'dffs': 48,  # 3 registers
        'roms': 1,
        'rams': 2,
        'inputs': 1,
        'outputs': 1,
    }
