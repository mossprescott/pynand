#! /usr/bin/env python3

"""Run the full computer with display and keyboard connected via pygame.

The program to run must be in the form of Hack assembly (.asm) or VM opcodes (a directory
of .vm files) and is specified by sys.argv[1].
The `codegen` simulator is used unless --simulator is specified.

$ ./computer.py examples/Blink.asm

Note: if nothing is displayed on Mac OS X Mojave, install updated pygame with a fix:
$ pip3 install pygame==2.0.0dev6

To install pygame on M1 Mac (Big Sur), this may help:
https://www.quora.com/How-do-you-install-Pygame-on-a-MacBook-M1?share=1
"""

import argparse
import os
import pygame
from pygame import Surface, Color, PixelArray
import re
import sys
import time

import nand.component
import nand.syntax
from nand.translate import override_sys_wait, translate_dir, translate_library
from nand.platform import USER_PLATFORM

EVENT_INTERVAL = 1/10
DISPLAY_INTERVAL = 1/20  # Note: screen update is pretty slow at this point, so no point in trying for a higher frame rate.
CYCLE_INTERVAL = 1/1.0  # How often to update the cycle and frame counters; a bit longer so they doesn't bounce around too much

CYCLES_PER_CALL = 100  # Number of cycles to run in the tight loop (when not tracing)


parser = argparse.ArgumentParser(description="Run assembly or VM/Jack source with display and keyboard")
parser.add_argument("path", help="Path to source, either one file with assembly (<file>.asm) or a directory containing .vm or .jack files.")
parser.add_argument("--simulator", action="store", default="codegen", help="One of 'vector' (slower, more precise); 'codegen' (faster, default); 'compiled' (experimental)")
parser.add_argument("--trace", action="store_true", help="(VM/Jack-only) print cycle counts during initialization. Note: runs almost 3x slower.")
parser.add_argument("--print", action="store_true", help="(VM/Jack-only) print translated assembly.")
# TODO: "--debug" showing opcode-level trace. Breakpoints, stepping, peek/poke?
parser.add_argument("--no-waiting", action="store_true", help="(VM/Jack-only) substitute a no-op function for Sys.wait.")
parser.add_argument("--max-fps", action="store", type=int, help="Experimental! (VM/Jack-only) pin the game loop to a fixed rate, approximately (in games that use Sys.wait).\nMay or may not work, depending on the translator.")
# TODO: "--max-cps"; limit the clock speed directly. That will allow different chips to be compared (in a way).
# TODO: "--headless" with no UI, with Keyboard and TTY connected to stdin/stdout

def main(platform=USER_PLATFORM):
    args = parser.parse_args()

    print(f"\nRunning {args.path} on {platform.chip.constr().label}\n")

    prg, src_map, wait_addresses, halt_addresses = load(platform, args.path, print_asm=args.print, no_waiting=args.no_waiting)

    print(f"Size in ROM: {len(prg):0,d}")

    run(prg,
        chip=platform.chip,
        name=args.path,
        simulator=args.simulator,
        src_map=src_map if args.trace else None,
        is_in_wait=in_function_pred(None if args.no_waiting else wait_addresses),
        max_fps=args.max_fps,
        is_in_halt=in_function_pred(halt_addresses))


def load(platform, path, print_asm=False, no_waiting=False):
    if os.path.splitext(path)[1] == '.asm':
        # The path is expected to be a single file containing the entire contents of ROM:
        print(f"Reading assembly from file: {path}")
        with open(path, mode='r') as f:
            prg, _, _ = platform.assemble(f)
        return prg, None, None, None
    else:
        # The path may be a file or directory containing VM or Jack source.
        # TODO: handle combinations of the above, with or without included "OS" classes.

        translator = platform.translator()
        translator.preamble()
        translate_dir(translator, platform, path, print_asm)

        translate_library(translator, platform)

        translator.finish()

        try:
            translator.check_references()
        except Exception as x:
            print(f"Warning: reference consistency check failed: {x}")

        if no_waiting:
            # Tricky: the assembler will favor the latest occurrence of any label, so simply
            # redefining a function at the end effectively overrides the previous definition
            # (which is still taking up space in the ROM.)
            override_sys_wait(translator, platform)

        if print_asm:
            for instr in translator.asm:
                print(instr)
            print()

        wait_addresses = translator.asm.find_function("Sys", "wait")
        halt_addresses = translator.asm.find_function("Sys", "halt")

        # TODO: when --max-fps is enabled, inject a raw assembly version of Sys.wait that
        # definitely runs long enough to be detected in the run loop. Is that feasible,
        # given possible variation in VM/CPU details?

        # These are just the defaults for now, but maybe they could be overridable?
        min_static = 16
        max_static = 255
        instrs, symbols, statics = platform.assemble(translator.asm, min_static=min_static, max_static=max_static)

        if print_asm:
            print(f"Statics ({len(statics)} of {max_static - min_static + 1}):")
            for name, addr in sorted(statics.items()):
                print(f"  {name}: {addr}")
            print()

        return instrs, translator.asm.src_map, wait_addresses, halt_addresses


