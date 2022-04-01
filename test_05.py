#! /usr/bin/env pytest

from nand import run
import nand.component
import project_05


def test_memory_system():
    mem = run(project_05.MemorySystem)

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
    mem.tick(); mem.tock()
    assert mem.out == 0
    mem.address = 0x4000
    mem.tick(); mem.tock()
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
    mem.tick(); mem.tock()
    assert mem.out == -1
    mem.address = 0x4000
    mem.tick(); mem.tock()
    assert mem.out == 0

    # Low order address bits connected
    # (note: not actually testing anything in this system?)
    mem.address = 0x0001; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0002; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0004; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0008; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0010; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0020; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0040; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0080; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0100; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0200; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0400; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x0800; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x1000; mem.tick(); mem.tock(); assert mem.out == 0
    mem.address = 0x2000; mem.tick(); mem.tock(); assert mem.out == 2222

    # RAM[0x1234] = 1234
    mem.address = 0x1234
    mem.in_ = 1234
    mem.load = 1
    mem.tick(); mem.tock()
    assert mem.out == 1234

    # Did not also write to upper RAM or Screen
    mem.load = 0
    mem.address = 0x2234
    mem.tick(); mem.tock()
    assert mem.out == 0
    mem.address = 0x6234
    mem.tick(); mem.tock()
    assert mem.out == 0

    # RAM[0x2345] = 2345
    mem.address = 0x2345
    mem.in_ = 2345
    mem.load = 1
    mem.tick(); mem.tock()
    assert mem.out == 2345

    # Did not also write to lower RAM or Screen
    mem.load = 0
    mem.address = 0x0345
    mem.tick(); mem.tock()
    assert mem.out == 0
    mem.address = 0x4345
    mem.tick(); mem.tock()
    assert mem.out == 0


    ### Keyboard test

    ## Note: this test can't be done on the isolated MemorySystem, because the necessary
    ## connections are only provided when the simulator detects the full Computer is being
    ## simulated. Instead, we test it below.
    # mem.address = 0x6000
    # assert mem.out == 75


    ### Screen test

    mem.load = 1
    mem.in_ = -1
    mem.address = 0x4fcf
    mem.tick(); mem.tock()
    assert mem.out == -1

    mem.address = 0x504f
    mem.tick(); mem.tock()
    assert mem.out == -1

def a_contents(cpu):
    """Inspect the contents of the A register, by applying a bit pattern that forces it onto the memory input."""
    # cpu.instruction = 0b1111010011010000  # D=D-M
    # cpu.instruction = 0b1110110000010000  # D=A
    # cpu.instruction = 0b1111110000010000  # D=M
    cpu.instruction = 0b1110110000001000  # M=A
    return cpu.outM

def d_contents(cpu):
    """Inspect the contents of the D register, by applying a bit pattern that forces it onto the memory input."""
    cpu.instruction = 0b1110001100001000  # M=D
    return cpu.outM


