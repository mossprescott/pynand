#! /usr/bin/env python3

"""Run the full computer with display and keyboard connected via pygame.

The program to run must be in the form of Hack assembly (.asm) or VM opcodes (a directory 
of .vm files) and is specified by sys.argv[1].
The `codegen` simulator is used unless --vector is used.

$ ./computer.py examples/Blink.asm

Note: if nothing is displayed on Mac OS X Mojave, install updated pygame with a fix: 
$ pip3 install pygame==2.0.0dev6
"""

import argparse
import collections
import os
import pygame
from pygame import Surface, Color, PixelArray
import sys
import time

import nand.component
import nand.syntax
from nand.translate import translate_dir
from nand.solutions import solved_05, solved_06, solved_07
import project_05, project_06, project_07, project_08

EVENT_INTERVAL = 1/10
DISPLAY_INTERVAL = 1/10  # Note: screen update is pretty slow at this point, so no point in trying for a higher frame rate.
CYCLE_INTERVAL = 1/1.0  # How often to update the cycle counter; a bit longer so it doesn't bounce around too much

CYCLES_PER_CALL = 100  # Number of cycles to run in the tight loop (when not tracing)


parser = argparse.ArgumentParser(description="Run assembly or VM source with display and keyboard")
parser.add_argument("path", help="Path to source, either one file with assembly (<file>.asm) or a directory containing .vm files.")
parser.add_argument("--vector", action="store_true", help="Use the slower, but more precise, bit-vector-based runtime.")
parser.add_argument("--trace", action="store_true", help="(VM-only) print cycle counts during initialization. Note: runs almost 3x slower.")
parser.add_argument("--print", action="store_true", help="(VM-only) print translated assembly.")
parser.add_argument("--no-waiting", action="store_true", help="(VM-only) substitute a no-op function for Sys.wait.")


Platform = collections.namedtuple("Platform", ["chip", "assemble", "parse_line", "translator"])
"""Package of a chip and the assembler and translator needed to run VM programs on it."""


HACK_PLATFORM = Platform(
    chip=project_05.Computer,
    assemble=project_06.assemble,
    parse_line=project_07.parse_line,
    translator=project_08.Translator)
"""The default chip and associated tools, defined in the project_0x.py modules."""


STANDARD_PLATFORM = Platform(
    chip=solved_05.Computer,
    assemble=solved_06.assemble,
    parse_line=solved_07.parse_line,
    translator=solved_07.Translator)
"""The included chip and tools; for comparison with the current solution."""

def main(platform=HACK_PLATFORM):
    args = parser.parse_args()
    
    print(f"\nRunning {args.path} on {platform.chip.constr().label}\n")

    prg, src_map = load(platform, args.path, print_asm=args.print, no_waiting=args.no_waiting)
    
    print(f"Size in ROM: {len(prg):0,d}")

    run(prg,
        chip=platform.chip,
        name=args.path,
        simulator='vector' if args.vector else 'codegen',
        src_map=src_map if args.trace else None)


def load(platform, path, print_asm=False, no_waiting=False):
    if os.path.splitext(path)[1] == '.asm':
        print(f"Reading assembly from file: {path}")
        with open(path, mode='r') as f:
            prg = platform.assemble(f)
        return prg, None
    else:
        translate = platform.translator()
        translate.preamble()
        translate_dir(translate, platform.parse_line, path)
        translate_dir(translate, platform.parse_line, "nand2tetris/tools/OS")  # HACK not committed

        if no_waiting:
            translate.function("Sys", "wait", 0)
            translate.push_constant(0)
            translate.return_op()

        if print_asm:
            for instr in translate.asm:
                print(instr)

        return platform.assemble(translate.asm), translate.asm.src_map


COLORS = [0xFFFFFF, 0x000000]
"""0: White, 1: Black, as it was meant to be."""

