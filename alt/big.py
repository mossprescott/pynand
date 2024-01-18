#! python

"""A computer with a single 16-bit address space for ROM and RAM.

Uses the same ISA and assembler as the normal Hack CPU.

Both instructions and data can be read from any address.

Writes to ROM addresses are ignored.

A small portion of the RAM is reserved for screen buffer and I/O:
- 1000 words to hold 80x25 8-bit characters
- Keyboard and TTY in the same 1024-word "page".
- 23 other words are available for future expansion.

Layout considerations:
- ROM is only large enough to fit a scheme/basic/forth interpreter (8K?)
- Screen buffer and I/O: 1K
- RAM fills as much of the rest of 64K as possible
- The low-memory page is RAM, for convenient access
- The ROM lives in the 15-bit addressable range, so a code address can always be loaded in one cycle
- "negative" addresses are a uniform block of RAM, useful for heap


| Address Range | Size (words) | Storage | Contents                       |
| 0x0000–0x03FF | 1K           | RAM     | Temporaries, "registers", etc. |
| 0x0400–0x07FF | 1K           | RAM     | Screen buffer and I/O          |
| 0x0800–0x7FFF | 30K          | ROM     | Code: boot/runtime; data       |
| 0x8000–0xFFFF | 32K          | RAM     | Heap or other large blocks     |

Note: it's also possible to treat all negative values as addresses in a continous block of RAM
starting at 0x8000 = -32768. In fact, this range extends all the way to the bottom of the ROM
at 0x0800 = 2048.

TODO: make the size of the ROM configurable, so you can trade off heap space vs runtime size.
"""

from nand import chip, lazy, RAM, ROM, Input, Output, DFF
from project_01 import And, Or, Not
from project_03 import Mux, Mux16, Register, PC, ALU
import project_05
from alt.threaded import Eq16


SCREEN_BASE   = 0x0400
KEYBOARD_ADDR = 0x07FF
ROM_BASE      = 0x0800
HEAP_BASE     = 0x8000

@chip
def FlatMemory(inputs, outputs):
    """The same interface as MemorySystem, but also maps the ROM and extends address to the full 16 bits.

    Note: this will need some additional support in the "codegen" simulator, which otherwise implements
    the standard MemoryStstem directly.
    """

    in_ = inputs.in_
    load = inputs.load
    address = inputs.address

    # addresses 0x08-- through 0x7F-- are in the ROM:
    # - high bits 00001–01111   (0000 1000 0000 0000 to 0111 1111 1111 1111)
    # - or, 0... 1... .... ....
    # - or, 1 <= (address >> 11) < 16
    is_rom = And(a=Not(in_=address[15]).out,
                 b=Or(a=Or(a=address[14],
                           b=address[13]).out,
                      b=Or(a=address[12],
                           b=address[11]).out).out).out

    is_io = Eq16(a=address, b=KEYBOARD_ADDR).out

    ram = RAM(16)(in_=in_, load=load, address=address)  # Fully 64K; partially hidden by the ROM
    rom = ROM(15)(address=address)  # Based at 0 and sized to 32K, but partially hidden by RAM
    # screen = RAM(10) # Separate RAM would make life easier for the harness?
    keyboard = Input()
    tty = Output(in_=in_, load=is_io)

    outputs.out = Mux16(sel=is_io,
                        a=Mux16(sel=is_rom, a=ram.out, b=rom.out).out,
                        b=keyboard.out).out
    outputs.tty_ready = tty.ready


