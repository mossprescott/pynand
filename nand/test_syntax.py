import pytest

from nand.syntax import Nand, chip, run, lazy, clock

def test_trivial():
    @chip
    def Buffer(inputs, outputs):
        outputs.out = inputs.in_

    buffer = Buffer.constr()

    assert buffer.inputs() == {"in_": 1}
    assert buffer.outputs() == {"out": 1}

    assert len(buffer.wires) == 1  # TODO: how to assert on the structure?

    assert run(Buffer, in_=False).out == False
    assert run(Buffer, in_=True).out == True


def test_simple():
    @chip
    def Not(inputs, outputs):
        outputs.out = Nand(a=inputs.in_, b=inputs.in_).out

    not_ = Not.constr()

    assert not_.inputs() == {"in_": 1}
    assert not_.outputs() == {"out": 1}

    assert len(not_.wires) == 3  # TODO: how to assert on the structure?

    assert run(Not, in_=False).out == True
    assert run(Not, in_=True).out == False


def test_flat_multibit():
    """No nesting, multiple-bit input and output, both explicit."""

    @chip
    def Not2(inputs, outputs):
        outputs.out[0] = Nand(a=inputs.in_[0], b=inputs.in_[0]).out
        outputs.out[1] = Nand(a=inputs.in_[1], b=inputs.in_[1]).out

    not2 = Not2.constr()

    assert not2.inputs() == {"in_": 2}
    assert not2.outputs() == {"out": 2}

    assert len(not2.wires) == 6  # TODO: how to assert on the structure?

    assert run(Not2, in_=0b01).out == 0b10
    assert run(Not2, in_=0b10).out == 0b01


def test_implicit_multibit_out():
    """A nested chip with multiple-bit output and a bare reference to it."""

    @chip
    def Dup(inputs, outputs):
        outputs.out[0] = inputs.in_
        outputs.out[1] = inputs.in_

    @chip
    def Wrap(inputs, outputs):
        outputs.out = Dup(in_=inputs.in_).out

    wrap = Wrap.constr()

    assert wrap.inputs() == {"in_": 1}
    assert wrap.outputs() == {"out": 2}

    assert len(wrap.wires) == 3  # TODO: how to assert on the structure?

    assert run(Wrap, in_=0b0).out == 0b00
    assert run(Wrap, in_=0b1).out == 0b11


def test_implicit_multibit_in():
    """A nested chip with multiple-bit input and a bare reference to it."""

    @chip
    def LessThan3(inputs, outputs):
        outputs.out = Nand(a=inputs.in_[0], b=inputs.in_[1]).out

    @chip
    def Wrap(inputs, outputs):
        outputs.out = LessThan3(in_=inputs.in_).out

    wrap = Wrap.constr()
    assert wrap.inputs() == {"in_": 2}
    assert wrap.outputs() == {"out": 1}

    assert len(wrap.wires) == 3  # TODO: how to assert on the structure?

    assert run(Wrap, in_=0).out == True
    assert run(Wrap, in_=1).out == True
    assert run(Wrap, in_=2).out == True
    assert run(Wrap, in_=3).out == False


def test_simple_const_input():
    @chip
    def Bounce(inputs, outputs):
        outputs.out = inputs.in_

    @chip
    def ZeroOne(inputs, outputs):
        outputs.zero = Bounce(in_=0).out
        outputs.one = Bounce(in_=1).out

    assert run(ZeroOne).zero == False
    assert run(ZeroOne).one == True


def test_multibit_const_input():
    @chip
    def Bounce16(inputs, outputs):
        for i in range(16):
            outputs.out[i] = inputs.in_[i]

    @chip
    def Constants(inputs, outputs):
        outputs.zero = Bounce16(in_=0).out
        outputs.one = Bounce16(in_=1).out
        outputs.onetofive = Bounce16(in_=12345).out

    assert run(Constants).zero == 0
    assert run(Constants).one == 1
    assert run(Constants).onetofive == 12345

def test_simple_const_output():
    @chip
    def Zero(inputs, outputs):
        outputs.out = 0

    assert(run(Zero).out) == 0

def test_multibit_const_output():
    @chip
    def ShiftL16(inputs, outputs):
        outputs.out[0] = 0
        for i in range(15):
            outputs.out[i+1] = inputs.in_[i]

    assert(run(ShiftL16, in_=1).out) == 2

def test_lazy_simple():
    @chip
    def And(inputs, outputs):
        # Just declare them in the wrong order for no good reason:
        nand1 = lazy()
        nand2 = Nand(a=nand1.out, b=nand1.out)
        nand1.set(Nand(a=inputs.a, b=inputs.b))
        outputs.out = nand2.out

    and_ = And.constr()
    assert and_.inputs() == {"a": 1, "b": 1}
    assert and_.outputs() == {"out": 1}
    assert len(and_.wires) == 5  # TODO: how to assert on the structure?

    assert run(And, a=False, b=False).out == False
    assert run(And, a=False, b=True).out == False
    assert run(And, a=True, b=False).out == False
    assert run(And, a=True, b=True).out == True


def test_clocked_simple():
    @chip
    def ClockLow(inputs, outputs):
        outputs.out = Nand(a=clock, b=clock).out

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
#     @chip
#     def ClockHigh(inputs, outputs):
#         outputs.out = clock
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
    @chip
    def Err(inputs, outputs):
        Nand(a=0, b=0, c=0)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value) == "Unrecognized input: 'c'"


def test_error_missing_arg():
    @chip
    def And(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.b).out

    @chip
    def Wrap(inputs, outputs):
        outputs.out = And(a=inputs.in_).out  # Missing `b=` here

    with pytest.raises(SyntaxError) as exc_info:
        wrap = Wrap.constr()
    assert str(exc_info.value) == "Missing input(s): {'b'}"


def test_error_unknown_input():
    @chip
    def And(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.b).out

    @chip
    def Wrap(inputs, outputs):
        outputs.out = And(a=inputs.in_, b=inputs.in_, c=inputs.in_).out  # Extra input: `c`

    with pytest.raises(SyntaxError) as exc_info:
        wrap = Wrap.constr()
    assert str(exc_info.value) == "Unrecognized input: 'c'"


def test_error_unknown_output():
    @chip
    def And(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.b).out

    @chip
    def Wrap(inputs, outputs):
        outputs.out = And(a=inputs.in_, b=inputs.in_).result  # Wrong name

    with pytest.raises(SyntaxError) as exc_info:
        wrap = Wrap.constr()
    assert str(exc_info.value) == "Unrecognized output: 'result'"


def test_error_ref_expected_for_input():
    @chip
    def Err(inputs, outputs):
        Nand(a=Nand(a=0, b=1),  # missing ".out"
             b=0)

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value).startswith("Expected a reference for input 'a', got ")


def test_error_ref_expected_for_output():
    @chip
    def Err(inputs, outputs):
        outputs.out = Nand(a=0, b=1)  # missing ".out"

    with pytest.raises(SyntaxError) as exc_info:
        Err.constr()
    assert str(exc_info.value).startswith("Expected a reference or single-bit constant for output 'out', got ")
