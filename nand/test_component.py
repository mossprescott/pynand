from nand.component import *
from nand.evaluator import run_op


def test_nand():
    nand = Nand()

    assert nand.inputs() == {"a": 1, "b": 1}
    assert nand.outputs() == {"out": 1}

    # assert nand.wire({a: 0b001, b: 0b010}) == {}

    traces = {"a": [0b001], "b": [0b010], "out": [0b100]}

    op, = nand.combine(**traces)
    assert run_op(op, 0b000) == 0b100
    assert run_op(op, 0b001) == 0b101
    assert run_op(op, 0b010) == 0b110
    assert run_op(op, 0b011) == 0b011
    assert run_op(op, 0b100) == 0b100
    assert run_op(op, 0b101) == 0b101
    assert run_op(op, 0b110) == 0b110
    assert run_op(op, 0b111) == 0b011

    assert nand.sequence(**traces) == []


def test_dff():
    dff = DFF()

    assert dff.inputs() == {"in_": 1}
    assert dff.outputs() == {"out": 1}

    traces = {"in_": [0b01], "out": [0b10]}

    assert dff.combine(**traces) == []

    op, = dff.sequence(**traces)
    assert run_op(op, 0b00) == 0b00
    assert run_op(op, 0b01) == 0b11
    assert run_op(op, 0b10) == 0b00
    assert run_op(op, 0b11) == 0b11


def test_rom():
    rom = ROM(4)

    assert rom.inputs() == {"address": 4}
    assert rom.outputs() == {"out": 16}

    traces = {
        "address": [0b0001 << i for i in range(4)],
        "out": [0b10000 << i for i in range(16)]
    }

    op, = rom.combine(**traces)

    rom.program([1, 2, 3, 4, 5])
    for i in range(16):
        if i < 5:
            assert run_op(op, i) == ((i+1) << 4) | i
        else:
            assert run_op(op, i) == 0x00 | i

    assert rom.sequence(**traces) == []


def test_ram():
    ram = RAM(4)

    assert ram.inputs() == {"in_": 16, "load": 1, "address": 4}
    assert ram.outputs() == {"out": 16}

    traces = {
        "in_": [0b1 << i for i in range(16)],
        "load": [0b1 << 16],
        "address": [0b1 << (i+17) for i in range(4)],
        "out": [0b1 << (i+21) for i in range(16)]
    }

    op, = ram.combine(**traces)

    for i in range(16):
        ram.set(i, i)

    for i in range(16):
        addr = i << 17
        out = i << 21
        assert run_op(op, addr) == out | addr


    op, = ram.sequence(**traces)

    for i in range(16):
        in_ = 12345 + i
        load = 0b1 << 16
        addr = i << 17
        run_op(op, addr | load | in_)
        assert ram.get(i) == 12345 + i


def test_input():
    inpt = Input()

    assert inpt.inputs() == {}
    assert inpt.outputs() == {"out": 16}

    traces = { "out": [0b1 << i for i in range(16)]}

    op, = inpt.combine(**traces)

    assert run_op(op, 0) == 0

    inpt.set(12345)
    assert run_op(op, 0) == 12345

    assert inpt.sequence(**traces) == []


def test_has_combine_ops():
    assert Nand().has_combine_ops() == True
    assert DFF().has_combine_ops() == False
    assert ROM(1).has_combine_ops() == True
    assert RAM(1).has_combine_ops() == True
    assert Input().has_combine_ops() == True
