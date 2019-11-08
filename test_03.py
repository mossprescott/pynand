from project_03 import *

def test_dff_coarse():
    """Test of DFF behavior when inputs are always stable across clock cycles.
    """
    
    dff = run(DFF)
    
    assert dff.out == 0
    
    dff.in_ = 1
    assert dff.out == 0

    ticktock(dff)
    assert dff.out == 1

    dff.in_ = 0
    assert dff.out == 1
    
    ticktock(dff)
    assert dff.out == 0


def test_dff_fine():
    """Test of DFF behavior with varying signal timing.
    """
    
    dff = run(DFF)
    
    assert dff.out == 0
    
    dff.in_ = 1
    assert dff.out == 0
    
    dff.clock = 1
    assert dff.out == 0
    dff.clock = 0
    assert dff.out == 1  # New value appears on the falling edge

    dff.in_ = 0
    assert dff.out == 1
    
    dff.clock = 1
    assert dff.out == 1
    dff.clock = 0
    assert dff.out == 0  # New value appears on the falling edge
    
    # Now adjust the input while the clock is high:
    dff.clock = 1
    assert dff.out == 0
    
    dff.in_ = 1
    assert dff.out == 0
    
    dff.clock = 0
    assert dff.out == 1  # New value appears on the falling edge, still
    
    dff.clock = 1
    assert dff.out == 1

    dff.clock = 0
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

    ticktock(bit)
    assert bit.out == 1  # Now you can see the new value

    bit.load = 0
    bit.in_ = 0
    ticktock(bit)
    assert bit.out == 1  # No change
    
    bit.load = 1
    bit.in_ = 0
    assert bit.out == 1  # Not updated yet
    
    ticktock(bit)
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
    
    bit.clock = 1
    assert bit.out == 0  # No change
    
    bit.clock = 0
    assert bit.out == 1  # Now you can see the new value

    bit.clock = 1
    assert bit.out == 1  # Still no change
    
    bit.clock = 0
    assert bit.out == 1  # Still no change
    
    bit.load = 1
    bit.in_ = 0
    assert bit.out == 1  # Update, but not exposed yet
    
    bit.clock = 1
    assert bit.out == 1  # No change
    
    bit.clock = 0
    assert bit.out == 0  # Now you can see the new value


def test_register():
    reg = run(Register)
    
    reg.in_ = 0
    reg.load = 0
    ticktock(reg)
    assert reg.out == 0

    reg.load = 1
    ticktock(reg)
    assert reg.out == 0

    reg.in_ = -32123
    reg.load = 0
    ticktock(reg)
    assert reg.out == 0
    
    reg.in_ = 11111
    reg.load = 0
    ticktock(reg)
    assert reg.out == 0
    
    reg.in_ = -32123
    reg.load = 1
    ticktock(reg)
    assert reg.out == -32123
    

def tick(inst):
    inst._vector._propagate()  # HACK
    inst.clock = 1
    inst._vector._propagate()  # HACK

def tock(inst):
    inst._vector._propagate()  # HACK
    inst.clock = 0
    inst._vector._propagate()  # HACK

def ticktock(inst):
    tick(inst)
    tock(inst)
