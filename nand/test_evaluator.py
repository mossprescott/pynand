from nand.evaluator import NandVector

def test_xor():
    xor = NandVector(
        {'a': 0b000001, 'b': 0b000010},
        {'out': 0b100000},
        {'na': 0b00100, 'nb': 0b01000},
        [ (0b000011, 0b000100),  # Nand(a, b) -> nand
          (0b000101, 0b001000),  # Nand(a, nand) -> na
          (0b000110, 0b010000),  # Nand(b, nand) -> nb
          (0b011000, 0b100000)   # Nand(na, na) -> out
        ],
        []
    )

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
        [(0b01, 0b10)])
    
    assert ff.get('out') == 0
    
    ff.set('in_', 1)
    assert ff.get('out') == 0
    
    ff._flop()
    assert ff.get('out') == 1
    