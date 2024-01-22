#! /usr/bin/env python

"""A computer with a single 16-bit address space for ROM and RAM.

Uses the same ISA and assembler as the normal Hack CPU, with a few extensions.

Both instructions and data can be read from any address. *Note: because instructions and
data share the single memory bus, it now takes 2 cycles to fetch and execute most if not
all instructions.* This is more or less authentic to early integrated CPUs, which were
designed to minimize pinout while making effective use of whatever memory the customer
was able to afford.

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
That means synthesizing the logic to overlay the right adress range, so maybe you just select
one of a few available sizes, e.g. 2K, 6K, 10K, 14K, 30K?

"Character-mode" graphics make more efficient use of memory, with only 1k allocated to the screen
as opposed to 8K for a similar number of pixels (assuming 9-point font.) It also means at least
8x faster updates,

For authentic Macintosh fonts, see https://archive.org/details/AppleMacintoshSystem753
"""

from nand import chip, lazy, RAM, ROM, Input, Output, DFF
import nand.syntax
from nand.vector import unsigned
from project_01 import And, Or, Not
from project_03 import Mux, Mux16, Register, PC, ALU
from nand.solutions import solved_06
from alt.threaded import Eq16

SCREEN_BASE   = 0x0400
KEYBOARD_ADDR = 0x07FF
ROM_BASE      = 0x0800
HEAP_BASE     = 0x8000


#
# Components:
#