def test_cpu(chip=project_05.CPU):
    cpu = run(chip, simulator="codegen")

    cpu.instruction = 0b0011000000111001  # @12345
    assert cpu.writeM == 0 and cpu.addressM == 12345
    cpu.ticktock()
    assert cpu.pc == 1 and d_contents(cpu) == 0

    cpu.instruction = 0b1110110000010000  # D=A
    assert cpu.writeM == 0 and cpu.addressM == 12345
    cpu.ticktock()
    assert cpu.pc == 2 and d_contents(cpu) == 12345

    cpu.instruction = 0b0101101110100000  # @23456
    assert cpu.writeM == 0 and cpu.addressM == 23456
    cpu.ticktock()
    assert cpu.pc == 3 and d_contents(cpu) == 12345

    cpu.instruction = 0b1110000111010000  # D=A-D
    assert cpu.writeM == 0 and cpu.addressM == 23456
    cpu.ticktock()
    assert cpu.pc == 4 and d_contents(cpu) == 11111

    cpu.instruction = 0b0000001111101000  # @1000
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 5 and d_contents(cpu) == 11111

    cpu.instruction = 0b1110001100001000  # M=D
    assert cpu.outM == 11111 and cpu.writeM == 1 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 6 and d_contents(cpu) == 11111

    cpu.instruction = 0b0000001111101001  # @1001
    assert cpu.writeM == 0 and cpu.addressM == 1001
    cpu.ticktock()
    assert cpu.pc == 7 and d_contents(cpu) == 11111

    # Note confusing timing here: outM has the value to be written to memory when the clock falls. Afterward,
    # outM has a nonsense value.
    # TODO: always assert outM and writeM before tick/tock?
    cpu.instruction = 0b1110001110011000  # MD=D-1
    assert cpu.outM == 11110 and cpu.writeM == 1 and cpu.addressM == 1001
    cpu.ticktock()
    # assert cpu.pc == 7 and d_contents(cpu) == 11111
    # cpu.ticktock()
    # assert cpu.outM == 11109 and cpu.writeM == 1 and cpu.addressM == 1001
    # cpu.ticktock()
    assert cpu.pc == 8 and d_contents(cpu) == 11110

    cpu.instruction = 0b0000001111101000  # @1000
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 9 and d_contents(cpu) == 11110

    cpu.instruction = 0b1111010011010000  # D=D-M
    cpu.inM = 11111
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 10 and d_contents(cpu) == -1

    cpu.instruction = 0b0000000000001110  # @14
    assert cpu.writeM == 0 and cpu.addressM == 14
    cpu.ticktock()
    assert cpu.pc == 11 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000100  # D;jlt
    assert cpu.writeM == 0 and cpu.addressM == 14
    cpu.ticktock()
    assert cpu.pc == 14 and d_contents(cpu) == -1

    cpu.instruction = 0b0000001111100111  # @999
    assert cpu.writeM == 0 and cpu.addressM == 999
    cpu.ticktock()
    assert cpu.pc == 15 and d_contents(cpu) == -1

    # Note: when the instruction both reads and writes A, the addressM output will change at the
    # cycle boundary, so the timing of the tests matters.
    cpu.instruction = 0b1110110111100000  # A=A+1
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 16 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100001000  # M=D
    assert cpu.outM == -1 and cpu.writeM == 1 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 17 and d_contents(cpu) == -1

    cpu.instruction = 0b0000000000010101  # @21
    assert cpu.writeM == 0 and cpu.addressM == 21
    cpu.ticktock()
    assert cpu.pc == 18 and d_contents(cpu) == -1

    cpu.instruction = 0b1110011111000010  # D+1;jeq
    assert cpu.writeM == 0 and cpu.addressM == 21
    cpu.ticktock()
    assert cpu.pc == 21 and d_contents(cpu) == -1

    cpu.instruction = 0b0000000000000010  # @2
    assert cpu.writeM == 0 and cpu.addressM == 2
    cpu.ticktock()
    assert cpu.pc == 22 and d_contents(cpu) == -1

    cpu.instruction = 0b1110000010010000  # D=D+A
    assert cpu.writeM == 0 and cpu.addressM == 2
    cpu.ticktock()
    assert cpu.pc == 23 and d_contents(cpu) == 1

    cpu.instruction = 0b0000001111101000  # @1000
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 24 and d_contents(cpu) == 1

    cpu.instruction = 0b1110111010010000  # D=-1
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 25 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000001  # D;JGT
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 26 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000010  # D;JEQ
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 27 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000011  # D;JGE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 28 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000100  # D;JLT
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000101  # D;JNE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000110  # D;JLE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == -1

    cpu.instruction = 0b1110001100000111  # D;JMP
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == -1

    cpu.instruction = 0b1110101010010000  # D=0
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1001 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000001  # D;JGT
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1002 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000010  # D;JEQ
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000011  # D;JGE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000100  # D;JLT
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1001 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000101  # D;JNE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1002 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000110  # D;JLE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 0

    cpu.instruction = 0b1110001100000111  # D;JMP
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 0

    cpu.instruction = 0b1110111111010000  # D=1
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1001 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000001  # D;JGT
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000010  # D;JEQ
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1001 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000011  # D;JGE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000100  # D;JLT
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1001 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000101  # D;JNE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000110  # D;JLE
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1001 and d_contents(cpu) == 1

    cpu.instruction = 0b1110001100000111  # D;JMP
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 1000 and d_contents(cpu) == 1

    cpu.reset = 1
    assert cpu.writeM == 0 and cpu.addressM == 1000
    cpu.ticktock()
    assert cpu.pc == 0 and d_contents(cpu) == 1

    cpu.instruction = 0b0111111111111111  # @32767
    cpu.reset = 0
    assert cpu.writeM == 0 and cpu.addressM == 32767
    cpu.ticktock()
    assert cpu.pc == 1 and d_contents(cpu) == 1


