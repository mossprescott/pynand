"""A faster evaluator, which assumes that certain components are defined in the usual way.

This is meant to be flexible enough to implement new ALUs, new ISAs, and other variations, and yet
fast enough to run interactive programs.

The following components are assumed to have the conventional behavior, and are implemented
directly in Python:
- Nand, of course
- common 1-bit functions: Not, And, Or
- common 16-bit functions: Not16, And16, Add16, Inc16, Mux16
- one oddball: Zero16 (which could be generalized to Eq16)
- Register
- ROM: there should no more than one ROM present
- MemorySystem: there should be no more than one MemorySystem present

Any other ICs that appear are flattened to combinations of these. The downside is that a 
moderate amount of flattening will have a significant impact on simulation speed. For example,
the entire Computer amounts to 35 components; it's basically just decoding the instruction, 
the ALU function, and a little wiring. That's why this is fast.

If a new design can benefit from some additional components (e.g. ShiftR16), they're not very hard 
to add, but they should be limited to operations that:
- are generally useful (i.e. not design-specific logic)
- are already implemented with Nand, DFF, etc., and shown to be practical

That's right, the entire MemorySystem (mapping main memory, screen memory, and keyboard input 
into a flat address space) is all implemented with fixed logic. The rationale is that changing 
the memory layout also entails constructing a new UI harness, which is beside the point.
"""

from nand.component import Nand, Const, ROM
from nand.integration import IC, Connection, root
from nand.optimize import simplify
from nand.evaluator import extend_sign

PRIMITIVES = set([
    "Nand",
    "Not16", "And16", "Add16", "Mux16", "Zero16",  # These are enough for the ALU
    "Inc16", "Register",  # Needed for PC
    "Not", "And", "Or",  # Needed for CPU
    "MemorySystem",  # Needed for Computer
])


def translate(ic):
    """Generate a Python class implementing the IC, and providing the same interface as you get
    from nand.syntax.run().
    """
    
    class_name, lines = generate_python(ic)
    
    # print(ic)
    # print_lines(lines)

    eval(compile('\n'.join(lines),
            filename="<generated>",
            mode='single'))
    
    return locals()[class_name]


