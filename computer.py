# Note: install updated pygame with Mojave fix: 
# pip3 install pygame==2.0.0dev6

import sys
import pygame
from pygame import Surface, Color, PixelArray

import nand.component
from nand.syntax import run
import project_05
import project_06
import test_05


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
        
        # offscreen = Surface(size, depth=1)
        # pixels = offscreen.get_buffer()
        # pixels.write(1, 0)  # ???
        # offscreen.blit(screen)

    def process_events(self):
        """Drain pygame's event loop, returning the pressed key, if any.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: sys.exit()  # HACK
        
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

    def update_display(self, pixels):
        self.screen.fill(COLORS[0])

        row_words = self.width//16
        for y in range(self.height):
            for w in range(row_words):
                word = pixels[y*row_words + w]
                if y == 1 and w == 0:
                    print(f"word: {hex(word)}")
                for i in range(16):
                    if word & 0b1:
                        x = w*16 + i
                        print(f"set pixel: {(x, y)}")
                        self.screen.set_at((x, y), COLORS[1])
                    word >>= 1

        pygame.display.flip()


def main():
    with open(sys.argv[1]) as f:
        prg = project_06.load_file(f)

    computer = run(project_05.Computer)
    test_05.init_rom(computer, prg)
    
    main_mem = test_05.get_ram(computer, address_bits=14)
    screen_mem = test_05.get_ram(computer, address_bits=13)
    keyboard, = computer.components(nand.component.Input)

    kvm = KVM(sys.argv[1], 512, 256)

    cycles = 0
    while True:
        computer.tick(); computer.tock(); cycles += 1

        # A few times per second, process events and update the display:
        if cycles % 200 == 0:
            key = kvm.process_events()
            keyboard.set(key or 0)

        if cycles % 100 == 0:
            kvm.update_display(screen_mem.storage)

        if cycles % 5000 == 0:
            print(f"cycles: {cycles}; pc: {computer.pc}")
            print(f"mem@00:   {', '.join(hex(main_mem.storage[i])[2:].rjust(4, '0') for i in range(16))}")
            print(f"mem@16:   {', '.join(hex(main_mem.storage[i+16])[2:].rjust(4, '0') for i in range(16))}")


if __name__ == "__main__":
    main()