def test_computer_no_program(chip=project_05.Computer):
    computer = run(chip)

    for _ in range(100):
        computer.ticktock()

    assert computer.pc == 100


# Add.hack:
ADD_PROGRAM = [
    0b0000000000000010,  # @2
    0b1110110000010000,  # D=A
    0b0000000000000011,  # @3
    0b1110000010010000,  # D=D+A
    0b0000000000000001,  # @1     Note: modified to avoid address 0 (SP), which may get special treatment
    0b1110001100001000,  # M=D
]

def test_computer_add(chip=project_05.Computer, simulator="vector"):
    computer = run(chip, simulator=simulator)

    # First run (at the beginning PC=0)
    computer.run_program(ADD_PROGRAM)

    assert computer.peek(1) == 5


    # Reset the PC
    computer.reset = 1
    computer.ticktock()
    assert computer.pc == 0

    # Second run, to check that the PC was reset correctly.
    computer.poke(1, 12345)
    computer.reset = 0
    while computer.pc < len(ADD_PROGRAM):
        computer.ticktock()

    assert computer.peek(1) == 5


MAX_PROGRAM = [
    # Note: modified to avoid address 0 (SP), which may get special treatment
    0b0000000000000001,  #  0: @1
    0b1111110000010000,  #  1: D=M
    0b0000000000000010,  #  2: @2
    0b1111010011010000,  #  3: D=D-M  ; D = mem[1] - mem[2]
    0b0000000000001010,  #  4: @10
    0b1110001100000001,  #  5: D; JGT
    0b0000000000000010,  #  6: @2
    0b1111110000010000,  #  7: D=M    ; D = mem[2]
    0b0000000000001100,  #  8: @12
    0b1110101010000111,  #  9: JMP
    0b0000000000000001,  # 10: @1
    0b1111110000010000,  # 11: D=M    ; D = mem[1]
    0b0000000000000011,  # 12: @3
    0b1110001100001000,  # 13: M=D    ; mem[3] = max
    0b0000000000001110,  # 14: @14
    0b1110101010000111,  # 15: JMP    ; infinite loop
]

def test_computer_max(chip=project_05.Computer, simulator="vector", cycles_per_instr=1):
    computer = run(chip, simulator=simulator)

    computer.init_rom(MAX_PROGRAM)

    # first run: compute max(3,5)
    computer.poke(1, 3)
    computer.poke(2, 5)
    for _ in range(14*cycles_per_instr):
        computer.ticktock()
    assert computer.peek(3) == 5

    # second run: compute max(23456,12345)
    computer.reset_program()
    computer.poke(1, 23456)
    computer.poke(2, 12345)
    # The run on these inputs needs less cycles (different branching)
    for _ in range(10*cycles_per_instr):
        computer.ticktock()
    assert computer.peek(3) == 23456

# Copy one keycode value from the address where the keyboard is mapped to the RAM.
COPY_INPUT_PROGRAM = [
    24576, # @(0x6000)
    64528, # D=M     (D = keycode)
    1,     # @1
    58120, # M=D     (mem[1] = D)
    4,     # @4
    60039, # 0;JMP   (infinite loop)
]

