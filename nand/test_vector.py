from nand.component import Nand, DFF
from nand.vector import NandVector, nand_op, custom_op, synthesize, set_trace, tst_trace
from nand.integration import IC, Connection, root

def dff_op(in_, out):
    def dff(traces):
        in_val = tst_trace(in_, traces)
        return set_trace(out, in_val, traces)
    return custom_op(dff)
    
def test_vector_xor():
    xor = NandVector(
        {'a': 1 << 0, 'b': 1 << 1},
        {'out': 1 << 5},
        {'na': 1 << 4, 'nb': 1 << 3},
        [],
        [ nand_op(1 << 0, 1 << 1, 1 << 2),  # Nand(a, b) -> nand
          nand_op(1 << 0, 1 << 2, 1 << 3),  # Nand(a, nand) -> na
          nand_op(1 << 1, 1 << 2, 1 << 4),  # Nand(b, nand) -> nb
          nand_op(1 << 3, 1 << 4, 1 << 5),  # Nand(na, na) -> out
        ],
        [])

    assert xor.get('out') == False

    xor.set('a', True)
    assert xor.get('out') == True

    xor.set('b', True)
    assert xor.get('out') == False

    xor.set('a', False)
    assert xor.get('out') == True

    xor.set('b', False)
    assert xor.get('out') == False
    assert xor.get_internal('na') and xor.get_internal('nb')


def test_vector_flop():
    ff = NandVector(
        {'in_': 0b01},
        {'out': 0b10},
        {},
        [],
        [],
        [dff_op(0b01, 0b10)])
    
    assert ff.get('out') == False
    
    ff.set('in_', True)
    assert ff.get('out') == False
    
    ff._flop()
    assert ff.get('out') == True
    

def test_simple_synthesis():
    ic = IC("JustNand", {"a": 1, "b": 1}, {"out": 1})
    nand = Nand()
    ic.wire(Connection(root, "a", 0), Connection(nand, "a", 0))
    ic.wire(Connection(root, "b", 0), Connection(nand, "b", 0))
    ic.wire(Connection(nand, "out", 0), Connection(root, "out", 0))

    nv, _ = synthesize(ic)

    assert nv.get(("out", 0)) == True

    nv.set(("a", 0), True)
    assert nv.get(("out", 0)) == True

    nv.set(("b", 0), True)
    assert nv.get(("out", 0)) == False

    nv.set(("a", 0), False)
    assert nv.get(("out", 0)) == True


def test_nested_synthesis():
    def Not():
        ic = IC("Not", {"in_": 1}, {"out": 1})
        nand = Nand()
        ic.wire(Connection(root, "in_", 0), Connection(nand, "a", 0))
        ic.wire(Connection(root, "in_", 0), Connection(nand, "b", 0))
        ic.wire(Connection(nand, "out", 0), Connection(root, "out", 0))
        return ic
    
    def Or():
        ic = IC("Or", {"a": 1, "b": 1}, {"out": 1})
        not_a = Not()
        not_b = Not()
        nand = Nand()
        ic.wire(Connection(root, "a", 0), Connection(not_a, "in_", 0))
        ic.wire(Connection(root, "b", 0), Connection(not_b, "in_", 0))
        ic.wire(Connection(not_a, "out", 0), Connection(nand, "a", 0))
        ic.wire(Connection(not_b, "out", 0), Connection(nand, "b", 0))
        ic.wire(Connection(nand, "out", 0), Connection(root, "out", 0))
        return ic
    
    ic = Or()
    
    nv, _ = synthesize(ic)
    
    assert nv.get(("out", 0)) == False

    nv.set(("a", 0), True)
    assert nv.get(("out", 0)) == True

    nv.set(("b", 0), True)
    assert nv.get(("out", 0)) == True

    nv.set(("a", 0), False)
    assert nv.get(("out", 0)) == True


def test_back_edges_none():
    ic = IC("Nonsense", {"reset": 1}, {"out": 1})
    nand1 = Nand()
    dff = DFF()
    ic.wire(Connection(root, "reset", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(dff, "out", 0), Connection(nand1, "b", 0))  # not a back-edge, because it's a latched output
    ic.wire(Connection(nand1, "out", 0), Connection(dff, "in_", 0))
    ic.wire(Connection(dff, "out", 0), Connection(root, "out", 0))
    
    nv, _ = synthesize(ic)
    assert nv.non_back_edge_mask == 0b111  # i.e. every bit, which is one Nand, one DFF, and reset

def test_back_edges_goofy():
    ic = IC("Nonsense", {"reset": 1}, {"out": 1})
    nand1 = Nand()
    nand2 = Nand()
    ic.wire(Connection(root, "reset", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(nand1, "b", 0))  # back-edge here
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "b", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(root, "out", 0))
    
    nv, _ = synthesize(ic)
    assert nv.non_back_edge_mask == 0b011  # i.e. not nand2, yes nand1 and reset

    