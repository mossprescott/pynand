from NandVector import NandVector
from Compiler import *

def test_wrapper():
    nand_vec = NandVector(
        {'a': 0b001, 'b': 0b010},
        {'out': 0b100},
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