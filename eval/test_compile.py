from eval.Nand import Component, Nand
from eval.NandVector import NandVector
from eval.Compiler import *

def test_wrapper_nand():
    """Test the wrapper that provides a nice syntax around a NandVector."""
    
    nand_vec = NandVector(
        {('a', None): 0b001, ('b', None): 0b010},
        {('out', None): 0b100},
        [(0b011, 0b100)])
    nand = NandVectorWrapper(nand_vec)
    
    nand.a = nand.b = 0
    assert nand.out == 1
    
    nand.a = 1
    assert nand.out == 1
    
    nand.b = 1
    assert nand.out == 0
    
    nand.a = 0
    assert nand.out == 1


def test_wrapper_swap():
    """Test the wrapper that provides a nice syntax around a NandVector."""
    
    swap_vec = NandVector(
        {('in_', 0): 0b01, ('in_', 1): 0b10},
        {('out', 0): 0b10, ('out', 1): 0b01},
        [])
    swap = NandVectorWrapper(swap_vec)
    
    swap.in_ = 0b00
    assert swap.out == 0b00
    
    swap.in_ = 0b01
    assert swap.out == 0b10

    swap.in_ = 0b10
    assert swap.out == 0b01

    swap.in_ = 0b11
    assert swap.out == 0b11


def test_compile_nand():
    """Inspect the NandVector that a trivial component compiles to."""

    nand_vec = component_to_vector(Nand)  # TODO

    # Note: either input can be assigned to either of the low two bits.
    assert set(nand_vec.inputs.keys()) == set(['a', 'b'])
    assert set(nand_vec.inputs.values()) == set([0b001, 0b010])

    assert nand_vec.outputs == {'out': 0b100}

    assert nand_vec.ops == [(0b011, 0b100)]


def test_compile_not():
    """Inspect the NandVector that a trivial component compiles to."""

    def mkNott(inputs, outputs):
        outputs.out = Nand(a=inputs.a, b=inputs.a).out

    nand_vec = component_to_vector(Component(mkNott))

    assert nand_vec.inputs == {('a', None): 0b01}
    assert nand_vec.outputs == {('out', None): 0b10}
    assert nand_vec.ops == [(0b01, 0b10)]


def test_compile_multibit_nand():
    """Inspect the NandVector that a trivial component compiles to."""

    def mkNand2(inputs, outputs):
        outputs.out[2] = Nand(a=inputs.in_[0], b=inputs.in_[1]).out

    nand_vec = component_to_vector(Component(mkNand2))

    # Note: either input can be assigned to either of the low two bits.
    assert set(nand_vec.inputs.keys()) == set([('in_', 0), ('in_', 1)])
    assert set(nand_vec.inputs.values()) == set([0b001, 0b010])

    assert nand_vec.outputs == {('out', 2): 0b100}

    assert nand_vec.ops == [(0b011, 0b100)]

