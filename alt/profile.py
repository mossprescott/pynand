#! /usr/bin/env python3

"""VM-level profiler, tracking the number of cycles by: instruction, opcode, function.

This immediately revealed that Math.divide is a huge problem, and in particular dividing by 16. So
I added the shift.py implementation which eliminates those calls, for the biggest improvement yet.

Second discovery: 67% of the time (post-initialization) was in Sys.wait(). That was easy to hack
around.

Now:
40% of the time (initialization) is in Memory.alloc(), which is unexpected.
20% is still in Math.multiply, even after making it a bit quicker with "shiftr".
2% is Math.abs, but despite the small number I wonder how much it would help to inline it since it
would be quite simple to translate directly to assembly.

"call" and "return" ops only account for about 5% each. A lot less than expected.
"lt" and "push local" are higher: around 13%. "lt" could be improved a lot in the translator by
fusing it with "not/if-goto".
"""

import collections
import sys

import nand.syntax, nand.translate, nand.platform


# TODO: make some or all of this stuff command-line params

MAX_CYCLES = 15_000_000

CALL_SITES = False
"""If True, time is charged to each particular call, otherwise, all calls to the same function are
 aggregated."""

# TODO:
# CALL_TREES = True
# """If True, aggregate time in functions according to the call chain."""

# SIMULATOR = "codegen"
SIMULATOR = "compiled"  # only about 30% faster, interestingly

NO_WAITING = True

def main():
    path = sys.argv[1] if len(sys.argv) == 2 else "examples/project_11/Pong"

    if False:
        platform = nand.platform.BUNDLED_PLATFORM
    elif False:
        import alt.threaded
        platform = alt.threaded.THREADED_PLATFORM
    elif False:
        import alt.lazy
        platform = alt.lazy.LAZY_PLATFORM
    elif False:
        import alt.shift
        platform = alt.shift.SHIFT_PLATFORM
    elif True:
        import alt.reg
        platform = alt.reg.REG_PLATFORM


    translate = platform.translator()

    translate.preamble()
    nand.translate.translate_dir(translate, platform, path)
    nand.translate.translate_library(translate, platform)

    # Substitute implementation for Sys.wait(), which returns immediately. This takes precedence
    # just because it appears later in the assembly stream, so its address will appear in the symbol map.
    # TODO: make this some kind of system trap, along with Sys.halt and Sys.error, that signals the
    # simulator to sleep for a bit, maybe.
    if NO_WAITING:
        nand.translate.override_sys_wait(translate, platform)

    translate.finish()

    # for l in translate.asm:
    #     print(l)

    prg, _, _ = platform.assemble(translate.asm)
    src_map = translate.asm.src_map
    # print(list(src_map.items())[:10])

    computer = nand.syntax.run(platform.chip, simulator=SIMULATOR)
    computer.init_rom(prg)


    # raw_instructions = collections.Counter()  # by ROM address
    instructions = collections.Counter()  # by ROM address, binned according to src_map
    opcodes = collections.Counter()  # by opcode (not including args)
    fns = collections.Counter()  # by ROM address of the "function" op
    fn_instructions = collections.Counter()  # by ROM address of the "function" op

    current_instr = None
    current_opcode = None
    fn_stack = [0]
    fns[0] = 1

    fn_prefix = "call " if CALL_SITES else "function "

    # Counts the number of Sys.wait() calls. If greater than zero, we are in the game loop
    current_frame = 0

    recorded_cycles = 0

    was_recording = False

    for cycle in range(MAX_CYCLES):
        # recording = current_frame > 0  # Uncomment to skip initialization
        recording = True               # Uncomment to profile from the start

        if recording and not was_recording:
            print(f"\nStart recording at cycle {cycle:,d}")
            was_recording = True

        if cycle % 5000 == 0:
            print(".", end="", flush=True)

        pc = computer.pc
        # raw_instructions[pc] += 1

        op = src_map.get(pc)
        if op:
            current_instr = pc

            current_opcode = op.split()[0]  # TODO: smarter than this
            if current_opcode in ("push", "pop"):
                current_opcode = " ".join(op.split()[:2])

            if current_opcode == "function":
                fn = op.split()[1]
                if fn == "Sys.wait":
                    current_frame += 1
                    print("w", end="", flush=True)
                elif fn == "Sys.halt":
                    print(f"\nHalted")
                    break

            # Note: functions with no locals don't actually need to generate any instructions for
            # the "function" opcode, but if they didn't, their first opcode would overwrite the
            # "function" opcode in the source map, since it has the same instruction address.
            # HACK: for now, generating a no-op instruction for these function opcodes works around
            # this issue (while making the program just slightly slower.)
            # Need to make src_map a multi-map.
            if op.startswith(fn_prefix):
                fn_stack.append(pc)
                if recording:
                    fns[pc] += 1
            elif op.startswith("return") and len(fn_stack) > 1:
                # TODO: wait to pop _after_ this op, so the return is charged to the function (not the caller)
                fn_stack.pop()

        if recording:
            if current_instr:
                instructions[current_instr] += 1

            if current_opcode:
                opcodes[current_opcode] += 1

            fn_instructions[fn_stack[-1]] += 1

            recorded_cycles += 1

        computer.ticktock()

    print()
    print(f"Ran {cycle:,d} cycles; recorded: {recorded_cycles:,d}; frames: {current_frame+1:,d}")
    print()

    # print(raw_instructions.most_common(50))

    print("Instructions (top 20):")
    for addr, count in instructions.most_common(20):
        print(f"  {100*count/recorded_cycles:0.2f}%: {src_map[addr]} @ {addr}")
    print()

    print("Opcodes:")
    for op, count in opcodes.most_common():
        print(f"  {100*count/recorded_cycles:0.2f}%: {op}")
    print()

    print("Functions (top 20):")
    for addr, count in fn_instructions.most_common(20):
        print(f"  {100*count/recorded_cycles:0.2f}%: {'start' if addr == 0 else src_map[addr]} @ {addr} ({fns[addr]} times)")


if __name__ == "__main__":
    main()
