import pytest

from nand.syntax import Nand, build, run, lazy, clock

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

    assert run(Constants).zero == 0
    assert run(Constants).one == 1
    assert run(Constants).onetofive == 12345

# TODO: const output? For consistency only; probably not sensible.


def test_lazy_simple():
    def mkAnd(inputs, outputs):
        # Just declare them in the wrong order for no good reason:
        nand1 = lazy()
        nand2 = Nand(a=nand1.out, b=nand1.out)
        nand1.set(Nand(a=inputs.a, b=inputs.b))
        outputs.out = nand2.out
    And = build(mkAnd)
    
    chip = And.constr()
    assert chip.inputs() == {"a": 1, "b": 1}
    assert chip.outputs() == {"out": 1}
    assert len(chip.wires) == 5  # TODO: how to assert on the structure?
    
    assert run(And, a=False, b=False).out == False
    assert run(And, a=False, b=True).out == False
    assert run(And, a=True, b=False).out == False
    assert run(And, a=True, b=True).out == True


def test_clocked_simple():
    def mkClockLow(inputs, outputs):
        outputs.out = Nand(a=clock, b=clock).out
    ClockLow = build(mkClockLow)

    ch = run(ClockLow)
    
    assert ch.out == True

    ch.tick()
    assert ch.out == False

    ch.tock()
    assert ch.out == True


# skip for now:
# def test_clocked_to_output():
#     """An edge case: clock copied directly to an output.
#     """
#
#     def mkClockHigh(inputs, outputs):
#         outputs.out = clock
#     ClockHigh = build(mkClockHigh)
#
#     print(ClockHigh.constr())
#
#     ch = run(ClockHigh)
#     print(ch._vector.combine_ops)
#     print(ch._vector.sequence_ops)
#
#     assert ch.out == False
#
#     ch.tick()
#     assert ch.out == True
#
#     ch.tock()
#     assert ch.out == False


def test_error_unexpected_arg():
    def mkErr(inputs, outputs):
        Nand(a=0, b=0, c=0)    
    Err = build(mkErr)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value) == "Unrecognized input: 'c'"


def test_error_missing_arg():
    def mkAnd(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.b).out
    And = build(mkAnd)

    def mkWrap(inputs, outputs):
        outputs.out = And(a=inputs.in_).out  # Missing `b=` here
    Wrap = build(mkWrap)

    with pytest.raises(SyntaxError) as exc_info:
        chip = Wrap.constr()
    assert str(exc_info.value) == "Missing input(s): {'b'}"


def test_error_unknown_input():
    def mkAnd(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.b).out
    And = build(mkAnd)

    def mkWrap(inputs, outputs):
        outputs.out = And(a=inputs.in_, b=inputs.in_, c=inputs.in_).out  # Extra input: `c`
    Wrap = build(mkWrap)

    with pytest.raises(SyntaxError) as exc_info:
        chip = Wrap.constr()
    assert str(exc_info.value) == "Unrecognized input: 'c'"


def test_error_unknown_output():
    def mkAnd(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.b).out
    And = build(mkAnd)

    def mkWrap(inputs, outputs):
        outputs.out = And(a=inputs.in_, b=inputs.in_).result  # Wrong name
    Wrap = build(mkWrap)

    with pytest.raises(SyntaxError) as exc_info:
        chip = Wrap.constr()
    assert str(exc_info.value) == "Unrecognized output: 'result'"


def test_error_ref_expected_for_input():
    def mkErr(inputs, outputs):
        Nand(a=Nand(a=0, b=1),  # missing ".out"
             b=0)
    Err = build(mkErr)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value).startswith("Expected a reference for input 'a', got ")


def test_error_ref_expected_for_output():
    def mkErr(inputs, outputs):
        outputs.out = Nand(a=0, b=1)  # missing ".out"
    Err = build(mkErr)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value).startswith("Expected a reference for output 'out', got ")
