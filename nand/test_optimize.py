from nand.component import Nand, Const
from nand.integration import IC, Connection
from nand.optimize import simplify

def test_simplify_constant_one():
    """Nand(1, x) == Nand(x, 1) => Nand(x, x).
    """
    
    ic = IC("WeirdNot", {"in": 1}, {"out": 1})
    nand1 = Nand()
    ic.wire(Connection(ic.root, "in", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(Const(1, 1), "out", 0), Connection(nand1, "b", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(ic.root, "out", 0))
    
    simple = simplify(ic)
    
    simple_nand = simple.sorted_components()[0]
    assert simple.wires == {
        Connection(simple_nand, "a", 0): Connection(simple.root, "in", 0),
        Connection(simple_nand, "b", 0): Connection(simple.root, "in", 0),
        Connection(simple.root, "out", 0): Connection(simple_nand, "out", 0),
    }


def test_simplify_constant_zero():
    ic = IC("Perverse1", {"in": 1}, {"out": 1})
    nand1 = Nand()
    ic.wire(Connection(ic.root, "in", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(Const(1, 0), "out", 0), Connection(nand1, "b", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(ic.root, "out", 0))
    
    simple = simplify(ic)
    
    assert simple.wires == {Connection(simple.root, "out", 0): Connection(Const(1, 1), "out", 0)}


def test_simplify_double_negative():
    ic = IC("PerverseBuffer", {"in": 1}, {"out": 1})
    nand1 = Nand()
    nand2 = Nand()
    ic.wire(Connection(ic.root, "in", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(ic.root, "in", 0), Connection(nand1, "b", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "b", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(ic.root, "out", 0))
    
    simple = simplify(ic)
    
    assert simple.wires == {Connection(simple.root, "out", 0): Connection(simple.root, "in", 0)}


def test_simplify_duplicate():
    ic = IC("2Nands", {"in1": 1, "in2": 1}, {"out1": 1, "out2": 1})
    nand1 = Nand()
    nand2 = Nand()
    ic.wire(Connection(ic.root, "in1", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(ic.root, "in2", 0), Connection(nand1, "b", 0))
    ic.wire(Connection(ic.root, "in2", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(ic.root, "in1", 0), Connection(nand2, "b", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(ic.root, "out1", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(ic.root, "out2", 0))
    
    simple = simplify(ic)
    
    simple_nand = simple.sorted_components()[0]
    # Note: in1 and in2 connected to a and b randomly
    assert simple.wires.keys() == set([
        Connection(simple_nand, "a", 0),
        Connection(simple_nand, "b", 0),
        Connection(simple.root, "out1", 0),
        Connection(simple.root, "out2", 0),
    ])
    assert simple.wires[Connection(simple.root, "out1", 0)] == Connection(simple_nand, "out", 0)
    assert simple.wires[Connection(simple.root, "out2", 0)] == Connection(simple_nand, "out", 0)
