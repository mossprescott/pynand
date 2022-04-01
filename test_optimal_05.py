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

    # Set up the address for the first write:
    chip.address = 0
    chip.ticktock()

    chip.load = 1
    for i in range(0, 10):
        # Note: i is the address that we're writing now

        assert chip.out == 0   # always 0; hasn't been written yet

        chip.in_ = i        # value for _this_ write
        chip.address = i+1  # address for the _next_ write

        chip.ticktock()

    chip.address = 0
    chip.ticktock()

    chip.load = 0
    # Read each value, and verify timing:
    # Note: throughput is 1 read/cycle.
    for i in range(10):
        # First, check the output when the address has not been updated since the previous cycle:
        assert chip.out == i

        # Now supply the address to be read on the _next_ cycle:
        chip.address = i+1

        # Even after applying the new address, the output still reflects the latched address:
        assert chip.out == i

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
