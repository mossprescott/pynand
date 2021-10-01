#! /usr/bin/env pytest

from nand import run

from alt.risc.chip import *


def test_alu():
    alu = run(ALU)

    alu.src1 = 1
    alu.src2 = 3

    # ADD
    alu.op = 0
    assert alu.out == 4

    # NAND
    alu.op = 1
    assert alu.out == -2

    # PASS1
    alu.op = 2
    assert alu.out == 1

    # EQ?
    alu.op = 3
    assert alu.eq == 0
    alu.src1 = alu.src2 = -32123
    assert alu.eq == 1


def test_alu_gate_count():
    # Compare to project_02's ~560 nands
    assert gate_count(ALU) == {
        "nands": 413,
    }



def test_register_file():
    rf = run(RegisterFile)

    # set each register (including r0, which doesn't actually have any effect)
    rf.load = 1
    for i in range(8):
        rf.target = i
        rf.in_ = i
        rf.ticktock()

    # each value separately retained
    rf.load = 0
    for i in range(8):
        rf.address1 = i
        rf.address2 = 0
        assert rf.out1 == i
        assert rf.out2 == 0

        rf.address1 = 0
        rf.address2 = i
        assert rf.out1 == 0
        assert rf.out2 == i

    # writing to r0 has no effect:
    rf.target = 0
    rf.in_ = 42
    rf.load = 1
    rf.ticktock()

    rf.address1 = rf.address2 = 0
    assert rf.out1 == 0
    assert rf.out2 == 0

def test_register_file_gate_count():
    assert gate_count(RegisterFile) == {
        "nands": 1157,  # Note: unrealistically high?
        "dffs": 16*7,
    }


def test_control():
    control = run(Control)

    control.op = 0  # add
    assert control.registerLoad == 1
    assert control.registerAddress2Sel == 1
    assert control.aluSrc1Sel == 0
    assert control.aluSrc2Sel == 0
    assert control.aluOp == 0  # 00 = ADD
    assert control.memLoad == 0
    assert control.loadMem == 0
    assert control.isJump == 0
    assert control.isBranch == 0

    # Note: this component ends up being declarative, so not much point in testing
    # every combination.


def test_control_gate_count():
    """10 output signals, 3 input bits, and a certain amount of logic."""
    # Note: compare to 24 gates per output for the dumbest possible Mux every time.
    assert gate_count(Control) == {
        "nands": 35,  # 10*24
    }


def test_cpu_compute():
    cpu = run(CPU, simulator="vector")

    cpu.instruction = 0b010_001_000_0000_000  # nand r1 r0 r0
    cpu.ticktock()
    assert peek_reg(cpu, 1) == -1

    cpu.instruction = 0b000_010_001_0000_001  # add r2 r1 r1
    cpu.ticktock()
    assert peek_reg(cpu, 2) == -2

def peek_reg(cpu, reg):
    """Inspect the value of a register by applying the `sw` opcode and
    looking at the value that's presented to the memory.
    """
    cpu.instruction = 0b101_000_000_0000000 | (reg << 10)
    return cpu.outM


def test_cpu_immediate():
    cpu = run(CPU, simulator="codegen")

    cpu.instruction = 0b001_001_000_0000001  # addi r1 r0 1
    cpu.ticktock()
    assert peek_reg(cpu, 1) == 1

    cpu.instruction = 0b001_010_000_1111111  # addi r2 r0 -1
    cpu.ticktock()
    assert peek_reg(cpu, 2) == -1

    # The largest positive value you can load with addi is (1 << 6) - 1:
    cpu.instruction = 0b001_001_000_0111111  # addi r1 r0 63
    cpu.ticktock()
    assert peek_reg(cpu, 1) == 63

    # The largest negative value you can load with addi is (-1 << 6):
    cpu.instruction = 0b001_010_000_1000000  # addi r2 r0 -64
    cpu.ticktock()
    assert peek_reg(cpu, 2) == -64


    # The smallest positive value you can load with lui is 1 << 6:
    cpu.instruction = 0b011_011_00_0000_0001  # lui r3 r0 64
    cpu.ticktock()
    assert peek_reg(cpu, 3) == 64

    # The smallest nagative value you can load with lui is -1 << 6:
    cpu.instruction = 0b011_011_11_1111_1111  # lui r3 r0 -64
    cpu.ticktock()
    assert peek_reg(cpu, 3) == -64


def test_cpu_load():
    cpu = run(CPU, simulator="codegen")

    cpu.instruction = 0b100_100_000_010_1010  # lw r4 r0 42

    # Asks the memory for the correct address:
    assert cpu.addressM == 42

    # Stores the value the memory presents:
    cpu.inM = 12345
    cpu.ticktock()
    peek_reg(cpu, 4) == 12345

    cpu.instruction = 0b100_101_000_010_1011  # lw r5 r0 43
    cpu.inM = 33333
    cpu.ticktock()

    peek_reg(cpu, 4) == 12345
    peek_reg(cpu, 5) == 33333


def test_cpu_branch():
    cpu = run(CPU, simulator="codegen")

    cpu.instruction = 0b000_000_000_0000_000  # add r0 r0 r0
    cpu.ticktock()
    assert cpu.pc == 1

    cpu.instruction = 0b110_000_000_0000001  # beq r0 r0 +1
    cpu.ticktock()
    assert cpu.pc == 3

def test_cpu_gate_count():
    assert gate_count(CPU) == {
        "nands": 2500,  # ?
        "dffs": 8*16,
    }


def test_computer_load():
    """Somewhat redundantly, test that loads actually get recorded."""

    computer = run(RiSCComputer)

    # Copy a value from RAM to r1 (aka SP), and then back to RAM:
    computer.init_rom([
        0b100_001_000_0001111,  # lw r1 r0 15
        0b101_001_000_0011111,  # sw r1 r0 31
    ])

    computer.poke(15, 12345)

    computer.ticktock()
    computer.ticktock()

    assert computer.pc == 2
    assert computer.peek(31) == 12345