def generate_python(ic):
    """Given an IC, generate the Python source of a class which implements the chip, as a sequence of lines."""

    class_name = f"{ic.label}_gen"
    ic = ic.flatten(primitives=PRIMITIVES)
    # ic = simplify(ic.flatten(primitives=PRIMITIVES))  # TODO: don't flatten everything in simplify

    # print(ic)
    
    all_comps = ic.sorted_components()

    supr = 'SOC' if any(isinstance(c, IC) and c.label == 'MemorySystem' for c in all_comps) else 'Chip'

    lines = []
    def l(indent, str):
        l = "    "*indent + str
        # print(f"> {l}")
        lines.append(l)

    def src_one(comp, name):
        conn = ic.wires[Connection(comp, name, 0)]
        
        # TODO: deal with lots of cases
        if isinstance(conn.comp, Const):
            value = conn.comp.value
        elif conn.comp == root:
            value = f"self._{conn.name}"
        else:
            value = f"_{all_comps.index(conn.comp)}_{conn.name}"

        if conn.bit != 0:
            return f"({value} & (1 << {conn.bit}) != 0)"
        elif conn.comp.label == "Register":
            raise Exception("TODO: unexpected wiring for 1-bit component")
        else:
            return f"({value} & 0b1 != 0)" 

    def src_many(comp, name, bits=None):
        if bits is None:
            bits = 16

        conn0 = ic.wires[Connection(comp, name, 0)]
        if conn0.bit != 0:
            raise Exception(f"TODO: unexpected wiring for {bits}-bit component")
        for i in range(1, bits):
            conn_i = ic.wires[Connection(comp, name, i)]
            if conn_i.comp != conn0.comp or conn_i.name != conn0.name or conn_i.bit != i:
                raise Exception(f"TODO: unexpected wiring for {bits}-bit component")
        
        conn = conn0
        
        # TODO: deal with lots of cases
        if isinstance(conn.comp, Const):
            return conn.comp.value

        if conn.comp == root:
            name = f"self._{conn.name}"
        else:
            name = f"_{all_comps.index(conn.comp)}_{conn.name}"

        if conn.comp.label == "Register":
            return f"self.{name}"
        else:
            return name

    def unary1(comp, template):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src_one(comp, 'in_'))}")

    def binary1(comp, template):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src_one(comp, 'a'), src_one(comp, 'b'))}")

    def unary16(comp, template, bits=None):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src_many(comp, 'in_', bits))}")
        
    def binary16(comp, template):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src_many(comp, 'a'), src_many(comp, 'b'))}")

    l(0, f"class {class_name}({supr}):")
    l(1,   f"def __init__(self):")
    l(2,     f"{supr}.__init__(self, {ic.inputs()!r}, {ic.outputs()!r})")
    for name in ic.inputs():
        l(2, f"self._{name} = 0  # input")
    for name in ic.outputs():
        l(2, f"self._{name} = 0  # output")
    for comp in all_comps:
        if isinstance(comp, IC) and comp.label == "Register":
            l(2, f"self._{all_comps.index(comp)}_out = 0  # register")
            
    l(0, "")
    
    l(1, f"def _eval(self, update_state):")
    l(2,   "def extend_sign(x):")
    l(3,     "return (-1 & ~0xffff) | x if x & 0x8000 != 0 else x")
    for comp in all_comps:
        if isinstance(comp, Nand):
            binary1(comp, "not ({} and {})")
        elif isinstance(comp, Const):
            pass
        elif comp.label == 'Not':
            unary1(comp, "not {}")
        elif comp.label == 'And':
            binary1(comp, "{} and {}")
        elif comp.label == 'Or':
            binary1(comp, "{} or {}")
        elif comp.label == 'Not16':
            unary16(comp, "~{}")
        elif comp.label == 'And16':
            binary16(comp, "{} & {}")
        elif comp.label == 'Add16':
            binary16(comp, "extend_sign({} + {})")
        elif comp.label == 'Mux16':
            binary16(comp, f"{{}} if not {src_one(comp, 'sel')} else {{}}")
        elif comp.label == 'Zero16':
            unary16(comp, "{} == 0")
        elif comp.label == 'Inc16':
            unary16(comp, "extend_sign({} + 1)")
        elif comp.label == "Register":
            l(2, f"# _{all_comps.index(comp)} is a Register; updated later")
        elif isinstance(comp, ROM):
            l(2, f"_{all_comps.index(comp)}_address = {src_many(comp, 'address', comp.address_bits)}")
            l(2, f"if len(self._rom) > _{all_comps.index(comp)}_address:")
            l(3,   f"_{all_comps.index(comp)}_out = self._rom[_{all_comps.index(comp)}_address]")
            l(2, f"else:")
            l(3,   f"_{all_comps.index(comp)}_out = 0")
        # elif isinstance(comp, RAM):
        #     l(2, f"_{all_comps.index(comp)}_out = self.{all_comps.index(comp)}[{src_many(comp, 'address', comp.address_bits)}]")
        # elif isinstance(comp, Input):
        #     l(2, f"# _{all_comps.index(comp)} is a Input: self._{all_comps.index(comp)} is used")
        elif comp.label == "MemorySystem":
            l(2, f"_{all_comps.index(comp)}_address = {src_many(comp, 'address', 14)}")  # TODO: 15?
            l(2, f"if 0 <= _{all_comps.index(comp)}_address < 0x4000:")
            l(3,   f"_{all_comps.index(comp)}_out = self._ram[_{all_comps.index(comp)}_address]")
            l(2, f"elif _{all_comps.index(comp)}_address < 0x6000:")
            l(3,   f"_{all_comps.index(comp)}_out = self._screen[_{all_comps.index(comp)}_address & 0x1fff]")
            l(2, f"elif _{all_comps.index(comp)}_address == 0x6000:")
            l(3,   f"_{all_comps.index(comp)}_out = self._keyboard")
            l(2, f"else:")
            l(3,   f"_{all_comps.index(comp)}_out = 0")
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")

    for name, bits in ic.outputs().items():
        if bits == 1:
            l(2, f"self._{name} = {src_one(root, name)}")
        else:
            l(2, f"self._{name} = {src_many(root, name)}")

    l(2, "if update_state:")
    l(3,   "pass")
    for comp in all_comps:
        if not isinstance(comp, IC) or comp.label in ('Not', 'And', 'Or', 'Not16', 'And16', 'Add16', 'Mux16', 'Zero16', 'Inc16'):
            # All combinational components: nothing to do here
            pass
        elif comp.label == "Register":
            # l(3, f"print('register: {all_comps.index(comp)}')")  # HACK
            l(3, f"if {src_one(comp, 'load')}:")
            l(4,   f"self._{all_comps.index(comp)}_out = {src_many(comp, 'in_')}")
            # l(4,   f"print('  loaded: ' + str({src_many(comp, 'in_')}))")  # HACK
        elif comp.label == "MemorySystem":
            l(3, f"if {src_one(comp, 'load')}:")
            l(4,   f"_{all_comps.index(comp)}_in = {src_many(comp, 'in_')}")
            l(4,   f"if 0 <= _{all_comps.index(comp)}_address < 0x4000:")
            l(5,     f"self._ram[_{all_comps.index(comp)}_address] = _{all_comps.index(comp)}_in")
            l(4,   f"elif _{all_comps.index(comp)}_address < 0x6000:")
            l(5,     f"self._screen[_{all_comps.index(comp)}_address & 0x1fff] = _{all_comps.index(comp)}_in")
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")
    l(0, "")
    
    return class_name, lines