# "Recognizes all ASCII characters, as well as the following keys: 
# newline (128=String.newline()), backspace (129=String.backspace()), 
# left arrow (130), up arrow (131), right arrow (132), down arrow (133), 
# home (134), end (135), page up (136), page down (137), 
# insert (138), delete (139), ESC (140), F1-F12 (141-152)."
LEFT_ARROW = 130
UP_ARROW = 131
RIGHT_ARROW = 132
DOWN_ARROW = 133
ESCAPE = 140
NEWLINE = 128


class KVM:
    def __init__(self, title, width, height):
        self.width = width
        self.height = height

        pygame.init()
        
        flags = 0
        # flags = pygame.FULLSCREEN
        # pygame.SCALED requires 2.0.0
        flags |= pygame.SCALED
        self.screen = pygame.display.set_mode((width, height), flags=flags)
        pygame.display.set_caption(title)
        
    def process_events(self):
        """Drain pygame's event loop, returning the pressed key, if any.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
        keys = pygame.key.get_pressed()
        
        # print(f"key codes: {codes}")
        # print(f"mods: {hex(pygame.key.get_mods())}")
        if keys[pygame.K_UP]:
            key = UP_ARROW
        elif keys[pygame.K_LEFT]:
            key = LEFT_ARROW
        elif keys[pygame.K_DOWN]:
            key = DOWN_ARROW
        elif keys[pygame.K_RIGHT]:
            key = RIGHT_ARROW
        elif keys[pygame.K_ESCAPE]:
            key = ESCAPE
        elif keys[pygame.K_SPACE]:
            key = ord(' ')
        elif keys[pygame.K_RETURN]:
            key = NEWLINE
        else:
            for c in range(ord('a'), ord('z')+1):
                if keys[c]:
                    key = c
                    break
            else:
                key = None
        return key

    def update_display(self, get_pixel):
        self.screen.fill(COLORS[0])

        row_words = self.width//16
        for y in range(self.height):
            for w in range(row_words):
                word = get_pixel(y*row_words + w)
                for i in range(16):
                    if word & 0b1:
                        x = w*16 + i
                        self.screen.set_at((x, y), COLORS[1])
                    word >>= 1

        pygame.display.flip()


def run(program, chip, name="Nand!", simulator='codegen', src_map=None):
    computer = nand.syntax.run(chip, simulator=simulator)
    computer.init_rom(program)
    
    kvm = KVM(name, 512, 256)

    last_cycle_time = last_event_time = last_display_time = now = time.monotonic()
    
    last_cycle_count = cycles = 0
    while True:
        if not src_map:
            computer.ticktock(CYCLES_PER_CALL)
            cycles += CYCLES_PER_CALL
            
        else:
            computer.ticktock(); cycles += 1

            op = src_map.get(computer.pc) if src_map else None
            if op and op.startswith("call") and (
                'Main' in op or 'init' in op):
                print(f"{computer.pc}: {op}; cycle: {cycles:0,d}")
        
        # Note: check the time only every few frames to reduce the overhead of timing
        if cycles % CYCLES_PER_CALL == 0:
            now = time.monotonic()
        
            # A few times per second, process events and update the display:
            if now >= last_event_time + EVENT_INTERVAL:
                last_event_time = now
                key = kvm.process_events()
                computer.set_keydown(key or 0)

            if now >= last_display_time + DISPLAY_INTERVAL:
                last_display_time = now
                kvm.update_display(computer.peek_screen)

            if now >= last_cycle_time + CYCLE_INTERVAL:
                cps = (cycles - last_cycle_count)/(now - last_cycle_time)
                pygame.display.set_caption(f"{name}: {cycles//1000:0,d}k cycles; {cps/1000:0,.1f}k/s; PC: {computer.pc}")
                last_cycle_time = now
                last_cycle_count = cycles
            
                # print(f"cycles: {cycles//1000:0,d}k; pc: {computer.pc}")
                # print(f"mem@00:   {', '.join(hex(computer.peek(i))[2:].rjust(4, '0') for i in range(16))}")
                # print(f"mem@16:   {', '.join(hex(computer.peek(i+16))[2:].rjust(4, '0') for i in range(16))}")


if __name__ == "__main__":
    main()