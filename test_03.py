from project_03 import *

def test_dff():
    dff = run(DFF)
    
    assert dff.out == 0
    
    dff.store = 1
    dff.data = 1
    # TODO: 
    assert dff.out == 0  # Store not visible on the output yet

    dff.store = 0
    dff.data = 0    
    assert dff.out == 0  # Still not visible, and clearing data has no affect after store is lowered
    
    dff.clock = 1
    assert dff.out == 1  # Now the output has the new value
    
    dff.clock = 0
    assert dff.out == 1  # No change

    dff.clock = 1
    assert dff.out == 1  # Still no change
    
    dff.clock = 0
    assert dff.out == 1  # Still no change
    
    dff.store = 1
    dff.store = 0
    assert dff.out == 1  # Update, but not exposed yet
    
    dff.clock = 1
    assert dff.out == 0  # Now you can see the new value
    
    dff.clock = 0
    assert dff.out == 0  # No change
