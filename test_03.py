from project_03 import *

def dff_coarse_test(dff):
    """Test of DFF behavior when inputs are always stable across clock cycles.
    """

    assert dff.out == 0

    dff.in_ = 1
    assert dff.out == 0

    dff.tick(); dff.tock()
    assert dff.out == 1

    dff.in_ = 0
    assert dff.out == 1

    dff.tick(); dff.tock()
    assert dff.out == 0


def dff_fine_test(dff):
    """Test of DFF behavior with varying signal timing.
    """

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


def test_dynamic_dff_coarse():
    dff = run(DynamicDFF)
    dff_coarse_test(dff)

def test_dynamic_dff_fine():
    dff = run(DynamicDFF)
    dff_fine_test(dff)
    

def test_dff_coarse():
    dff = run(DFF)
    dff_coarse_test(dff)

def test_dff_fine():
    dff = run(DFF)
    dff_fine_test(dff)


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
    ram.load = 1
    for i in range(size):
        ram.in_ = i
        ram.address = i
        ram.tick(); ram.tock()
        assert ram.out == i

    ram.in_ = -1
    ram.load = 0
    for i in range(size):
        ram.address = i
        assert ram.out == i


def test_ram8():
    ram = run(RAM8)
    ram_test(ram, 8)


def test_ram64():
    ram = run(RAM64)
    ram_test(ram, 64)


def test_ram512():
    ram = run(RAM512)
    ram_test(ram, 512)


def test_ram4k():
    ram = run(RAM4K)
    ram_test(ram, 4096)


def test_ram16K():
    ram = run(RAM16K)
    ram_test(ram, 16384)


def test_pc():
    raise NotImplementedError()
