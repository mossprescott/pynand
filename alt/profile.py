"""VM-level profiler, tracking the number of cycles by: instruction, opcode, function (self), function (total).

First discoveries:

40% of the time (initialization) is in Memory.alloc(), which is unexpected.
30% is in Math.multiply, which is more than I expected in this phase.

67% of the time (post-initialization) was in Sys.wait(). That was easy to hack around.

After fixing that:
38% is Math.divide().
27% is Math.multiply().
This is no great surprise and represents an opportunity. Doing 16-bit multiply/divide without even 
shift/mask is just hard, and the included implementation may not even be good. Probably time to try 
a new CPU with one or two shift instructions, and implement them both using that.

"call" and "return" ops only account for about 10% each. That's a lot, but less than I expected.
"push local" is the only one higher: more than 13%.
"""

import collections
import sys

import nand.syntax, nand.translate
import project_05, project_06, project_07, project_08


def main():
    path = sys.argv[1]

    chip = project_05.Computer
    assemble = project_06.assemble
    parse_line = project_07.parse_line
    translate = project_08.Translator()
    # import alt.lazy
    # translate = alt.lazy.Translator()
    
    
    # initialization:
    # SKIP_CYCLES = 0
    # CYCLES = 4_000_000

    # skip initialization:
    SKIP_CYCLES = 4_000_000
    CYCLES = 4_000_000
    
    
    translate.preamble()
    nand.translate.translate_dir(translate, parse_line, path)
    nand.translate.translate_dir(translate, parse_line, "nand2tetris/tools/OS")  # HACK not committed
    
    # Substitute implementation for Sys.wait(), which returns immediately. This take precedence
    # just because it appears later in the assembly stream, so it's address will appear in the symbol map.
    # TODO: make this some kind of system trap, along with Sys.halt and Sys.error, that signals the 
    # simulator to sleep for a bit, maybe.
    translate.function("Sys", "wait", 0)
    translate.push_constant(0)
    translate.return_op()
    
    # for l in translate.asm:
    #     print(l)

    prg = assemble(translate.asm)
    src_map = translate.asm.src_map
    # print(list(src_map.items())[:10])
    
    computer = nand.syntax.run(chip, simulator="codegen")
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
    
    print(f"Skipping {SKIP_CYCLES:,d} cycles")
    # computer.ticktock(SKIP_CYCLES)

    for cycle in range(SKIP_CYCLES + CYCLES):
        if cycle % 1000 == 0:
            if cycle >= SKIP_CYCLES and (cycle - 1000) < SKIP_CYCLES:
                print()
                print(f"Running {CYCLES:,d} cycles")
            print(".", end="", flush=True)

        pc = computer.pc
        # raw_instructions[pc] += 1
        
        op = src_map.get(pc)
        if op:
            current_instr = pc

            current_opcode = op.split()[0]  # TODO: smarter than this
            if current_opcode in ("push", "pop"):
                current_opcode = " ".join(op.split()[:2])

            # Note: can't use "function" because functions with no locals don't generate any 
            # instructions for the "function" opcode (that is, their first opcode overwrites the 
            # "function" opcode in the source map, since it has the same instruction address.)
            # But this is not what you want most of the time because it's counting _call sites_.
            # HACK: for now, generating a no-op instruction for these function opcodes works around 
            # this issue (while making the program just slightly slower.)
            # Need to make src_map a multi-map.
            if op.startswith("function "):
                fn_stack.append(pc)
                # print('; '.join(("start" if addr == 0 else src_map[addr]) for addr in fn_stack))
                if cycle > SKIP_CYCLES:
                    fns[pc] += 1
            elif op.startswith("return") and len(fn_stack) > 1:
                # TODO: wait to pop _after_ this op, so the return is charged to the function (not the caller)
                fn_stack.pop()
                # print('; '.join(("start" if addr == 0 else src_map[addr]) for addr in fn_stack))

        if cycle > SKIP_CYCLES:
            if current_instr:
                instructions[current_instr] += 1
        
            if current_opcode:
                opcodes[current_opcode] += 1
            
            fn_instructions[fn_stack[-1]] += 1

        computer.ticktock()

    print()

    # print(raw_instructions.most_common(50))

    print("Instructions (top 50):")
    for addr, count in instructions.most_common(50):
        print(f"  {100*count/CYCLES:0.2f}%: {src_map[addr]} @ {addr}")
    print()    

    print("Opcodes (top 50):")
    for op, count in opcodes.most_common(50):
        print(f"  {100*count/CYCLES:0.2f}%: {op}")
    print()    

    print("Functions (top 20):")
    for addr, count in fn_instructions.most_common(20):
        print(f"  {100*count/CYCLES:0.2f}%: {'start' if addr == 0 else src_map[addr]} @ {addr} ({fns[addr]} times)")

    
if __name__ == "__main__":
    main()
