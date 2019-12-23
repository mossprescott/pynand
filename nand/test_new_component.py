from nand.peripheral import *

def test_nand():
    root = object()
    a = Ref(root, "a", 0)
    b = Ref(root, "b", 0)
    nand = Nand(a, b)
    
    out = Ref(nand, "out", 0)
    
    assert nand.outputs() == set([out])

    # assert nand.wire({a: 0b001, b: 0b010}) == {}
    
    op, = nand.combine({a: 0b001, b: 0b010, out: 0b100})    
    assert op(0b000) == 0b100
    assert op(0b001) == 0b101
    assert op(0b010) == 0b110
    assert op(0b011) == 0b011
    assert op(0b100) == 0b100
    assert op(0b101) == 0b101
    assert op(0b110) == 0b110
    assert op(0b111) == 0b011

    assert nand.sequence({a: 0b001, b: 0b010, out: 0b100}) == []


# def test_integrated():
#     root = object()
#     in_ = Ref(root, "in_", 0)
#
#     nand = Nand(in_, in_)
#
#     out, = nand.outputs()
#
#     andd = Integrated()

def test_dff():
    root = object()
    a = Ref(root, "a", 0)
    dff = DFF(a)
    
    out = Ref(dff, "out", 0)
    
    assert dff.outputs() == set([out])
    
    assert dff.combine({a: 0b01, out: 0b10}) == []

    op, = dff.sequence({a: 0b01, out: 0b10})
    assert op(0b00) == 0b00
    assert op(0b01) == 0b11
    assert op(0b10) == 0b00
    assert op(0b11) == 0b11
    