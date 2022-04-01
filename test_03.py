#! /usr/bin/env pytest

import pytest

from nand import DFF, run, gate_count
from project_03 import *


def test_my_dff_legit():
    """The challenge is to implement DFF with only Nand gates."""
    assert list(gate_count(MyDFF).keys()) == ['nands']


# Tricky: certain simplifications change the evaluation order such that a latch defined on the
# raw clock signal doesn't behave predictably. For now, turning those optimizations off makes it
# work, but it seems like this exercise might need to be dropped.
@pytest.mark.parametrize("dff_type,opt", [(MyDFF, False), (DFF, True)])
def test_dff_coarse(dff_type, opt):
    """Test of DFF behavior when inputs are always stable across clock cycles.
    """

    dff = run(dff_type, optimize=opt)

    dff.tick(); dff.tock()
    assert dff.out == 0

    dff.in_ = 1
    assert dff.out == 0

    dff.tick(); dff.tock()
    assert dff.out == 1

    dff.in_ = 0
    assert dff.out == 1

    dff.tick(); dff.tock()
    assert dff.out == 0


# Tricky: certain simplifications change the evaluation order such that a latch defined on the
# raw clock signal doesn't behave predictably. For now, turning those optimizations off makes it
# work, but it seems like this exercise might need to be dropped.
@pytest.mark.parametrize("dff_type,opt", [(MyDFF, False), (DFF, True)])
def test_dff_fine(dff_type, opt):
    """Test of DFF behavior with varying signal timing.
    """

    dff = run(dff_type, optimize=opt)

    dff.tick(); dff.tock()
    assert dff.out == 0

    dff.in_ = 1
    assert dff.out == 0

    dff.tick()
    assert dff.out == 0
    dff.tock()
    assert dff.out == 1  # New value appears on the falling edge

    dff.in_ = 0
    assert dff.out == 1

    dff.tick()
    assert dff.out == 1
    dff.tock()
    assert dff.out == 0  # New value appears on the falling edge

    # Now adjust the input while the clock is high:
    dff.tick()
    assert dff.out == 0

    dff.in_ = 1
    assert dff.out == 0

    dff.tock()
    assert dff.out == 1  # New value appears on the falling edge, still

    dff.tick()
    assert dff.out == 1

    dff.tock()
    assert dff.out == 1

    # TODO: is this behavior good enough, or is it too sensitive to the order of applying signals?
    # FIXME: minimally need a way to update the clock that forces values to propagate, so you don't
    # have to inspect values to get the correct behavior. Probably by making clock special (and
    # global), and providing tick() and tock() to cycle it.


def test_bit_coarse():
    bit = run(Bit)

    assert bit.out == 0

    bit.load = 1
    bit.in_ = 1
    assert bit.out == 0  # New value not visible on the output yet

    bit.tick(); bit.tock()
    assert bit.out == 1  # Now you can see the new value

    bit.load = 0
    bit.in_ = 0
    bit.tick(); bit.tock()
    assert bit.out == 1  # No change

    bit.load = 1
    bit.in_ = 0
    assert bit.out == 1  # Not updated yet

    bit.tick(); bit.tock()
    assert bit.out == 0  # Now you can see the new value


def test_bit_fine():
    bit = run(Bit)

    assert bit.out == 0

    bit.load = 1
    bit.in_ = 1
    assert bit.out == 0  # New value not visible on the output yet

    # bit.load = 0
    # bit.in_ = 0
    # assert bit.out == 0  # Still not visible, and clearing data has no affect after store is lowered

    bit.tick()
    assert bit.out == 0  # No change

    bit.tock()
    assert bit.out == 1  # Now you can see the new value

    bit.tick()
    assert bit.out == 1  # Still no change

    bit.tock()
    assert bit.out == 1  # Still no change

    bit.load = 1
    bit.in_ = 0
    assert bit.out == 1  # Update, but not exposed yet

    bit.tick()
    assert bit.out == 1  # No change

    bit.tock()
    assert bit.out == 0  # Now you can see the new value


def test_register_legit():
    """The challenge is to implement Register from Nand and DFF."""
    assert gate_count(Register).keys() == set(['nands', 'dffs'])

