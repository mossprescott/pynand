import pytest

from nand.component import Nand, DFF
from nand.integration import *

def test_simple_wiring():
    ic = IC("JustNand", {"in_": 1}, {"out": 1})

    nand = Nand()

    ic.wire(Connection(root, "in_", 0), Connection(nand, "a", 0))
    ic.wire(Connection(root, "in_", 0), Connection(nand, "b", 0))
    ic.wire(Connection(nand, "out", 0), Connection(root, "out", 0))

    assert str(ic).split(sep='\n') ==[
        "JustNand(in_[1]; out[1]):",
        "  in_                   -> Nand_0.a             ",
        "  in_                   -> Nand_0.b             ",
        "  Nand_0.out            -> out                  ",
    ]


def test_multibit_wiring():
    nand16 = IC("Nand16", {"a": 16, "b": 16}, {"out": 16})
    for i in range(16):
        nand = Nand()
        nand16.wire(Connection(root, "a", i), Connection(nand, "a", 0))
        nand16.wire(Connection(root, "b", i), Connection(nand, "b", 0))
        nand16.wire(Connection(nand, "out", 0), Connection(root, "out", i))
    
    ic = IC("JustNand16", {"in_": 16}, {"out": 16})
    for i in range(16):
        ic.wire(Connection(root, "in_", i), Connection(nand16, "a", i))
        ic.wire(Connection(root, "in_", i), Connection(nand16, "b", i))
        ic.wire(Connection(nand16, "out", i), Connection(root, "out", i))
    
    assert str(ic).split(sep='\n') ==[
        "JustNand16(in_[16]; out[16]):",
        "  in_[0..15]            -> Nand16_0.a[0..15]    ",
        "  in_[0..15]            -> Nand16_0.b[0..15]    ",
        "  Nand16_0.out[0..15]   -> out[0..15]           ",
    ]


def test_wiring_errors():
    ic = IC("?", {"in_": 1}, {"out": 1})

    nand = Nand()

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(root, "in_", 0), Connection(nand, "foo", 0))
    assert str(exc_info.value) == "Component Nand has no input 'foo'"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(root, "in_", 0), Connection(nand, "a", 1))
    assert str(exc_info.value) == "Tried to connect bit 1 of 1-bit input Nand.a"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(root, "in_", 0), Connection(nand, "a", -1))
    assert str(exc_info.value) == "Tried to connect bit -1 of 1-bit input Nand.a"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(root, "bar", 0), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Component Root has no output 'bar'"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(root, "in_", 17), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Tried to connect bit 17 of 1-bit output Root.in_"  # TODO: msg could be better

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(ic, "in_", 0), Connection(nand, "a", 0))
    assert str(exc_info.value) == "Tried to connect input to self; use `root` instead"

    with pytest.raises(WiringError) as exc_info:
        ic.wire(Connection(nand, "out", 0), Connection(ic, "out", 0))
    assert str(exc_info.value) == "Tried to connect output to self; use `root` instead"


def test_components_simple():
    ic = IC("Whatevs", {"in_": 1}, {"out": 1})
    
    nand1 = Nand()
    nand2 = Nand()
    nand3 = Nand()
    
    ic.wire(Connection(root, "in_", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(root, "in_", 0), Connection(nand1, "b", 0))
    
    ic.wire(Connection(root, "in_", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "b", 0))
    
    ic.wire(Connection(nand2, "out", 0), Connection(nand3, "a", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(nand3, "b", 0))
    
    ic.wire(Connection(nand3, "out", 0), Connection(root, "out", 0))
    
    assert ic.sorted_components() == [nand1, nand2, nand3]
    
# TODO: more tests of ordering
# - ordered by input name?
# - in the presence of cycles?
# - accounting for combinational/sequential logic? That is, a DFF can precede the source of its 
#     value, since it never propagates a signal at combine() time. Too much of a special case?


def test_components_dff_sorting():
    """DFFs can be evaluated last because their outputs won't update until the next clock cycle,
    and therefore aren't needed for 'downstream' evaluation.
    """
    
    ic = IC("Mixed", {"in": 1}, {"out": 1})
    nand1 = Nand()
    dff1 = DFF()
    nand2 = Nand()
    ic.wire(Connection(root, "in", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(root, "in", 0), Connection(nand1, "b", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(dff1, "in_", 0))
    ic.wire(Connection(dff1, "out", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(dff1, "out", 0), Connection(nand2, "b", 0))
    ic.wire(Connection(nand2, "out", 0), Connection(root, "out", 0))

    # Note: relative order of the Nands doesn't really matter here
    assert ic.flatten().sorted_components() == [nand2, nand1, dff1]


def test_flatten_prune():
    yn = IC("YesAndNo", {"in": 1}, {"out": 1, "not_out": 1})
    nand1 = Nand()
    yn.wire(Connection(root, "in", 0), Connection(root, "out", 0))
    yn.wire(Connection(root, "in", 0), Connection(nand1, "a", 0))
    yn.wire(Connection(root, "in", 0), Connection(nand1, "b", 0))
    yn.wire(Connection(nand1, "out", 0), Connection(root, "not_out", 0))
    
    yes = IC("Yes", {"in": 1}, {"out": 1})
    yes.wire(Connection(root, "in", 0), Connection(yn, "in", 0))
    yes.wire(Connection(yn, "out", 0), Connection(root, "out", 0))
    
    no = IC("No", {"in": 1}, {"out": 1})
    no.wire(Connection(root, "in", 0), Connection(yn, "in", 0))
    no.wire(Connection(yn, "not_out", 0), Connection(root, "out", 0))
    
    assert len(yes.flatten().wires) == 1
    assert len(no.flatten().wires) == 3
    assert yes.flatten().sorted_components() == []
    assert no.flatten().sorted_components() == [nand1]


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
