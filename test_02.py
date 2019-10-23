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
    assert eval(ALU, x=0, y=-1, zx=1, nx=0, zy=1, ny=0, f=1, no=0).out == 0   # 0
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=1, ny=1, f=1, no=1).out == 1   # 1
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=1, ny=0, f=1, no=0).out == -1  # -1
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=1, ny=1, f=0, no=0).out == 0   # X
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=0, ny=0, f=0, no=0).out == -1  # Y
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=1, ny=1, f=0, no=1).out == -1  # !X
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=0, ny=0, f=0, no=1).out == 0   # !Y
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=1, ny=1, f=1, no=1).out == 0   # -X
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=0, ny=0, f=1, no=1).out == 1   # -Y
    assert eval(ALU, x=0, y=-1, zx=0, nx=1, zy=1, ny=1, f=1, no=1).out == 1   # X + 1
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=0, ny=1, f=1, no=1).out == 0   # Y + 1
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=1, ny=1, f=1, no=0).out == -1  # X-1
    assert eval(ALU, x=0, y=-1, zx=1, nx=1, zy=0, ny=0, f=1, no=0).out == -2  # Y-1
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=0, ny=0, f=1, no=0).out == -1  # X + Y
    assert eval(ALU, x=0, y=-1, zx=0, nx=1, zy=0, ny=0, f=1, no=1).out == 1   # X - Y
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=0, ny=1, f=1, no=1).out == -1  # Y - X
    assert eval(ALU, x=0, y=-1, zx=0, nx=0, zy=0, ny=0, f=0, no=0).out == 0   # X & Y
    assert eval(ALU, x=0, y=-1, zx=0, nx=1, zy=0, ny=1, f=0, no=1).out == -1  # X | Y

    assert eval(ALU, x=23456, y=7890, zx=1, nx=0, zy=1, ny=0, f=1, no=0).out == 0          # 0
    assert eval(ALU, x=23456, y=7890, zx=1, nx=1, zy=1, ny=1, f=1, no=1).out == 1          # 1
    assert eval(ALU, x=23456, y=7890, zx=1, nx=1, zy=1, ny=0, f=1, no=0).out == -1         # -1
    assert eval(ALU, x=23456, y=7890, zx=0, nx=0, zy=1, ny=1, f=0, no=0).out == 23456      # X
    assert eval(ALU, x=23456, y=7890, zx=1, nx=1, zy=0, ny=0, f=0, no=0).out == 7890       # Y
    assert eval(ALU, x=0x5BA0, y=0x1ED2, zx=0, nx=0, zy=1, ny=1, f=0, no=1).out & 0xFFFF == 0xA45F # !X
    assert eval(ALU, x=0x5BA0, y=0x1ED2, zx=1, nx=1, zy=0, ny=0, f=0, no=1).out & 0xFFFF == 0xE12D # !Y
    assert eval(ALU, x=23456, y=7890, zx=0, nx=0, zy=1, ny=1, f=1, no=1).out == -23456     # -X
    assert eval(ALU, x=23456, y=7890, zx=1, nx=1, zy=0, ny=0, f=1, no=1).out == -7890      # -Y
    assert eval(ALU, x=23456, y=7890, zx=0, nx=1, zy=1, ny=1, f=1, no=1).out == 23457      # X + 1
    assert eval(ALU, x=23456, y=7890, zx=1, nx=1, zy=0, ny=1, f=1, no=1).out == 7891       # Y + 1
    assert eval(ALU, x=23456, y=7890, zx=0, nx=0, zy=1, ny=1, f=1, no=0).out == 23455      # X - 1
    assert eval(ALU, x=23456, y=7890, zx=1, nx=1, zy=0, ny=0, f=1, no=0).out == 7889       # Y - 1
    assert eval(ALU, x=23456, y=7890, zx=0, nx=0, zy=0, ny=0, f=1, no=0).out == 31346      # X + Y
    assert eval(ALU, x=23456, y=7890, zx=0, nx=1, zy=0, ny=0, f=1, no=1).out == 15566      # X - Y
    assert eval(ALU, x=23456, y=7890, zx=0, nx=0, zy=0, ny=1, f=1, no=1).out == -15566     # Y - X
    assert eval(ALU, x=0x5BA0, y=0x1ED2, zx=0, nx=0, zy=0, ny=0, f=0, no=0).out == 0x1A80  # X & Y
    assert eval(ALU, x=0x5BA0, y=0x1ED2, zx=0, nx=1, zy=0, ny=1, f=0, no=1).out == 0x5FF2  # X | Y