def test_register():
    reg = run(Register)

    reg.in_ = 0
    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.load = 1
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.in_ = -32123
    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.in_ = 11111
    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == 0

    reg.in_ = -32123
    reg.load = 1
    reg.tick(); reg.tock()
    assert reg.out == -32123

    reg.load = 0
    reg.tick(); reg.tock()
    assert reg.out == -32123

    reg.in_ = -1
    reg.tick(); reg.tock()
    assert reg.out == -32123

    # TODO: more of the original test?


def ram_test(ram, size):
    # Distribute test values over the address space, but keep the total count small:
    addrs = [0] + list(range(1, size, size//33 + 1)) + [size-1]

    ram.load = 1
    for i in addrs:
        ram.in_ = i
        ram.address = i
        ram.tick(); ram.tock()
        assert ram.out == i

    ram.in_ = -1
    ram.load = 0
    for i in addrs:
        ram.address = i
        ram.tick(); ram.tock()  # Note: one-cycle latency is now expected for the "real" RAM
        assert ram.out == i


def test_ram8_legit():
    """The challenge is to implement RAM8 from Registers."""
    assert gate_count(RAM8).keys() == set(['nands', 'dffs'])

def test_ram8():
    ram = run(RAM8)
    ram_test(ram, 8)


def test_ram64_legit():
    """The challenge is to implement RAM64 from Registers."""
    assert gate_count(RAM64).keys() == set(['nands', 'dffs'])

def test_ram64():
    # Gate-level simulation is annoyingly slow for this large chip, so use the less
    # exacting but much more efficient codegen simulator:
    ram = run(RAM64, simulator='codegen')
    ram_test(ram, 64)


def test_ram512_legit():
    """The challenge is to implement RAM512 from Registers."""
    assert gate_count(RAM512).keys() == set(['nands', 'dffs'])

def test_ram512():
    # Gate-level simulation is annoyingly slow for this large chip, so use the less
    # exacting but much more efficient codegen simulator:
    ram = run(RAM512, simulator='codegen')
    ram_test(ram, 512)


# TODO: fix flattening and synthesis so this isn't so slow; the time's probably
# actually not in codegen or execution.
@pytest.mark.skip(reason="This is just too slow (about 40s.)")
def test_ram4k_legit():
    """The challenge is to implement RAM4K from Registers."""
    assert gate_count(RAM4K).keys() == set(['nands', 'dffs'])

@pytest.mark.skip(reason="This is just too slow (almost 5 minutes.)")
def test_ram4k():
    # Gate-level simulation is annoyingly slow for this large chip, so use the less
    # exacting but much more efficient codegen simulator:
    ram = run(RAM4K, simulator='codegen')
    ram_test(ram, 4096)


def test_ram16k_legit():
    # This large RAM has to be implemented as a wrapper around a Memory:
    assert True

def test_ram16K():
    ram = run(RAM16K)
    ram_test(ram, 16384)


def test_pc():
    pc = run(PC)

    pc.in_ = 0; pc.reset = 0; pc.load = 0; pc.inc = 0
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.inc = 1
    pc.tick(); pc.tock()
    assert pc.out == 1

    pc.in_ = -32123
    pc.tick(); pc.tock()
    assert pc.out == 2

    pc.load = 1
    pc.tick(); pc.tock()
    assert pc.out == -32123

    pc.load = 0
    pc.tick(); pc.tock()
    assert pc.out == -32122

    pc.tick(); pc.tock()
    assert pc.out == -32121

    pc.in_ = 12345; pc.load = 1; pc.inc = 0
    pc.tick(); pc.tock()
    assert pc.out == 12345

    pc.reset = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.reset = 0; pc.inc = 1
    pc.tick(); pc.tock()
    assert pc.out == 12345

    pc.reset = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.reset = 0; pc.load = 0
    pc.tick(); pc.tock()
    assert pc.out == 1

    pc.reset = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.in_ = 0; pc.reset = 0; pc.load = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.load = 0; pc.inc = 1
    pc.tick(); pc.tock()
    assert pc.out == 1

    pc.in_ = 22222; pc.reset = 1; pc.inc = 0
    pc.tick(); pc.tock()
    assert pc.out == 0
