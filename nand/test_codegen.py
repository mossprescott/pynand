from nand import unsigned
from nand.codegen import translate
from nand.component import Nand
from nand.integration import IC, Connection, root
import nand.syntax
from project_02 import ALU


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


def test_alu():
    alu = translate(ALU.constr())()
    
    # HACK: copied verbatim from test_02
    
    alu.x = 0
    alu.y = -1 
    
    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 0   # 0
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 1   # 1
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == -1  # -1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0; assert alu.out == 0   # X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == -1  # Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1; assert alu.out == -1  # !X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1; assert alu.out == 0   # !Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 0   # -X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 1   # -Y
    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 1   # X + 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 0   # Y + 1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0; assert alu.out == -1  # X - 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == -2  # Y - 1
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == -1  # X + Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 1   # X - Y
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == -1  # Y - X
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == 0   # X & Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1; assert alu.out == -1  # X | Y


    alu.x = 23456
    alu.y = 7890
    
    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 0      # 0
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 1      # 1
    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == -1     # -1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0; assert alu.out == 23456  # X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert alu.out == 7890   # Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1; assert unsigned(alu.out) == 0xA45F # !X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1; assert unsigned(alu.out) == 0xE12D # !Y
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == -23456 # -X
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == -7890  # -Y
    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 23457  # X + 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == 7891   # Y + 1
    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0; assert alu.out == 23455  # X - 1
    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 7889   # Y - 1
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0; assert alu.out == 31346  # X + Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1; assert alu.out == 15566  # X - Y
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1; assert alu.out == -15566 # Y - X
    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0; assert unsigned(alu.out) == 0x1A80 # X & Y
    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1; assert unsigned(alu.out) == 0x5FF2 # X | Y
