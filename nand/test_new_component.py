from nand.peripheral import *


def test_nand():
    nand = Nand()

    assert nand.inputs() == {"a": 1, "b": 1}
    assert nand.outputs() == {"out": 1}

    # assert nand.wire({a: 0b001, b: 0b010}) == {}

    traces = {"a": [0b001], "b": [0b010], "out": [0b100]}

    op, = nand.combine(**traces)
    assert op(0b000) == 0b100
    assert op(0b001) == 0b101
    assert op(0b010) == 0b110
    assert op(0b011) == 0b011
    assert op(0b100) == 0b100
    assert op(0b101) == 0b101
    assert op(0b110) == 0b110
    assert op(0b111) == 0b011

    assert nand.sequence(**traces) == []


def test_dff():
    dff = DFF()

    assert dff.inputs() == {"in_": 1}
    assert dff.outputs() == {"out": 1}

    traces = {"in_": [0b01], "out": [0b10]}

    assert dff.combine(**traces) == []

    op, = dff.sequence(**traces)
    assert op(0b00) == 0b00
    assert op(0b01) == 0b11
    assert op(0b10) == 0b00
    assert op(0b11) == 0b11


def test_rom():
    rom = ROM(4)

    assert rom.inputs() == {"address": 4}
    assert rom.outputs() == {"out": 16}
    
    traces = { 
        "address": [0b0001 << i for i in range(4)],
        "out": [0b10000 << i for i in range(16)]
    }
    
    op, = rom.combine(**traces)
    for i in range(16):
        # every location is 0
        assert op(i) == 0x00 | i
    
    rom.program([1, 2, 3, 4, 5])
    for i in range(16):
        if i < 5:
            assert op(i) == ((i+1) << 4) | i
        else:
            assert op(i) == 0x00 | i
    
    
    assert rom.sequence(**traces) == []