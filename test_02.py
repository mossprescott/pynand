from project_02 import *

def test_halfAdder():
    result = eval(HalfAdder, a=0, b=0)
    assert result.sum == 0 and result.carry == 0

    result = eval(HalfAdder, a=0, b=1)
    assert result.sum == 1 and result.carry == 0

    result = eval(HalfAdder, a=1, b=0)
    assert result.sum == 1 and result.carry == 0

    result = eval(HalfAdder, a=1, b=1)
    assert result.sum == 0 and result.carry == 1

def test_fullAdder():
    result = eval(FullAdder, a=0, b=0, c=0)
    assert result.sum == 0 and result.carry == 0
    
    result = eval(FullAdder, a=0, b=0, c=1)
    assert result.sum == 1 and result.carry == 0
    
    result = eval(FullAdder, a=0, b=1, c=0)
    assert result.sum == 1 and result.carry == 0
    
    result = eval(FullAdder, a=0, b=1, c=1)
    assert result.sum == 0 and result.carry == 1
    
    result = eval(FullAdder, a=1, b=0, c=0)
    assert result.sum == 1 and result.carry == 0
    
    result = eval(FullAdder, a=1, b=0, c=1)
    assert result.sum == 0 and result.carry == 1
    
    result = eval(FullAdder, a=1, b=1, c=0)
    assert result.sum == 0 and result.carry == 1
    
    result = eval(FullAdder, a=1, b=1, c=1)
    assert result.sum == 1 and result.carry == 1

def test_inc16():
    assert eval(Inc16, in_= 0).out ==  1
    assert eval(Inc16, in_=-1).out ==  0
    assert eval(Inc16, in_= 5).out ==  6
    assert eval(Inc16, in_=-5).out == -4
    
def test_add16():
    assert eval(Add16, a=0, b=0).out == 0
    assert eval(Add16, a=0, b=-1).out == -1
    assert eval(Add16, a=-1, b=-1).out == -2
    # Note: values get sign extended for convenience, but here we strip
    # that off for easy hex comparison in these odd cases
    assert eval(Add16, a=0xAAAA, b=0x5555).out & 0xFFFF == 0xFFFF
    assert eval(Add16, a=0x3CC3, b=0x0FF0).out & 0xFFFF == 0x4CB3
    assert eval(Add16, a=0x1234, b=0x9876).out & 0xFFFF == 0xAAAA

    
def test_alu_nostat():
    pass

def test_alu():
    pass