def test_alu():
# |        x         |        y         |zx |nx |zy |ny | f |no |       out        |zr |ng |
# | 0000000000000000 | 1111111111111111 | 1 | 0 | 1 | 0 | 1 | 0 | 0000000000000000 | 1 | 0 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 1 | 1 | 1 | 1 | 0000000000000001 | 0 | 0 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 1 | 0 | 1 | 0 | 1111111111111111 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 1 | 1 | 0 | 0 | 0000000000000000 | 1 | 0 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 0 | 0 | 0 | 0 | 1111111111111111 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 1 | 1 | 0 | 1 | 1111111111111111 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 0 | 0 | 0 | 1 | 0000000000000000 | 1 | 0 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 1 | 1 | 1 | 1 | 0000000000000000 | 1 | 0 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 0 | 0 | 1 | 1 | 0000000000000001 | 0 | 0 |
# | 0000000000000000 | 1111111111111111 | 0 | 1 | 1 | 1 | 1 | 1 | 0000000000000001 | 0 | 0 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 0 | 1 | 1 | 1 | 0000000000000000 | 1 | 0 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 1 | 1 | 1 | 0 | 1111111111111111 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 1 | 1 | 0 | 0 | 1 | 0 | 1111111111111110 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 0 | 0 | 1 | 0 | 1111111111111111 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 0 | 1 | 0 | 0 | 1 | 1 | 0000000000000001 | 0 | 0 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 0 | 1 | 1 | 1 | 1111111111111111 | 0 | 1 |
# | 0000000000000000 | 1111111111111111 | 0 | 0 | 0 | 0 | 0 | 0 | 0000000000000000 | 1 | 0 |
# | 0000000000000000 | 1111111111111111 | 0 | 1 | 0 | 1 | 0 | 1 | 1111111111111111 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 1 | 0 | 1 | 0 | 1 | 0 | 0000000000000000 | 1 | 0 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 1 | 1 | 1 | 1 | 0000000000000001 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 1 | 0 | 1 | 0 | 1111111111111111 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 1 | 1 | 0 | 0 | 0000000000010001 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 0 | 0 | 0 | 0 | 0000000000000011 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 1 | 1 | 0 | 1 | 1111111111101110 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 0 | 0 | 0 | 1 | 1111111111111100 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 1 | 1 | 1 | 1 | 1111111111101111 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 0 | 0 | 1 | 1 | 1111111111111101 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 0 | 1 | 1 | 1 | 1 | 1 | 0000000000010010 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 0 | 1 | 1 | 1 | 0000000000000100 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 1 | 1 | 1 | 0 | 0000000000010000 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 1 | 1 | 0 | 0 | 1 | 0 | 0000000000000010 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 0 | 0 | 1 | 0 | 0000000000010100 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 0 | 1 | 0 | 0 | 1 | 1 | 0000000000001110 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 0 | 1 | 1 | 1 | 1111111111110010 | 0 | 1 |
# | 0000000000010001 | 0000000000000011 | 0 | 0 | 0 | 0 | 0 | 0 | 0000000000000001 | 0 | 0 |
# | 0000000000010001 | 0000000000000011 | 0 | 1 | 0 | 1 | 0 | 1 | 0000000000010011 | 0 | 0 |
    
    
    pass