def print_lines(lines):
    """Print numbered source lines."""
    for i, l in enumerate(lines):
        print(f"{str(i+1).rjust(3)}: {l}")


class Chip:
    """Super for generated classes, which mostly deals with inputs and outputs."""
    def __init__(self, inputs, outputs):
        self.__inputs = inputs
        self.__outputs = outputs
        self.__dirty = True
        
    def __setattr__(self, name, value):
        if name.startswith('_'): return object.__setattr__(self, name, value)
        
        if name not in self.__inputs:
            raise Exception(f"No such input: {name}")

        object.__setattr__(self, f"_{name}", value)
        self.__dirty = True
    
    def __getattr__(self, name):
        if name not in self.__outputs:
            raise Exception(f"No such output: {name}")

        if self.__dirty:
            self._eval(False)
        return object.__getattribute__(self, f"_{name}")

    def tick(self):
        """Raise the clock, preparing to advance to the next cycle."""
        pass

    def tock(self):
        """Lower the clock, causing clocked chips to assume their new values."""
        self._eval(True)
        
    def ticktock(self):
        """Equivalent to tick(); tock()."""
        self.tock()


class SOC(Chip):
    """Super for chips that include a full computer with ROM, RAM, and keyboard input."""
    
    def __init__(self, inputs, outputs):
        Chip.__init__(self, inputs, outputs)
        self._rom = []
        self._ram = [0]*(1 << 14)
        self._screen = [0]*(1 << 13)
        self._keyboard = 0
        
    def init_rom(self, instructions):
        """Overwrite the top of the ROM with a sequence of instructions.
    
        A two-instruction infinite loop is written immediately
        after the program, which could in theory be used to detect termination.
        """
    
        size = len(instructions)
        self._rom = instructions + [
            size,  # @size (which is the address of this instruction)
            0b111_0_000000_000_111,  # JMP
        ]

    def reset_program(self):
        """Reset the PC to 0, so that the program will continue execution as if from startup.
        
        All other state is unaffected.
        """
        self.reset = True
        self.ticktock()
        self.reset = False
        
    def run_program(self, instructions):
        """Install and run a sequence of instructions, stopping when pc runs off the end."""

        self.init_rom(instructions)
        self.reset_program()

        while self.pc <= len(instructions):
            self.ticktock()

    def peek(self, address):
        """Read a value from the main RAM. Address must be between 0x000 and 0x3FFF."""
        return self._ram[address]
    
    def poke(self, address, value):
        """Write a value to the main RAM. Address must be between 0x000 and 0x3FFF."""
        self._ram[address] = extend_sign(value)
    
    def peek_screen(self, address):
        """Read a value from the display RAM. Address must be between 0x000 and 0x1FFF."""
        return self._screen[address]
    
    def poke_screen(self, address, value):
        """Write a value to the display RAM. Address must be between 0x000 and 0x1FFF."""
        self._screen[address] = extend_sign(value)
    
    def set_keydown(self, keycode):
        """Provide the code which identifies a single key which is currently pressed."""
        self._keyboard = keycode