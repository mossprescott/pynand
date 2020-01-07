# HACK: this is a copy of computer.py, modified to use the codegen simulator.
# TODO: put a common interface around both simulated computers, and make the choice of simulation
# an option to this script.

# Note: install updated pygame with Mojave fix: 
# pip3 install pygame==2.0.0dev6

import sys
import pygame
from pygame import Surface, Color, PixelArray

import nand.component
from nand.syntax import run
import project_05
import project_06
# import test_05
from nand import test_codegen
from nand.codegen import translate

COLORS = [0xFFFFFF, 0x000000]
"""0: White, 1: Black, as it was meant to be."""


# "Recognizes all ASCII characters, as well as the following keys: newline (128=String.newline()), backspace (129=String.backspace()), left arrow (130), up arrow (131), right arrow (132), down arrow (133), home (134), end (135), page up (136), page down (137), insert (138), delete (139), ESC (140), F1-F12 (141-152)."
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
        
        # TODO: map K_... to ASCII plus control codes
        # codes = [i for i in range(256) if keys[i]]
        # print(f"key codes: {codes}")
        # print(f"mods: {hex(pygame.key.get_mods())}")
        # HACK: arrow keys not coming through from pygame, so just map WASD for now:
        if keys[pygame.K_a]:
            return LEFT_ARROW
        elif keys[pygame.K_d]:
            return RIGHT_ARROW
        elif keys[pygame.K_ESCAPE]:
            return ESCAPE
        elif keys[pygame.K_SPACE]:
            return ord(' ')
        elif keys[pygame.K_RETURN]:
            return NEWLINE
        return None

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


CPS = 100_000

def main():
    with open(sys.argv[1]) as f:
        prg = project_06.load_file(f)

    computer = translate(project_05.Computer.constr())()
    computer.init_rom(prg)
    
    kvm = KVM(sys.argv[1], 512, 256)

    cycles = 0
    while True:
        computer.ticktock(); cycles += 1

        # A few times per second, process events and update the display:
        if cycles % (CPS//30) == 0:
            key = kvm.process_events()
            computer.set_keydown(key or 0)

        if cycles % (CPS//15) == 0:
            kvm.update_display(computer.peek_screen)

        if cycles % (CPS*5) == 0:
            print(f"cycles: {cycles/1000:0,.0f}k; pc: {computer.pc}")
            # print(f"mem@00:   {', '.join(hex(main_mem.storage[i])[2:].rjust(4, '0') for i in range(16))}")
            # print(f"mem@16:   {', '.join(hex(main_mem.storage[i+16])[2:].rjust(4, '0') for i in range(16))}")


if __name__ == "__main__":
    main()