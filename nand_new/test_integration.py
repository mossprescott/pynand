import pytest

from nand_new.component import Nand
from nand_new.integration import IC, Connection, WiringError

def test_simple_wiring():
    ic = IC("?", {"in_": 1}, {"out": 1})

    nand = Nand()

    ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "a", 0))

    # print(f"{ic.components}")
    # assert 0

    # TODO: assert something


def test_wiring_errors():
    ic = IC("?", {"in_": 1}, {"out": 1})

    nand = Nand()

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "foo", 0))
    assert str(exc_info.value) == "Component Nand_0 has no input 'foo'"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "a", 1))
    assert str(exc_info.value) == "Tried to connect bit 1 of 1-bit input Nand_0.a"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "a", -1))
    assert str(exc_info.value) == "Tried to connect bit -1 of 1-bit input Nand_0.a"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "bar", 0), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Component Root has no output 'bar'"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 17), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Tried to connect bit 17 of 1-bit output Root.in_"


def test_simple_synthesis():
    ic = IC("JustNand", {"a": 1, "b": 1}, {"out": 1})
    nand = Nand()
    ic.wire(Connection(ic.root, "a", 0), Connection(nand, "a", 0))
    ic.wire(Connection(ic.root, "b", 0), Connection(nand, "b", 0))
    ic.wire(Connection(nand, "out", 0), Connection(ic.root, "out", 0))

    # print(ic)
    # print(ic.flatten())
    # assert False

    nv = ic.synthesize()

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
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "a", 0))
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "b", 0))
        ic.wire(Connection(nand, "out", 0), Connection(ic.root, "out", 0))
        return ic
    
    def Or():
        ic = IC("Or", {"a": 1, "b": 1}, {"out": 1})
        not_a = Not()
        not_b = Not()
        nand = Nand()
        ic.wire(Connection(ic.root, "a", 0), Connection(not_a, "in_", 0))
        ic.wire(Connection(ic.root, "b", 0), Connection(not_b, "in_", 0))
        ic.wire(Connection(not_a, "out", 0), Connection(nand, "a", 0))
        ic.wire(Connection(not_b, "out", 0), Connection(nand, "b", 0))
        ic.wire(Connection(nand, "out", 0), Connection(ic.root, "out", 0))
        return ic
    
    ic = Or()
    
    # print(ic)
    # print(ic.flatten())
    # assert False
    
    nv = ic.synthesize()
    
    assert nv.get(("out", 0)) == False

    nv.set(("a", 0), True)
    assert nv.get(("out", 0)) == True

    nv.set(("b", 0), True)
    assert nv.get(("out", 0)) == True

    nv.set(("a", 0), False)
    assert nv.get(("out", 0)) == True
