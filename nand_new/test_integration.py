import pytest

from nand_new.component import Nand
from nand_new.integration import IC, Connection, WiringError

def test_simple_wiring():
    nott = IC({"in_": 1}, {"out": 1})
    
    nand = Nand()
    
    nott.wire(Connection(nott.root, "in_", 0), Connection(nand, "a", 0))
    
    # print(f"{nott.components}")
    # assert 0

    # TODO: assert something
        
    
def test_wiring_errors():
    nott = IC({"in_": 1}, {"out": 1})
    
    nand = Nand()
    
    with pytest.raises(WiringError) as exc_info:
        nott.wire(Connection(nott.root, "in_", 0), Connection(nand, "foo", 0))
    assert str(exc_info.value) == "Component Nand_0 has no input 'foo'"
    
    with pytest.raises(WiringError) as exc_info:
        nott.wire(Connection(nott.root, "in_", 0), Connection(nand, "a", 1))
    assert str(exc_info.value) == "Tried to connect bit 1 of 1-bit input Nand_0.a"
    
    with pytest.raises(WiringError) as exc_info:
        nott.wire(Connection(nott.root, "in_", 0), Connection(nand, "a", -1))
    assert str(exc_info.value) == "Tried to connect bit -1 of 1-bit input Nand_0.a"
    
    with pytest.raises(WiringError) as exc_info:
        nott.wire(Connection(nott.root, "bar", 0), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Component Root has no output 'bar'"
    
    with pytest.raises(WiringError) as exc_info:
        nott.wire(Connection(nott.root, "in_", 17), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Tried to connect bit 17 of 1-bit output Root.in_"
