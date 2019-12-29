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
