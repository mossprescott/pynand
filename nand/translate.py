import os
import re

from nand.codegen import print_lines

class AssemblySource:
    """Utility for emitting assembly, with support for tracking source maps.

    This is handy when writing a VM translator, or other program that emits assembly code.

    Note: it's also being used to generate VM instructions, which have a similar syntax,
    but the nomenclature is certainly confusing, and the src_map feature doesn't make sense
    since "instruction" (opcode) counts aren't significant.
    TODO: pull out "VMSource" as a separate type.
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
        """Add a comment line to the instruction stream, but do not record it as the location of an opcode."""
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


    def add_line_raw(self, value):
        """Add a "line" to the stream without any sanity checking or tracking. Useful for hacks."""
        self.lines.append(value)

    def __iter__(self):
        return self.lines.__iter__()


    def find_function(self, class_name, function_name):
        """Search in the src map for the location of the instructions that enter and leave
        a particular function.

        Returns a tuple (address of "function" op, [addresses of all "return" ops within the function]).

        If the function contains no "return" ops, then the list will contain the location just past the
        end of the function's ops.

        Note: the point is that you can tell that you're leaving the function when one of its
        returns is executed, even if it has made some subroutine calls in the meantime.
        """

        start = None

        # Note: reversed, so we always find the _last_ occurrence, in case the function has been overridden
        for addr, op in sorted(self.src_map.items(), reverse=True):
            if op.startswith(f"function {class_name}.{function_name} "):
                start = addr
                break

        if start is None:
            return None

        ends = []
        for addr, op in [t for t in sorted(self.src_map.items()) if t[0] > start]:
            if op == "return":
                ends.append(addr)
            elif op.startswith("function"):
                if ends == []:
                    ends.append(addr-1)  # somewhat bogus, but don't want to trigger if we hit the exact start of the next fn.
                break

        if ends == []:
            # Must be Sys.halt (which is allowed to have no "return"), and must be the last in ROM.
            ends.append(self.instruction_count)

        return start, ends


    def pretty(self, start_addr=0):
        """Lines of code, including the location in ROM of each instruction, as a geneerator."""
        loc = start_addr
        for l in self.lines:
            raw = l.strip()
            if raw == "" or raw.startswith("//"):
                yield f"         {l}"
            elif raw.startswith("("):
                yield f"      {l}"
            else:
                yield f"{loc:5d}: {l}"
                loc += 1


    # TODO: find a better home for this (nand.runtime? .execute?, .debug?)
    def run(self, assembler, computer, stop_cycles=None, debug=False, tty=None):
        """Step through the execution of the generated program, using the provided assembler and
        computer.

        If `debug` is True, print the source op and a summary of the machine state before beginning
        each source op.

        This assumes the assembler doesn't do anything clever with the instructions, so they
        map one-to-one with the instructions emitted here.
        """

        if stop_cycles is None:
            stop_cycles = self.instruction_count
        stop_cycles *= 2  # Hack: because at least one chip/translator uses twice as many cycles as expected.

        if debug:
            # print_lines(self.lines)
            print('\n'.join(self.lines))
            print()

        asm, symbols, statics = assembler(self)
        computer.init_rom(asm)

        SP = 0
        LCL = 1
        ARG = 2
        THIS = 3
        THAT = 4

        def print_state(op=None):
            arg = [computer.peek(i) for i in range(computer.peek(ARG), computer.peek(LCL)-5)]
            saved = [computer.peek(i) for i in range(computer.peek(LCL)-5, computer.peek(LCL))]
            stack = [computer.peek(i) for i in range(computer.peek(LCL) or 256, computer.sp)]
            print("    SP    LCL    ARG   THIS   THAT     R0     R1     R2     R3     R4     R5     R6     R7     G0     G1     G2")
            print(" ".join(f"{w:6d}" for w in ([computer.sp] + [computer.peek(addr) for addr in range(1,16)])))
            print(f"  return: {saved[0]}; saved: {saved[1:]}; args: {arg}")
            print(f"  local+stack: {stack[-50:]}")
            # TODO: show values of statics, maybe only when they're written (or read?!)
            print(f"@{computer.pc}: {op or ''} ({cycles:0,d} of {stop_cycles:0,d} cycles)")

        for cycles in range(stop_cycles):
            op = self.src_map.get(computer.pc)
            if op:
                if debug:
                    print_state(op)
                if op.startswith("call Sys.halt"):
                    print(f"Halted at cycle {cycles:,d}")
                    return

            # This is handy to catch common errors, but doesn't work when the stack is going to be
            # initialized by the program itself.
            # if computer.sp < 256:
            #     print(f"broken stack at {computer.pc}")
            #     print_state()
            #     raise Exception()

            computer.ticktock()

            if tty is not None and not computer.tty_ready:
                c = computer.get_tty()
                # print(f"wrote: {c}; {chr(c)}")
                # TODO: what other character mapping?
                if c == 128:
                    tty.write("\n")
                else:
                    tty.write(chr(c))

        # Always show the final state:
        print_state()
        print()
        print("Did not reach Sys.halt()!")


    # TODO: find a better home for this (nand.runtime? .execute?, .debug?)
    def trace(self, assembler, computer, stop_cycles=1_000_000, tty=None):
        """Step through the execution of the generated program, using the provided assembler and
        computer, logging each subroutine call and return.

        Stop when Sys.halt is called, or after `stop_cycles`.
        """

        asm, symbols, statics = assembler(self)
        computer.init_rom(asm)

        indent = 0
        for cycles in range(stop_cycles):
            op = self.src_map.get(computer.pc)
            if op:
                m = re.match(r"call (.+) (\d+)", op)
                if m is not None:
                    target = m.group(1)
                    arg_count = int(m.group(2))
                    args = [str(computer.peek(computer.sp - arg_count + i)) for i in range(arg_count)]
                    print(f"{cycles:8,d}  {'  '*indent}{target}({', '.join(args)})     @{computer.pc}")
                    indent += 1
                elif op == "return":
                    print(f"{cycles:8,d}  {'  '*indent}return {computer.peek(computer.sp-1)}")
                    indent -= 1

                if op.startswith("call Sys.halt"):
                    return

            computer.ticktock()

            if tty is not None and not computer.tty_ready:
                c = computer.get_tty()
                # print(f"wrote: {c}; {chr(c)}")
                # TODO: what other character mapping?
                if c == 128:
                    tty.write("\n")
                else:
                    tty.write(chr(c))


# TODO: not necessarily a dir_path anymore
def translate_dir(translator, platform, path, print_ops=False):
    """Compile/translate Jack/VM programs from a directory or file,
    feeding the resulting VM instructions through the given translator.
    """

    def load_file(file_path):
        if file_path.endswith(".vm"):
            # print(f"// Loading VM source: {file_path}")
            with open(file_path, mode='r') as f:
                ops = [platform.parse_line(l) for l in f if platform.parse_line(l) is not None]
            translate_ops(translator, ops)

        elif file_path.endswith(".jack"):
            # print(f"// Loading Jack source: {file_path}")
            with open(file_path, mode='r') as f:
                chars = "\n".join(f.readlines())
                translate_jack(translator, platform, chars, print_ops)

        else:
            raise Exception(f"Don't know what to do with file: {file_path}")

    if os.path.isdir(path):
        for fn in os.listdir(path):
            load_file(os.path.join(path, fn))
    else:
        load_file(path)


def translate_jack(translator, platform, src, print_ops=False):
    """Compile Jack source code, then run the resulting VM instructions through the given translator.
    """

    if isinstance(src, str):
        ast = platform.parser(src)
    else:
        ast = src
    # print(f"  parsed class: {ast.name}")
    # print(f"// Loading Jack from AST: class {ast.name}")

    asm = AssemblySource()
    platform.compiler(ast, asm)

    if print_ops:
        for l in asm.lines: print(f"    {l}")

    ops = [platform.parse_line(l) for l in asm.lines if platform.parse_line(l) is not None]

    translate_ops(translator, ops)


def translate_ops(translator, ops):
    """Translate VM ops, which may represent only part of the current program and OS.
    The translator is first given a chance to rewrite ops.

    :param ops: list of tuples (op, arguments).
    """

    # TODO: print the rewritten ops when print_ops is enabled?

    better_ops = translator.rewrite_ops(ops)
    for op in better_ops:
        translator.handle(op)


EXTERNAL_LIBRARY_PATH = None
# EXTERNAL_LIBRARY_PATH = "nand2tetris/tools/OS"

def translate_library(translator, platform):
    if EXTERNAL_LIBRARY_PATH is None:
        for lib_class in platform.library:
            ast = lib_class

            asm = AssemblySource()
            platform.compiler(ast, asm)

            ops = [platform.parse_line(l) for l in asm.lines if platform.parse_line(l) is not None]

            translate_ops(translator, ops)

    else:
        translate_dir(translator, platform, EXTERNAL_LIBRARY_PATH)


def override_sys_wait(translator, platform):
    """Substitute a version of Sys.wait() that just returns immediately.

    This makes game loops run at "full speed", not burning any cycles trying to hit some
    arbitrary timing goal.

    Still a hack, but in this form it works with any compiler/translator.
    When a class is compiled, it gets translated to a set of independent subroutine bodies,
    so here we just define the one we want to override, translate it last, and count on the
    assembler to favor the later occurrence of the label.
    """
    asm = AssemblySource()
    platform.compiler(platform.parser("class Sys { function void wait() { return; } }"), asm)
    for op in translator.rewrite_ops(asm.lines):
        parsed_op = platform.parse_line(op)
        if parsed_op is not None:
            translator.handle(parsed_op)