COLORS = [0xFFFFFF, 0x000000]
"""0: White, 1: Black, as it was meant to be."""


KEY_MAP = dict([
    (pygame.K_RETURN, 128),
    (pygame.K_BACKSPACE, 129),
    (pygame.K_LEFT, 130),
    (pygame.K_UP, 131),
    (pygame.K_RIGHT, 132),
    (pygame.K_DOWN, 133),
    (pygame.K_HOME, 134),
    (pygame.K_END, 135),
    (pygame.K_PAGEUP, 136),
    (pygame.K_PAGEDOWN, 137),
    (pygame.K_INSERT, 138),
    (pygame.K_DELETE, 139),
    (pygame.K_ESCAPE, 140),
    (pygame.K_F1, 141),
    (pygame.K_F2, 142),
    (pygame.K_F3, 143),
    (pygame.K_F4, 144),
    (pygame.K_F5, 145),
    (pygame.K_F6, 146),
    (pygame.K_F7, 147),
    (pygame.K_F8, 148),
    (pygame.K_F9, 149),
    (pygame.K_F10, 150),
    (pygame.K_F11, 151),
    (pygame.K_F12, 152),
] +
[ (c, c) for c in range(32, 127) ])   # Printable characters, plus a few odd-balls

SHIFTED_KEY_MAP = {
    **KEY_MAP,
    **dict((ord(x), ord(y)) for x, y in
           zip("abcdefghijklmnopqrstuvwxyz`1234567890-=[]\\;',./",
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ~!@#$%^&*()_+{}|:\"<>?"))
}
"""Map from raw key code to the code produced when (any) shift modifier is down.
Note: this is definitely not correct if your keyboard layout isn't a typical US layout.
Not sure
"""

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
        typed_keys = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.unicode != "" and ord(event.unicode) in KEY_MAP:
                    typed_keys.append(KEY_MAP[ord(event.unicode)])

        # If any keydown event occurred since the last time we checked, the first such key is
        # recorded as down for the CPU. That gives the program a chance to detect keystrokes
        # that are too fast to actually be seen, but more importantly it also catches keystrokes
        # that pygame doesn't otherwise pass along: keys that are pressed when a modifier is down.
        if typed_keys != []:
            # print(f"typed: {typed_keys}")
            return typed_keys[0]

        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        shifted = mods & pygame.KMOD_SHIFT or mods & pygame.KMOD_LSHIFT or mods & pygame.KMOD_RSHIFT
        for idx, key in (KEY_MAP if not shifted else SHIFTED_KEY_MAP).items():
            if keys[idx]:
                return key

        return None

    def update_display(self, get_pixel):
        self.screen.fill(COLORS[0])

        row_words = self.width//16
        for y in range(self.height):
            for w in range(row_words):
                word = get_pixel(y*row_words + w)
                if word != 0:
                    for i in range(16):
                        if word & 0b1:
                            x = w*16 + i
                            self.screen.set_at((x, y), COLORS[1])
                        word >>= 1

        pygame.display.flip()


def run(program, chip, name="Nand!", simulator="codegen", src_map=None, is_in_wait=(lambda _: False), max_fps=None, is_in_halt=(lambda _: False)):
    computer = nand.syntax.run(chip, simulator=simulator)
    computer.init_rom(program)

    kvm = KVM(name, 512, 256)

    last_cycle_time = last_event_time = last_display_time = last_frame_time = now = time.monotonic()
    was_in_sys_wait = False
    halted = False

    last_cycle_count = cycles = 0
    last_frame_count = frames = 0
    while True:
        if halted:
            # Stop burning (host) cpu simulating the halt loop, but keep processing events
            # so the UI stays up.
            time.sleep(EVENT_INTERVAL)

        elif not src_map:
            computer.ticktock(CYCLES_PER_CALL)
            cycles += CYCLES_PER_CALL

        else:
            computer.ticktock(); cycles += 1

            op = src_map.get(computer.pc) if src_map else None
            if op and op.startswith("call"):
                # if 'Main' in op or 'init' in op or "Sys.halt" in op:
                #     print(f"{cycles:10,d}; {op}     @{computer.pc}")
                m = re.match(r'call (.*)\.(.*) (\d)', op)
                if m:
                    class_name = m.group(1)
                    sub_name = m.group(2)
                    tracable = False
                    if class_name == 'Main': tracable = True
                    elif sub_name == 'init': tracable = True
                    elif class_name == "Sys" and sub_name == "halt": tracable = True
                    elif class_name not in ("Keyboard", "Math", "Memory", "Array", "String", "Screen"): tracable = True
                    # tracable = True
                    if tracable:
                        print(f"{cycles:10,d}; {class_name}.{sub_name}     @{computer.pc}")
            # if op:
            #     print(f"{computer.pc:5d}: {op}; cycle: {cycles:0,d}")

        # Note: check the time only every few frames to reduce the overhead of timing
        if cycles % CYCLES_PER_CALL == 0:
            now = time.monotonic()

            # Detect when the program is complete:
            if not halted and is_in_halt(computer.pc):
                print(f"Halted after {cycles:,d} cycles (@{computer.pc})")
                halted = True

            # Detect the end of the game loop:
            in_sys_wait = is_in_wait(computer.pc)

            # BUG: this isn't reliable; it works only if the program doesn't jump to any
            # instructions outside the boundaries of the Sys.wait function body itself.
            # But a lot of translators are going to do that, even if it's written as a flat
            # loop at the Jack level. To make this work, probably going to have to inject a
            # raw assembly version of Sys.wait that has predictable behavior.
            if max_fps is not None and in_sys_wait and not was_in_sys_wait:
                frames += 1

                actual_delay = now - last_frame_time
                last_frame_time = now
                target_delay = 1.0/max_fps
                remaining_delay = target_delay - actual_delay
                if remaining_delay > 0:
                    # print(f"frame delay: {remaining_delay:.3f} ({100*remaining_delay/target_delay:.1f}%)")
                    time.sleep(remaining_delay)

            # A few times per second, process events and update the display:
            if now >= last_event_time + EVENT_INTERVAL:
                last_event_time = now
                key = kvm.process_events()
                computer.set_keydown(key or 0)

            # Update the display a little sooner if we're in Sys.wait at the moment. The effect
            # is to update after drawing is complete for a frame, more often than not, which reduces
            # tearing. But we always maintain a minimum refresh rate, so you can see what the
            # program is doing. Makes the most noticable difference when the FPS limit is high and the
            # CPU is slow (not "compiled".)
            if in_sys_wait:
                display_interval = DISPLAY_INTERVAL/2
            else:
                display_interval = DISPLAY_INTERVAL
            if now >= last_display_time + display_interval:
                last_display_time = now
                kvm.update_display(computer.peek_screen)

            if not halted and now >= last_cycle_time + CYCLE_INTERVAL:
                msgs = []

                msgs.append(f"{cycles//1000:0,d}k cycles")

                cps = (cycles - last_cycle_count)/(now - last_cycle_time)
                msgs.append(f"{cps/1000:0,.1f}k/s")

                if frames > 0:
                    fps = (frames - last_frame_count)/(now - last_cycle_time)
                    msgs.append(f"{fps:0.0f}fps")

                # This is sometimes helpful to show when your program jumps to some random address,
                # or runs off the end of the ROM.
                msgs.append(f"@{computer.pc}")

                pygame.display.set_caption(f"{name}: {'; '.join(msgs)}")

                last_cycle_time = now
                last_cycle_count = cycles
                last_frame_count = frames

            # Note: you might want to check the frame delay and sleep *here*, after updating the
            # display, so that the limit logic could account for the time is takes to process
            # events and update the display. But somehow when it happens in that sequence, the
            # loop gets very unresponsive and the FPS limit is effectively useless. Something
            # in pygame doesn't like that sequence, somehow?

            was_in_sys_wait = in_sys_wait


def in_function_pred(function_addresses):
    """Construct a function that checks to see if the current address (i.e. the PC) is within
    a certain region (i.e. a particular function). See translate.find_function().
    """

    if function_addresses is None:
        return lambda _: False

    start = function_addresses[0]
    last_return = function_addresses[1][-1]
    def pred(addr):
        return start <= addr <= last_return
    return pred


if __name__ == "__main__":
    main()
