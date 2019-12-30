from nand.component import set_trace, tst_trace
from nand.evaluator import NandVector

def nand_op(a, b, out):
    def nand(traces):
        a_val = tst_trace(a, traces)
        b_val = tst_trace(b, traces)
        out_val = not (a_val and b_val)
        return set_trace(out, out_val, traces)
    return nand

def dff_op(in_, out):
    def dff(traces):
        in_val = tst_trace(in_, traces)
        return set_trace(out, in_val, traces)
    return dff
    
def test_xor():
    xor = NandVector(
        {'a': 1 << 0, 'b': 1 << 1},
        {'out': 1 << 5},
        {'na': 1 << 4, 'nb': 1 << 3},
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


def test_flop():
    ff = NandVector(
        {'in_': 0b01},
        {'out': 0b10},
        {},
        [],
        [dff_op(0b01, 0b10)])
    
    assert ff.get('out') == False
    
    ff.set('in_', True)
    assert ff.get('out') == False
    
    ff._flop()
    assert ff.get('out') == True
    