@chip
def IdlableCPU(inputs, outputs):
    """Same as the standard CPU, plus an 'idle' input that suspends all state updates."""

    inM = inputs.inM                 # M value input (M = contents of RAM[A])
    instruction = inputs.instruction # Instruction for execution
    reset = inputs.reset             # Signals whether to re-start the current
                                     # program (reset==1) or continue executing
                                     # the current program (reset==0).
    # Extra for fetch/execute cycles:
    idle = inputs.idle               # When set, *don't* update any state

    i, _, _, a, c5, c4, c3, c2, c1, c0, da, dd, dm, jlt, jeq, jgt = [instruction[j] for j in reversed(range(16))]

    not_i = Not(in_=i).out

    not_idle = Not(in_=idle).out

    alu = lazy()
    a_reg = Register(in_=Mux16(a=instruction, b=alu.out, sel=i).out,
                     load=And(a=not_idle, b=Or(a=not_i, b=da).out).out)
    d_reg = Register(in_=alu.out,
                     load=And(a=not_idle, b=And(a=i, b=dd).out).out)
    jump_lt = And(a=alu.ng, b=jlt).out
    jump_eq = And(a=alu.zr, b=jeq).out
    jump_gt = And(a=And(a=Not(in_=alu.ng).out, b=Not(in_=alu.zr).out).out, b=jgt).out
    jump = And(a=i,
               b=Or(a=jump_lt, b=Or(a=jump_eq, b=jump_gt).out).out
              ).out
    pc = PC(in_=a_reg.out, load=jump, inc=not_idle, reset=reset)
    alu.set(ALU(x=d_reg.out, y=Mux16(a=a_reg.out, b=inM, sel=a).out,
                zx=c5, nx=c4, zy=c3, ny=c2, f=c1, no=c0))


    outputs.outM = alu.out                   # M value output
    outputs.writeM = And(a=dm, b=i).out      # Write to M?
    outputs.addressM = a_reg.out             # Address in data memory (of M) (latched)
    outputs.pc = pc.out                      # address of next instruction (latched)


@chip
def BigComputer(inputs, outputs):
    """A computer with the standard CPU, but mapping RAM, ROM, and I/O into the same large, flat
    memory space.

    In every even (fetch) cycle, an instruction is read from memory and stored in an extra Register.
    In odd (execute) cycles, memory and cpu state are updated as required by the instruction.

    Note: on start/reset, instructions from address 0 are read. Since a zero-value instruction
    just loads 0 into A, we effectively execute 2K no-op "@0" instructions before reaching the
    first actual ROM address.

    TODO: some instructions don't require access to the memory; they don't read or write from/to M.
    In that case, we could fetch and execute in a single cycle if the CPU exposed that info or took
    over control of the cycles. It looks like possibly as much as 50% of all instructions could
    execute in one cycle for 25% speedup. On the other hand, it would complicate tests somewhat
    unless we add "performance counters" to the CPU to keep track.
    """

    reset = inputs.reset

    # A DFF to split each pair of cycles into two halves:
    # fetch is True in the first half-cycle, when the instruction is fetched from memory.
    # execute is True in the second half-cycle, when any read/write operations are done.
    # The DFF stores execute (= !fetch), so that we start in fetch.
    half_cycle = lazy()
    fetch = Not(in_=half_cycle.out).out
    half_cycle.set(DFF(in_=Mux(a=fetch, b=0, sel=reset).out))
    execute = half_cycle.out

    cpu = lazy()

    mem = FlatMemory(in_=cpu.outM,
                     load=And(a=execute, b=cpu.writeM).out,
                     address=Mux16(a=cpu.pc, b=cpu.addressM, sel=execute).out)

    instr_reg = Register(in_=cpu.pc, load=fetch)

    # TODO: Set an instruction code that results in less computation during simulation, or is
    # there a way to do that that's more realistic? Maybe just leave the instruction unchanged
    # and disable all state updates; if the ALUs inputs don't change, it consumes no power?
    # Does that apply to (vector) simulation?
    cpu.set(IdlableCPU(inM=mem.out,
                       instruction=instr_reg.out,
                       reset=reset,
                       idle=fetch))

    # HACK: need some dependency to force the whole thing to be synthesized.
    # Exposing the PC also makes it easy to observe what's happening in a dumb way.
    outputs.pc = cpu.pc

    # HACK: similar issues, but in this case it's just the particular component that
    # needs to be forced to be included.
    outputs.tty_ready = mem.tty_ready

