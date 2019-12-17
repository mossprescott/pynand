from project_05 import *

def test_memory_system():
    mem = run(MemorySystem)

    # set RAM[0] = -1
    mem.in_ = -1
    mem.load = 1
    mem.address = 0
    mem.tick(); mem.tock()

    # RAM[0] holds value
    mem.in_ = 9999
    mem.load = 0
    mem.tick(); mem.tock()
    assert mem.out == -1

    # Did not also write to upper RAM or Screen
    mem.address = 0x2000
    assert mem.out == 0
    mem.address = 0x4000
    assert mem.out == 0

    # Set RAM[2000] = 2222
    mem.in_ = 2222
    mem.load = 1
    mem.address = 0x2000
    mem.tick(); mem.tock()
    assert mem.out == 2222

    # RAM[2000] holds value
    mem.in_ = 9999
    mem.load = 0
    mem.tick(); mem.tock()
    assert mem.out == 2222

    # Did not also write to lower RAM or Screen
    mem.address = 0
    assert mem.out == -1
    mem.address = 0x4000
    assert mem.out == 0

    # Low order address bits connected
    # (note: not actually testing anything in this system?)
    mem.address = 0x0001; assert mem.out == 0
    mem.address = 0x0002; assert mem.out == 0
    mem.address = 0x0004; assert mem.out == 0
    mem.address = 0x0008; assert mem.out == 0
    mem.address = 0x0010; assert mem.out == 0
    mem.address = 0x0020; assert mem.out == 0
    mem.address = 0x0040; assert mem.out == 0
    mem.address = 0x0080; assert mem.out == 0
    mem.address = 0x0100; assert mem.out == 0
    mem.address = 0x0200; assert mem.out == 0
    mem.address = 0x0400; assert mem.out == 0
    mem.address = 0x0800; assert mem.out == 0
    mem.address = 0x1000; assert mem.out == 0
    mem.address = 0x2000; assert mem.out == 2222

    # RAM[0x1234] = 1234
    mem.address = 0x1234
    mem.in_ = 1234
    mem.load = 1
    mem.tick(); mem.tock()
    assert mem.out == 1234

    # Did not also write to upper RAM or Screen
    mem.address = 0x2234
    assert mem.out == 0
    mem.address = 0x6234
    assert mem.out == 0

    # RAM[0x2345] = 2345
    mem.address = 0x2345
    mem.in_ = 2345
    mem.load = 1
    mem.tick(); mem.tock()
    assert mem.out == 2345

    # Did not also write to lower RAM or Screen
    mem.address = 0x0345
    assert mem.out == 0
    mem.address = 0x4345
    assert mem.out == 0


    ### Keyboard test

    mem.address = 0x6000
    # TODO: simulate 'k' key pressed
    # assert mem.out == 75
    assert mem.out == 0


    ### Screen test

    mem.load = 1
    mem.in_ = -1
    mem.address = 0x4fcf
    mem.tick(); mem.tock()
    assert mem.out == -1

    mem.address = 0x504f
    mem.tick(); mem.tock()
    assert mem.out == -1


def test_cpu():
    cpu = run(CPU)

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


def test_computer_no_program():
    computer = run(Computer)
    
    for _ in range(100):
        computer.tick(); computer.tock()
    
    assert computer.pc == 100