def test_computer_keyboard(chip=project_05.Computer, simulator="vector", cycles_per_instr=1):
    """A value which is presented via a special `Input` component can be read from the
    address 0x6000, where the "keyboard" is mapped.

    Note: can't test this at the level of MemorySystem, because the wrapper for the full
    computer provides some of the necessary plumbing.
    """

    computer = run(chip, simulator=simulator)

    computer.init_rom(COPY_INPUT_PROGRAM)

    KEY_A = ord("a")

    computer.set_keydown(KEY_A)
    for _ in range(4*cycles_per_instr):
        computer.ticktock()

    assert computer.peek(1) == KEY_A


def test_computer_tty_no_program(chip=project_05.Computer, simulator="vector"):
    """When nothing has been written address 0x6000, no value is available on the TTY "port".
    """

    computer = run(chip, simulator=simulator)

    for _ in range(100):
        computer.ticktock()

    assert computer.pc == 100
    assert computer.tty_ready == True
    assert computer.get_tty() == 0


# Write a few constant values to the external "tty" interface:
WRITE_TTY_PROGRAM = [
    1,      # @1
    60432,  # D=A
    24576,  # @(0x6000)
    58120,  # M=D   (write 1)

    0,      # @0
    60432,  # D=A
    24576,  # @(0x6000)
    58120,  # M=D   ("write" 0; no effect)

    12345,  # @12345
    60432,  # D=A
    24576,  # @(0x6000)
    58120,  # M=D   (write 12345)

    12,     # @12
    60039,  # 0; JMP  (infinite loop)
]

def test_computer_tty(chip=project_05.Computer, simulator="vector", cycles_per_instr=1):
    """A value which is written to the address 0x6000 can be read from outside via
    a special `Output` component.

    Also, the presence of a value in that component is signalled by the `tty_ready`

    Note: can't test this at the level of MemorySystem, because the wrapper for the full
    computer provides some of the necessary plumbing.
    """

    computer = run(chip, simulator=simulator)

    computer.init_rom(WRITE_TTY_PROGRAM)

    # Run until a value appears (after 4 instructions):

    cycles = 0
    while computer.tty_ready and cycles < 1000:
        computer.ticktock()
        cycles += 1

    print(f"cycles: {cycles}")
    assert computer.tty_ready == False
    assert computer.get_tty() == 1
    assert computer.tty_ready == True
    assert cycles == 4*cycles_per_instr   # Bogus?


    # Now run four more instructions; nothing written this time:

    for _ in range(4*cycles_per_instr):
        computer.ticktock()

    assert computer.tty_ready == True
    assert computer.get_tty() == 0
    assert computer.tty_ready == True


    # One more time, with a different value:

    cycles = 0
    while computer.tty_ready and cycles < 1000:
        computer.ticktock()
        cycles += 1

    assert computer.tty_ready == False
    assert computer.get_tty() == 12345
    assert computer.tty_ready == True
    assert cycles == 4*cycles_per_instr   # Bogus?



def cycles_per_second(chip, cycles_per_instr=1):
    """Estimate the speed of CPU simulation by running Max repeatedly with random input.
    """

    import random
    import timeit

    computer = run(chip)

    computer.init_rom(MAX_PROGRAM)

    CYCLES = 14*cycles_per_instr

    def once():
        x = random.randint(0, 0x7FFF)
        y = random.randint(0, 0x7FFF)
        computer.reset_program()
        computer.poke(1, x)
        computer.poke(2, y)
        for _ in range(CYCLES):
            computer.ticktock()
        assert computer.peek(3) == max(x, y)

    count, time = timeit.Timer(once).autorange()

    return count*CYCLES/time


def test_speed(chip=project_05.Computer, cycles_per_instr=1):
    cps = cycles_per_second(chip, cycles_per_instr)
    print(f"Measured speed: {cps:0,.1f} cycles/s")
    assert cps > 500  # Note: about 1k/s is expected, but include a wide margin for random slowness
