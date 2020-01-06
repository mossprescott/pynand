from nand import unsigned
from nand.codegen import translate
from nand.component import Nand
from nand.integration import IC, Connection, root
import nand.syntax
import project_02
import project_03
import project_05


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


def test_cpu():
    cpu = translate(project_05.CPU.constr())()

    # HACK: copied verbatim from test_05

    cpu.instruction = 0b0011000000111001  # @12345
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 12345 and cpu.pc == 1 # and DRegister == 0

    cpu.instruction = 0b1110110000010000  # D=A
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 12345 and cpu.pc == 2 # and DRegister == 12345

    cpu.instruction = 0b0101101110100000  # @23456
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 23456 and cpu.pc == 3 # and DRegister == 12345

    cpu.instruction = 0b1110000111010000  # D=A-D
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 23456 and cpu.pc == 4 # and DRegister == 11111

    cpu.instruction = 0b0000001111101000  # @1000
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 5 # and DRegister == 11111

    cpu.instruction = 0b1110001100001000  # M=D
    cpu.tick(); cpu.tock()
    assert cpu.outM == 11111 and cpu.writeM == 1 and cpu.addressM == 1000 and cpu.pc == 6 # and DRegister == 11111

    cpu.instruction = 0b0000001111101001  # @1001
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1001 and cpu.pc == 7 # and DRegister == 11111

    # Note confusing timing here: outM has the value to be written to memory when the clock falls. Afterward,
    # outM has a nonsense value.
    # TODO: always assert outM and writeM before tick/tock?
    cpu.instruction = 0b1110001110011000  # MD=D-1
    assert cpu.outM == 11110 and cpu.writeM == 1 and cpu.addressM == 1001 and cpu.pc == 7 # and DRegister == 11111
    cpu.tick(); cpu.tock()
    assert cpu.outM == 11109 and cpu.writeM == 1 and cpu.addressM == 1001 and cpu.pc == 8 # and DRegister == 11110

    cpu.instruction = 0b0000001111101000  # @1000
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 9 # and DRegister == 11110

    cpu.instruction = 0b1111010011010000  # D=D-M
    cpu.inM = 11111
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 10 # and DRegister == -1

    cpu.instruction = 0b0000000000001110  # @14
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 14 and cpu.pc == 11 # and DRegister == -1

    cpu.instruction = 0b1110001100000100  # D;jlt
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 14 and cpu.pc == 14 # and DRegister == -1

    cpu.instruction = 0b0000001111100111  # @999
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 999 and cpu.pc == 15 # and DRegister == -1

    cpu.instruction = 0b1110110111100000  # A=A+1
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 16 # and DRegister == -1

    cpu.instruction = 0b1110001100001000  # M=D
    cpu.tick(); cpu.tock()
    assert cpu.outM == -1 and cpu.writeM == 1 and cpu.addressM == 1000 and cpu.pc == 17 # and DRegister == -1

    cpu.instruction = 0b0000000000010101  # @21
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 21 and cpu.pc == 18 # and DRegister == -1

    cpu.instruction = 0b1110011111000010  # D+1;jeq
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 21 and cpu.pc == 21 # and DRegister == -1

    cpu.instruction = 0b0000000000000010  # @2
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 2 and cpu.pc == 22 # and DRegister == -1

    cpu.instruction = 0b1110000010010000  # D=D+A
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 2 and cpu.pc == 23 # and DRegister == 1

    cpu.instruction = 0b0000001111101000  # @1000
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 24 # and DRegister == -1

    cpu.instruction = 0b1110111010010000  # D=-1
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 25 # and DRegister == -1

    cpu.instruction = 0b1110001100000001  # D;JGT
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 26 # and DRegister == -1

    cpu.instruction = 0b1110001100000010  # D;JEQ
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 27 # and DRegister == -1

    cpu.instruction = 0b1110001100000011  # D;JGE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 28 # and DRegister == -1

    cpu.instruction = 0b1110001100000100  # D;JLT
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110001100000101  # D;JNE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110001100000110  # D;JLE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110001100000111  # D;JMP
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == -1

    cpu.instruction = 0b1110101010010000  # D=0
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 0

    cpu.instruction = 0b1110001100000001  # D;JGT
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1002 # and DRegister == 0

    cpu.instruction = 0b1110001100000010  # D;JEQ
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110001100000011  # D;JGE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110001100000100  # D;JLT
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 0

    cpu.instruction = 0b1110001100000101  # D;JNE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1002 # and DRegister == 0

    cpu.instruction = 0b1110001100000110  # D;JLE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110001100000111  # D;JMP
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 0

    cpu.instruction = 0b1110111111010000  # D=1
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000001  # D;JGT
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.instruction = 0b1110001100000010  # D;JEQ
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000011  # D;JGE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.instruction = 0b1110001100000100  # D;JLT
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000101  # D;JNE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.instruction = 0b1110001100000110  # D;JLE
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1001 # and DRegister == 1

    cpu.instruction = 0b1110001100000111  # D;JMP
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 1000 # and DRegister == 1

    cpu.reset = 1
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 1000 and cpu.pc == 0 # and DRegister == 1

    cpu.instruction = 0b0111111111111111  # @32767
    cpu.reset = 0
    cpu.tick(); cpu.tock()
    assert cpu.writeM == 0 and cpu.addressM == 32767 and cpu.pc == 1 # and DRegister == 1
