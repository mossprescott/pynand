#! /usr/bin/env python

"""Run the full computer with display and keyboard connected via pygame.

The program to run must be in Hack assembly form (.asm), and is specified by sys.argv[1].
The `codegen` simulator is used unless env var `PYNAND_SIMULATOR` is set to "vector":

$ python computer.py examples/Blink.asm

Note: if nothing is displayed on Mac OS X Mojave, install updated pygame with a fix: 
$ pip3 install pygame==2.0.0dev6
"""

import os
import pygame
from pygame import Surface, Color, PixelArray
import sys
import time

import nand.component
import nand.syntax
import project_05
import project_06


EVENT_INTERVAL = 1/10
DISPLAY_INTERVAL = 1/10  # Note: screen update is pretty slow at this point, so no point in trying for a higher frame rate.
CYCLE_INTERVAL = 1.0


def main():
    with open(sys.argv[1], mode='r') as f:
        prg = project_06.assemble(f)
    run(prg)


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


def run(program, src_map=None):
    computer = nand.syntax.run(project_05.Computer, simulator=os.environ.get("PYNAND_SIMULATOR") or 'codegen')
    computer.init_rom(program)
    
    kvm = KVM(sys.argv[1], 512, 256)

    last_cycle_time = last_event_time = last_display_time = now = time.monotonic()
    
    last_cycle_count = cycles = 0
    while True:
        computer.ticktock(); cycles += 1

        op = src_map.get(computer.pc) if src_map else None
        if op and op.startswith("call") and (
            'Screen' in op or 'Main' in op or 'init' in op):
            print(f"{computer.pc}: {op}; cycle: {cycles:0,d}")
        
        # Note: check the time only every few frames to reduce the overhead of timing
        if cycles % 10 == 0:
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
                pygame.display.set_caption(f"{sys.argv[1]}: {cycles//1000:0,d}k cycles; {cps/1000:0,.1f}k/s; PC: {computer.pc}")
                last_cycle_time = now
                last_cycle_count = cycles
            
                # print(f"cycles: {cycles//1000:0,d}k; pc: {computer.pc}")
                # print(f"mem@00:   {', '.join(hex(computer.peek(i))[2:].rjust(4, '0') for i in range(16))}")
                # print(f"mem@16:   {', '.join(hex(computer.peek(i+16))[2:].rjust(4, '0') for i in range(16))}")


if __name__ == "__main__":
    main()