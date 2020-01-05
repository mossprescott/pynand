from nand.codegen import translate
from nand.component import Nand
from nand.integration import IC, Connection, root
import nand.syntax


def test_nand():
    ic = nand.syntax._constr(nand.syntax.Nand)

    nnd = translate(ic)()

    assert nnd.out == True

    nnd.a = True
    assert nnd.out == True

    nnd.b = True
    assert nnd.out == False

    nnd.a = False
    assert nnd.out == True


def test_and3():
    """A simple component that's definitely not handled as a primitive."""

    ic = IC("And3", {"a": 1, "b": 1, "c": 1}, {"out": 1})
    nand1 = Nand()
    ic.wire(Connection(root, "a", 0), Connection(nand1, "a", 0))
    ic.wire(Connection(root, "b", 0), Connection(nand1, "b", 0))
    nand2 = Nand()
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "a", 0))
    ic.wire(Connection(nand1, "out", 0), Connection(nand2, "b", 0))
    nand3 = Nand()
    ic.wire(Connection(nand2, "out", 0), Connection(nand3, "a", 0))
    ic.wire(Connection(root, "c", 0), Connection(nand3, "b", 0))
    nand4 = Nand()
    ic.wire(Connection(nand3, "out", 0), Connection(nand4, "a", 0))
    ic.wire(Connection(nand3, "out", 0), Connection(nand4, "b", 0))
    ic.wire(Connection(nand4, "out", 0), Connection(root, "out", 0))

    and3 = translate(ic)()

    assert and3.out == False

    for i in range(8):
        a, b, c = [bool(i & (1 << j)) for j in range(3)]
        and3.a = a
        and3.b = b
        and3.c = c
        assert and3.out == (a and b and c)
