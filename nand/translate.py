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


    def __iter__(self):
        return self.lines.__iter__()


    def run(self, assembler, computer, stop_cycles=None, debug=False, num_locals=2, num_args=2):
        """Step through the execution of the generated program, using the provided assembler and 
        computer.
        
        If `debug` is True, print the source op and a summary of the machine state before beginning 
        each source op.

        This assumes the assembler doesn't do anything clever with the instructions, so they 
        map one-to-one with the instructions emitted here.
        """

        if stop_cycles is None:
            stop_cycles = self.instruction_count

        if debug:
            # print_lines(self.lines)
            print('\n'.join(self.lines))
            print()
    
        asm = assembler(self)
        computer.init_rom(asm)

        def print_state():
            tmp = [str(computer.peek(i)) for i in range(5, 13)]
            gpr = [str(computer.peek(i)) for i in range(13, 16)]
            lcl = [str(computer.peek(i)) for i in range(computer.peek(LCL), computer.peek(LCL)+num_locals)]
            arg = [str(computer.peek(i)) for i in range(computer.peek(ARG), computer.peek(ARG)+num_args)]
            stack_bottom = max(256, computer.peek(ARG)+num_args+5)
            stack = [str(computer.peek(i)) for i in range(stack_bottom, computer.peek(SP))]
            static = [str(computer.peek(i)) for i in range(16, 32)]
            print(f"  temp: {tmp}; gpr: {gpr}")
            print(f"  local: {lcl}; arg: {arg}; stack({computer.peek(SP)}): {stack}")
            print(f"  static: {static}")

        for cycles in range(stop_cycles):
            if debug:
                op = self.src_map.get(computer.pc)
                if op:
                    print_state()
                    print(f"{computer.pc}: {op}")
            if computer.peek(0) < 256: 
                print(f"broken stack at {computer.pc}")
                print_state()
                raise Exception()
            computer.ticktock()
        print_state()

        
SP = 0
LCL = 1
ARG = 2
THIS = 3
THAT = 4
