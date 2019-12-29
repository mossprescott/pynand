import pytest

from nand.component import Nand
from nand.integration import *

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
    assert str(exc_info.value) == "Component Nand has no input 'foo'"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "a", 1))
    assert str(exc_info.value) == "Tried to connect bit 1 of 1-bit input Nand.a"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 0), Connection(nand, "a", -1))
    assert str(exc_info.value) == "Tried to connect bit -1 of 1-bit input Nand.a"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "bar", 0), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Component Root has no output 'bar'"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic.root, "in_", 17), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Tried to connect bit 17 of 1-bit output Root.in_"


def test_components_simple():
    ic = IC("Whatevs", {"in_": 1}, {"out": 1})
    
    nand1 = Nand()
    nand2 = Nand()
    nand3 = Nand()
    
    ic.wire(Connection(ic.root, "in_", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(ic.root, "in_", 0), Connection(nand1, "b", 0))
    
    ic.wire(Connection(ic.root, "in_", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "b", 0))
    
    ic.wire(Connection(nand2, "out", 0), Connection(nand3, "a", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(nand3, "b", 0))
    
    ic.wire(Connection(nand3, "out", 0), Connection(ic.root, "out", 0))
    
    assert ic.sorted_components() == [nand1, nand2, nand3]
    
# TODO: more tests of ordering
# - ordered by input name?
# - in the presence of cycles?
# - accounting for combinational/sequential logic? That is, a DFF can precede the source of its 
#     value, since it never propagates a signal at combine() time. Too much of a special case?


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


def test_collapse_internal_none():
    graph = { 
        1: 2,
        3: 4,
        5: 6
    }
    assert collapse_internal(graph) == graph

def test_collapse_internal_simple():
    graph = { 
        1: 2,
        2: 3,
        4: 5,
    }
    collapsed = {
        1: 3,
        4: 5,
    }
    assert collapse_internal(graph) == collapsed

def test_collapse_internal_two_steps():
    graph = { 
        1: 2,
        2: 3,
        3: 4,
        5: 6,
    }
    collapsed = {
        1: 4,
        5: 6,
    }
    assert collapse_internal(graph) == collapsed

def test_collapse_internal_two_edges():
    graph = { 
        1: 3,
        2: 3,
        3: 4,
        5: 6,
    }
    collapsed = {
        1: 4,
        2: 4,
        5: 6,
    }
    assert collapse_internal(graph) == collapsed