@chip
def FlatMemory(inputs, outputs):
    """The same interface as MemorySystem, but also maps the ROM and extends address to the full 16 bits.

    FIXME: this will need some additional support in the "codegen" simulator, which otherwise implements
    the standard MemorySystem directly. But that support will be useful to any Computer with different
    memory layout.
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
    tty = Output(in_=in_, load=And(a=load, b=is_io).out)

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
    pc = PC(in_=a_reg.out, load=And(a=not_idle, b=jump).out, inc=not_idle, reset=reset)
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

    addr = Mux16(a=cpu.pc, b=cpu.addressM, sel=execute).out

    mem = FlatMemory(in_=cpu.outM,
                     load=And(a=execute, b=cpu.writeM).out,
                     address=addr)

    instr_reg = Register(in_=mem.out, load=fetch)

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

    # # TEMP:
    # outputs.fetch = fetch
    # # outputs.execute = execute
    # outputs.addr = addr
    # # outputs.addressM = cpu.addressM
    # outputs.writeM = cpu.writeM
    # outputs.outM = cpu.outM
    # outputs.instr = instr_reg.out


#
# Assembler:
#

import re


BUILTIN_SYMBOLS = {
    **{
        "SCREEN": SCREEN_BASE,
        "KEYBOARD": KEYBOARD_ADDR,
        "ROM": ROM_BASE,
        "HEAP": HEAP_BASE,
    },
    **solved_06.register_names(16)
}


def parse_op(string, symbols={}):
    """Handle 16-bit constants (e.g. #-10 or #0xFF00); used for data to be read from ROM.
    """
    m = re.match(r"#(-?((0x[0-9a-fA-F]+)|([1-9][0-9]*)|0))", string)
    if m:
        value = eval(m.group(1))
        if value < -32768 or value > 65535:
            raise Exception(f"Constant value out of range: {value} ({string})")
        return unsigned(value)
    else:
        return solved_06.parse_op(string, symbols)


def assemble(f, min_static=16, max_static=1023):
    """Standard assembler, except: shift the ROM base address, symbols for other base addresses, and 16-bit data."""
    return solved_06.assemble(f,
                              parse_op=parse_op,
                              min_static=min_static,
                              max_static=max_static,
                              start_addr=ROM_BASE,
                              builtins=BUILTIN_SYMBOLS)


#
# Harness:
#

import computer
import pygame.image
import time


def run(chip, program, name="Flat!", font="monaco-9", halt_addr=None):
    """Run with keyboard and text-mode graphics."""

    # TODO: font

    # A little sanity checking:
    if len(program) > HEAP_BASE:
        raise Exception(f"Program too large for ROM: {(len(program) - ROM_BASE)/1024:0.1f}K > {(HEAP_BASE - ROM_BASE)//1024}K")
    elif any(b != 0 for b in program[:ROM_BASE]):
        print("WARNING: non-zero words found in the program image below ROM_BASE; this memory is hidden by low RAM")

    computer = nand.syntax.run(chip, simulator="vector")

    computer.init_rom(program)

    # Jump over low memory that we might be using for debugging:
    computer.poke(0, ROM_BASE)
    computer.poke(1, parse_op("0;JMP"))

    kvm = TextKVM(name, 80, 25, 6, 10, "alt/big/Monaco9.png")

    # TODO: use computer.py's "run", for many more features
    cycles = 0
    halted = False
    while True:
        if not halted and computer.pc == halt_addr:
            halted = True
            print(f"halted after {cycles} cycles")

        if not halted:
            # print(f"@{computer.pc}; outputs: {computer.outputs()}")
            # print(f"  R0: {computer.peek(0)}; R1: {computer.peek(1)}")

            # computer.ticktock(100)
            # cycles += 100
            computer.ticktock()
            cycles += 1
        else:
            time.sleep(0.1)


        if cycles % 100 == 0 or halted:
            key = kvm.process_events()
            computer.set_keydown(key or 0)

            tty_char = computer.get_tty()
            if tty_char:
                print(chr(tty_char), end="", flush=True)

            kvm.update_display(lambda x: computer.peek(SCREEN_BASE + x))

            msgs = [
                f"{cycles/1000:0.1f}k cycles",
                f"@{computer.pc}",
            ]
            pygame.display.set_caption(f"{name}: {'; '.join(msgs)}")


class TextKVM(computer.KVM):
    """Keyboard and display, displaying characters using a set of baked-in glyphs.

    Each word of the screen buffer stores a pair of 8-bit characters.
    """

    def __init__(self, title, char_width, char_height, glyph_width, glyph_height, bitmap_path):
        computer.KVM.__init__(self, title, char_width*glyph_width, char_height*glyph_height)

        self.char_width = char_width
        self.char_height = char_height
        self.glyph_width = glyph_width
        self.glyph_height = glyph_height

        self.glyph_sheet = pygame.image.load(bitmap_path)


    def update_display(self, get_chars):
        self.screen.fill(computer.COLORS[0])

        stride = self.char_width//2
        for y in range(0, self.char_height):
            for x in range(0, self.char_width, 2):
                pair = get_chars(y*stride + x//2)
                self.render(  x, y, pair & 0xFF)
                self.render(x+1, y, pair >> 8)

        pygame.display.flip()


    def render(self, x, y, c):
        g_x = (c & 0x0F)*self.glyph_width
        g_y = (c >> 4)*self.glyph_height
        self.screen.blit(self.glyph_sheet,
                         dest=(x*self.glyph_width,
                               y*self.glyph_height),
                         area=pygame.Rect(g_x,
                                          g_y,
                                          self.glyph_width,
                                          self.glyph_height))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run assembly source with text-mode display and keyboard")
    parser.add_argument("path", help="Path to source (<file>.asm)")
    # parser.add_argument("--simulator", action="store", default="codegen", help="One of 'vector' (slower, more precise); 'codegen' (faster, default); 'compiled' (experimental)")
    # parser.add_argument("--trace", action="store_true", help="(VM/Jack-only) print cycle counts during initialization. Note: runs almost 3x slower.")
    # parser.add_argument("--print", action="store_true", help="(VM/Jack-only) print translated assembly.")
    # TODO: "--debug" showing opcode-level trace. Breakpoints, stepping, peek/poke?
    # parser.add_argument("--no-waiting", action="store_true", help="(VM/Jack-only) substitute a no-op function for Sys.wait.")
    # parser.add_argument("--max-fps", action="store", type=int, help="Experimental! (VM/Jack-only) pin the game loop to a fixed rate, approximately (in games that use Sys.wait).\nMay or may not work, depending on the translator.")
    # TODO: "--max-cps"; limit the clock speed directly. That will allow different chips to be compared (in a way).
    # TODO: "--headless" with no UI, with Keyboard and TTY connected to stdin/stdout

    args = parser.parse_args()

    print(f"Reading assembly from file: {args.path}")
    with open(args.path, mode='r') as f:
        prg, symbols, statics = assemble(f)

    prg_size = len(prg) - ROM_BASE
    max_size = HEAP_BASE - ROM_BASE
    print(f"Size in ROM: {prg_size:0,d} ({100*prg_size/max_size:0.1f}% of {max_size//1024}K)")
    print(f"symbols: {symbols}")
    print(f"statics: {statics}")

    run(chip=BigComputer, program=prg, halt_addr=symbols["halt"])


if __name__ == "__main__":
    main()
