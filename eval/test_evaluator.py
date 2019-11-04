from eval.evaluator import NandVector

def test_xor():
    xor = NandVector(
        {'a': 0b000001, 'b': 0b000010},
        {'out': 0b100000},
        [ (0b000011, 0b000100),  # Nand(a, b) -> nand
          (0b000101, 0b001000),  # Nand(a, nand) -> na
          (0b000110, 0b010000),  # Nand(b, nand) -> nb
          (0b011000, 0b100000)   # Nand(na, na) -> out
        ]
    )

    assert xor.get_output('out') == False

    xor.set_input('a', True)
    assert xor.get_output('out') == True

    xor.set_input('b', True)
    assert xor.get_output('out') == False

    xor.set_input('a', False)
    assert xor.get_output('out') == True

    xor.set_input('b', False)
    assert xor.get_output('out') == False
