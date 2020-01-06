from nand import unsigned
from nand.codegen import translate
from nand.component import Nand
from nand.integration import IC, Connection, root
import nand.syntax
import project_02
import project_03


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
    alu = translate(project_02.ALU.constr())()
    
    # HACK: copied verbatim from test_02
    
    alu.x = 0
    alu.y = -1 

    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # 0
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # -1
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0  # X
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # Y
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1  # !X
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1  # !Y
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # -X
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # -Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # X + 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y + 1
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0  # X - 1
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # Y - 1
    assert alu.out == -2 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # X + Y
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # X - Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y - X
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # X & Y
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1  # X | Y
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1


    alu.x = 17
    alu.y = 3 

    alu.zx = 1; alu.nx = 0; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # 0
    assert alu.out == 0 and alu.zr == 1 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # 1
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 1; alu.ny = 0; alu.f = 1; alu.no = 0  # -1
    assert alu.out == -1 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 0  # X
    assert alu.out == 17 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # Y
    assert alu.out == 3 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 0; alu.no = 1  # !X
    assert alu.out == -18 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 1  # !Y
    assert alu.out == -4 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # -X
    assert alu.out == -17 and alu.zr == 0 and alu.ng == 1

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # -Y
    assert alu.out == -3 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 1; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 1  # X + 1
    assert alu.out == 18 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y + 1
    assert alu.out == 4 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 1; alu.ny = 1; alu.f = 1; alu.no = 0  # X - 1
    assert alu.out == 16 and alu.zr == 0 and alu.ng == 0

    alu.zx = 1; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # Y - 1
    assert alu.out == 2 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 0  # X + Y
    assert alu.out == 20 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 0; alu.f = 1; alu.no = 1  # X - Y
    assert alu.out == 14 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 1; alu.f = 1; alu.no = 1  # Y - X
    assert alu.out == -14 and alu.zr == 0 and alu.ng == 1

    alu.zx = 0; alu.nx = 0; alu.zy = 0; alu.ny = 0; alu.f = 0; alu.no = 0  # X & Y
    assert alu.out == 1 and alu.zr == 0 and alu.ng == 0

    alu.zx = 0; alu.nx = 1; alu.zy = 0; alu.ny = 1; alu.f = 0; alu.no = 1  # X | Y
    assert alu.out == 19 and alu.zr == 0 and alu.ng == 0


def test_pc():
    pc = translate(project_03.PC.constr())()

    # HACK: copied verbatim from test_02

    pc.in_ = 0; pc.reset = 0; pc.load = 0; pc.inc = 0
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.inc = 1
    pc.tick(); pc.tock()
    assert pc.out == 1

    pc.in_ = -32123
    pc.tick(); pc.tock()
    assert pc.out == 2

    pc.load = 1
    pc.tick(); pc.tock()
    assert pc.out == -32123

    pc.load = 0
    pc.tick(); pc.tock()
    assert pc.out == -32122

    pc.tick(); pc.tock()
    assert pc.out == -32121

    pc.in_ = 12345; pc.load = 1; pc.inc = 0
    pc.tick(); pc.tock()
    assert pc.out == 12345

    pc.reset = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.reset = 0; pc.inc = 1
    pc.tick(); pc.tock()
    assert pc.out == 12345

    pc.reset = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.reset = 0; pc.load = 0
    pc.tick(); pc.tock()
    assert pc.out == 1

    pc.reset = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.in_ = 0; pc.reset = 0; pc.load = 1
    pc.tick(); pc.tock()
    assert pc.out == 0

    pc.load = 0; pc.inc = 1
    pc.tick(); pc.tock()
    assert pc.out == 1

    pc.in_ = 22222; pc.reset = 1; pc.inc = 0
    pc.tick(); pc.tock()
    assert pc.out == 0

