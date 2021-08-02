import os

from nand.codegen import print_lines

class AssemblySource:
    """Utility for emitting assembly, with support for tracking source maps.

    This is handy when writing a VM translator, or other program that emits assembly code.
    """

    def __init__(self):
        self.seq = 0
        self.instruction_count = 0
        self.lines = []
        self.src_map = {}


    def next_label(self, name):
        """Generate a unique label starting with `name`.
        """

        result = f"{name}_{self.seq}"
        self.seq += 1
        return result


    def start(self, op):
        """Record the beginning of instructions for an opcode. The offset is recorded to support debugging,
        and a comment is automatically inserted.
        """

        self.src_map[self.instruction_count] = op
        self.comment(f"{self.instruction_count}: {op}")


    def comment(self, comment):
        self.lines.append(f"// {comment}")


    def label(self, name):
        self.lines.append(f"({name})")


    def instr(self, instr):
        instr = instr.strip()
        if instr.startswith("/") or instr.startswith("("):
            raise SyntaxError(f"Expected an instruction (not a comment or label); found {instr!r}")
        self.lines.append(f"  {instr}")
        self.instruction_count += 1


    def blank(self):
        self.lines.append("")


    def __iter__(self):
        return self.lines.__iter__()


    def run(self, assembler, computer, stop_cycles=None, debug=False):
        """Step through the execution of the generated program, using the provided assembler and
        computer.

        If `debug` is True, print the source op and a summary of the machine state before beginning
        each source op.

        This assumes the assembler doesn't do anything clever with the instructions, so they
        map one-to-one with the instructions emitted here.
        """

        if stop_cycles is None:
            stop_cycles = self.instruction_count
        stop_cycles *= 2

        if debug:
            # print_lines(self.lines)
            print('\n'.join(self.lines))
            print()

        asm = assembler(self)
        computer.init_rom(asm)

        SP = 0
        LCL = 1
        ARG = 2
        THIS = 3
        THAT = 4

        def print_state():
            tmp = [str(computer.peek(i)) for i in range(5, 13)]
            gpr = [str(computer.peek(i)) for i in range(13, 16)]
            arg = [str(computer.peek(i)) for i in range(computer.peek(ARG), computer.peek(LCL)-5)]
            saved = [str(computer.peek(i)) for i in range(computer.peek(LCL)-5, computer.peek(LCL))]
            stack = [str(computer.peek(i)) for i in range(computer.peek(LCL) or 256, computer.sp)]
            static = [str(computer.peek(i)) for i in range(16, 32)]
            print(f"  temp: {tmp}; gpr: {gpr}")
            print(f"  arg({computer.peek(ARG)}): {arg}; return: {saved[0]}; l,a,t,t: {saved[1:]}")
            print(f"  local+stack({computer.sp}): {stack[-20:]}")
            # print(f"  static: {static}")

        for cycles in range(stop_cycles):
            if debug:
                op = self.src_map.get(computer.pc)
                if op:
                    print_state()
                    print(f"{computer.pc}: {op} ({cycles:0,d} of {stop_cycles:0,d} cycles)")
            # This is handy to catch common errors, but doesn't work when the stack is going to be
            # initialized by the program itself.
            # if computer.peek(0) < 256:
            #     print(f"broken stack at {computer.pc}")
            #     print_state()
            #     raise Exception()
            computer.ticktock()
        print_state()


def translate_dir(translator, parse_line, dir_path):
    def translate_ops(ops):
        better_ops = translator.rewrite_ops(ops)
        for op, args in better_ops:
            translator.__getattribute__(op)(*args)

    for fn in os.listdir(dir_path):
        if fn.endswith(".vm"):
            # print(f"// Loading VM source: {dir_path}/{fn}")
            with open(f"{dir_path}/{fn}", mode='r') as f:
                ops = [parse_line(l) for l in f if parse_line(l) is not None]
            translate_ops(ops)

        elif fn.endswith(".jack"):
            import project_10, project_11  # HACK
            print(f"// Loading Jack source: {dir_path}/{fn}")
            with open(f"{dir_path}/{fn}", mode='r') as f:
                chars = "\n".join(f.readlines())

                tokens = project_10.lex(chars)
                ast = project_10.parse_class(tokens)
                # print(f"  parsed class: {ast.name}")

                asm = AssemblySource()
                project_11.compile_class(ast, asm)
                # for l in asm.lines: print("    " + l)

                ops = [parse_line(l) for l in asm.lines if parse_line(l) is not None]

                translate_ops(ops)

    translator.finish()
