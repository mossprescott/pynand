import pytest

from nand_new.syntax import Nand, build, run

def test_trivial():
    def mkBuffer(inputs, outputs):
        outputs.out = inputs.in_
    Buffer = build(mkBuffer)

    chip = Buffer.constr()

    assert chip.inputs() == {"in_": 1}
    assert chip.outputs() == {"out": 1}

    assert len(chip.wires) == 1  # TODO: how to assert on the structure?

    assert run(Buffer, in_=False).out == False
    assert run(Buffer, in_=True).out == True


def test_simple():
    def mkNot(inputs, outputs):
        outputs.out = Nand(a=inputs.in_, b=inputs.in_).out
    Not = build(mkNot)

    chip = Not.constr()

    assert chip.inputs() == {"in_": 1}
    assert chip.outputs() == {"out": 1}

    assert len(chip.wires) == 3  # TODO: how to assert on the structure?

    assert run(Not, in_=False).out == True
    assert run(Not, in_=True).out == False


def test_flat_multibit():
    """No nesting, multiple-bit input and output, both explicit."""

    def mkNot2(inputs, outputs):
        outputs.out[0] = Nand(a=inputs.in_[0], b=inputs.in_[0]).out
        outputs.out[1] = Nand(a=inputs.in_[1], b=inputs.in_[1]).out
    Not2 = build(mkNot2)

    chip = Not2.constr()

    assert chip.inputs() == {"in_": 2}
    assert chip.outputs() == {"out": 2}

    assert len(chip.wires) == 6  # TODO: how to assert on the structure?

    assert run(Not2, in_=0b01).out == 0b10
    assert run(Not2, in_=0b10).out == 0b01


def test_implicit_multibit_out():
    """A nested chip with multiple-bit output and a bare reference to it."""

    def mkDup(inputs, outputs):
        outputs.out[0] = inputs.in_
        outputs.out[1] = inputs.in_
    Dup = build(mkDup)

    def mkWrap(inputs, outputs):
        outputs.out = Dup(in_=inputs.in_).out
    Wrap = build(mkWrap)

    chip = Wrap.constr()

    assert chip.inputs() == {"in_": 1}
    assert chip.outputs() == {"out": 2}

    assert len(chip.wires) == 3  # TODO: how to assert on the structure?

    assert run(Wrap, in_=0b0).out == 0b00
    assert run(Wrap, in_=0b1).out == 0b11


def test_implicit_multibit_in():
    """A nested chip with multiple-bit input and a bare reference to it."""

    def mkLessThan3(inputs, outputs):
        outputs.out = Nand(a=inputs.in_[0], b=inputs.in_[1]).out
    LessThan3 = build(mkLessThan3)

    def mkWrap(inputs, outputs):
        outputs.out = LessThan3(in_=inputs.in_).out
    Wrap = build(mkWrap)

    chip = Wrap.constr()
    
    assert chip.inputs() == {"in_": 2}
    assert chip.outputs() == {"out": 1}

    assert len(chip.wires) == 3  # TODO: how to assert on the structure?

    assert run(Wrap, in_=0).out == True
    assert run(Wrap, in_=1).out == True
    assert run(Wrap, in_=2).out == True
    assert run(Wrap, in_=3).out == False


def test_simple_const_input():
    def mkBounce(inputs, outputs):
        outputs.out = inputs.in_
    Bounce = build(mkBounce)

    def mkZeroOne(inputs, outputs):
        outputs.zero = Bounce(in_=0).out
        outputs.one = Bounce(in_=1).out
    ZeroOne = build(mkZeroOne)

    chip = ZeroOne.constr()

    assert run(ZeroOne).zero == False
    assert run(ZeroOne).one == True


def test_multibit_const_input():
    def mkBounce16(inputs, outputs):
        for i in range(16):
            outputs.out[i] = inputs.in_[i]
    Bounce16 = build(mkBounce16)

    def mkConstants(inputs, outputs):
        outputs.zero = Bounce16(in_=0).out
        outputs.one = Bounce16(in_=1).out
        outputs.onetofive = Bounce16(in_=12345).out
    Constants = build(mkConstants)

    chip = Constants.constr()

    assert run(Constants).zero == 0
    assert run(Constants).one == 1
    assert run(Constants).onetofive == 12345


# TODO: const output? For consistency only; probably not sensible.


def test_error_unexpected_arg():
    def mkErr(inputs, outputs):
        Nand(a=0, b=0, c=0)    
    Err = build(mkErr)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value) == "Unexpected argument: c"


def test_error_ref_expected_for_input():
    def mkErr(inputs, outputs):
        Nand(a=Nand(a=0, b=1),  # missing ".out"
             b=0)
    Err = build(mkErr)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value) == "Expected a reference for input 'a', got Nand(...)"


def test_error_ref_expected_for_output():
    def mkErr(inputs, outputs):
        outputs.out = Nand(a=0, b=1)  # missing ".out"
    Err = build(mkErr)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value) == "Expected a reference for output 'out', got Nand(...)"
