"""A faster evaluator, which assumes that certain components are defined in the usual way.

This is meant to be flexible enough to implement new ALUs, new ISAs, and other variations, and yet
fast enough to run interactive programs (about 100 kHz).

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
from nand.integration import IC, Connection, root, clock
from nand.optimize import simplify
from nand.vector import extend_sign


def run(ic):
    """Prepare an IC for simulation, returning an object which exposes the inputs and outputs
    as attributes. If the IC is Computer, it also provides access to the ROM, RAM, etc.
    """
    return translate(ic)()


def translate(ic):
    """Generate a Python class implementing the IC."""
    
    class_name, lines = generate_python(ic)
    
    # print(ic)
    # print_lines(lines)

    eval(compile('\n'.join(lines),
            filename="<generated>",
            mode='single'))
    
    return locals()[class_name]


PRIMITIVES = set([
    "Nand",
    "Not16", "And16", "Add16", "Mux16", "Zero16",  # These are enough for the ALU
    "Inc16", "Register",  # Needed for PC
    "Not", "And", "Or",  # Needed for CPU
    "MemorySystem",  # Needed for Computer
])


def generate_python(ic):
    """Given an IC, generate the Python source of a class which implements the chip, as a sequence of lines."""

    class_name = f"{ic.label}_gen"
    ic = ic.flatten(primitives=PRIMITIVES)
    # ic = simplify(ic.flatten(primitives=PRIMITIVES))  # TODO: don't flatten everything in simplify

    # print(ic)
    
    all_comps = ic.sorted_components()

    if any(conn == clock for conn in ic.wires.values()):
        raise NotImplementedError("This simulator cannot handle chips that refer to 'clock' directly.")

    supr = 'SOC' if any(isinstance(c, IC) and c.label == 'MemorySystem' for c in all_comps) else 'Chip'

    lines = []
    def l(indent, str):
        l = "    "*indent + str
        lines.append(l)

    def inlinable(comp):
        """If a component has only one output and it's only connected to one input, it can be 
        inlined, and its evaluation may be skipped thanks to short-circuiting.
        This alone is good for about 20% speedup.
        """
        connections = set((f.name, t.comp, t.name) for (t, f) in ic.wires.items() if f.comp == comp)
        return len(connections) <= 1

    def output_name(comp):
        return f"_{all_comps.index(comp)}_out"

    def src_one(comp, name, bit=0):
        conn = ic.wires[Connection(comp, name, bit)]
        
        # TODO: deal with lots of cases
        if isinstance(conn.comp, Const):
            value = conn.comp.value
        elif conn.comp == root:
            value = f"self._{conn.name}"
        elif inlinable(conn.comp):
            expr = component_expr(conn.comp)
            if expr:
                value = f"({expr})"
            else:
                value = f"_{all_comps.index(conn.comp)}_{conn.name}"
        else:
            value = f"_{all_comps.index(conn.comp)}_{conn.name}"

        if conn.bit != 0 or any(c.comp == conn.comp and c.name == conn.name and c.bit != 0 for c in ic.wires.values()):
            return f"({value} & {hex(1 << conn.bit)} != 0)"
        elif conn.comp.label == "Register":
            raise Exception("TODO: unexpected wiring for 1-bit component")
        else:
            return value

    def src_many(comp, name, bits=None):
        if bits is None:
            bits = 16

        conn0 = ic.wires[Connection(comp, name, 0)]
        src_conns = [(i, ic.wires.get(Connection(comp, name, i))) for i in range(bits)]
        if all((c.comp == conn0.comp and c.name == conn0.name and c.bit == bit) for (bit, c) in src_conns):
            conn = conn0
        
            if isinstance(conn.comp, Const):
                return conn.comp.value

            if conn.comp == root:
                return f"self._{conn.name}"
            elif conn.comp.label == "Register":
                return f"self._{all_comps.index(conn.comp)}_{conn.name}"
            elif inlinable(conn.comp):
                expr = component_expr(conn.comp)
                if expr:
                    return f"({expr})"

            return f"_{all_comps.index(conn.comp)}_{conn.name}"  # but it's always "out"?
        else:
            return "extend_sign(" + " | ".join(f"({src_one(comp, name, i)} << {i})" for i in range(bits)) + ")"

    def unary1(comp, template):
        return template.format(src_one(comp, 'in_'))

    def binary1(comp, template):
        return template.format(src_one(comp, 'a'), src_one(comp, 'b'))

    def unary16(comp, template, bits=None):
        return template.format(src_many(comp, 'in_', bits))
        
    def binary16(comp, template):
        return template.format(src_many(comp, 'a'), src_many(comp, 'b'))

    def component_expr(comp):
        if isinstance(comp, Nand):
            return binary1(comp, "not ({} and {})")
        elif isinstance(comp, Const):
            return None
        elif comp.label == 'Not':
            return unary1(comp, "not {}")
        elif comp.label == 'And':
            return binary1(comp, "{} and {}")
        elif comp.label == 'Or':
            return binary1(comp, "{} or {}")
        elif comp.label == 'Not16':
            return unary16(comp, "~{}")
        elif comp.label == 'And16':
            return binary16(comp, "{} & {}")
        elif comp.label == 'Add16':
            return binary16(comp, "extend_sign({} + {})")
        elif comp.label == 'Mux16':
            return binary16(comp, f"{{}} if not {src_one(comp, 'sel')} else {{}}")
        elif comp.label == 'Zero16':
            return unary16(comp, "{} == 0")
        elif comp.label == 'Inc16':
            return unary16(comp, "extend_sign({} + 1)")
        elif comp.label == "Register":
            return None
        elif isinstance(comp, ROM):
            # Note: the ROM is read on every cycle, so no point in trying to inline it away
            return None
        elif comp.label == "MemorySystem":
            # Note: the source of address better not be a big computation. At the moment it's always 
            # register A (so, saved in self)
            address = src_many(comp, 'address', 14)
            return f"self._ram[{address}] if 0 <= {address} < 0x4000 else (self._screen[{address} & 0x1fff] if 0x4000 <= {address} < 0x6000 else (self._keyboard if {address} == 0x6000 else 0))"
        else:
            raise Exception(f"Unrecognized primitive: {comp}")
    

    l(0, f"class {class_name}({supr}):")
    l(1,   f"def __init__(self):")
    l(2,     f"{supr}.__init__(self)")
    for name in ic.inputs():
        l(2, f"self._{name} = 0  # input")
    for name in ic.outputs():
        l(2, f"self._{name} = 0  # output")
    for comp in all_comps:
        if isinstance(comp, IC) and comp.label == "Register":
            l(2, f"self.{output_name(comp)} = 0  # register")
            
    l(0, "")
    
    l(1, f"def _eval(self, update_state):")
    l(2,   "def extend_sign(x):")
    l(3,     "return (-1 & ~0xffff) | x if x & 0x8000 != 0 else x")
    for comp in all_comps:
        if isinstance(comp, Const):
            pass
        elif comp.label == "Register":
            pass
        elif isinstance(comp, ROM):
            l(2, f"_{all_comps.index(comp)}_address = {src_many(comp, 'address', comp.address_bits)}")
            l(2, f"if len(self._rom) > _{all_comps.index(comp)}_address:")
            l(3,   f"{output_name(comp)} = self._rom[_{all_comps.index(comp)}_address]")
            l(2, f"else:")
            l(3,   f"{output_name(comp)} = 0")
        elif not inlinable(comp):
            expr = component_expr(comp)
            if expr:
                l(2, f"{output_name(comp)} = {expr}")
            else:
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
            l(4,   f"self.{output_name(comp)} = {src_many(comp, 'in_')}")
            # l(4,   f"print('  loaded: ' + str({src_many(comp, 'in_')}))")  # HACK
        elif comp.label == "MemorySystem":
            # Note: the source of address better not be a big computation. At the moment it's always 
            # register A (so, saved in self)
            address_expr = src_many(comp, 'address', 14)
            in_name = f"_{all_comps.index(comp)}_in"
            l(3, f"if {src_one(comp, 'load')}:")
            l(4,   f"{in_name} = {src_many(comp, 'in_')}")
            l(4,   f"if 0 <= {address_expr} < 0x4000:")
            l(5,     f"self._ram[{address_expr}] = {in_name}")
            l(4,   f"elif 0x4000 <= {address_expr} < 0x6000:")
            l(5,     f"self._screen[{address_expr} & 0x1fff] = {in_name}")
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")
    l(0, "")
    
    for name in ic.inputs():
        l(1, f"def _set_{name}(self, value):")
        l(2,   f"self._{name} = value")
        l(2,   f"self.__dirty = True")
        l(1, f"{name} = property(fset=_set_{name})")
        l(0, "")
    for name in ic.outputs():
        l(1, f"@property")
        l(1, f"def {name}(self):")
        l(2,   f"self._eval(False)")
        l(2,   f"return self._{name}")    
        l(0, "")
    
    return class_name, lines


def print_lines(lines):
    """Print numbered source lines."""
    for i, l in enumerate(lines):
        print(f"{str(i+1).rjust(3)}: {l}")


class Chip:
    """Super for generated classes, providing tick, tock, and ticktock.
    
    This: "clock" isn't exposed as an input, and it's state isn't properly updated, so 
    chips that refer to it directly aren't simulated properly by this implementation.
    
    TODO: handle "clock" correctly, and also implement the components needed by those tests?
    """
    
    def __init__(self):
        self.__dirty = True
    
    def tick(self):
        """Raise the clock, preparing to advance to the next cycle."""
        pass

    def tock(self):
        """Lower the clock, causing clocked chips to assume their new values."""
        self._eval(True)
        
    def ticktock(self):
        """Equivalent to tick(); tock()."""
        self._eval(True)


class SOC(Chip):
    """Super for chips that include a full computer with ROM, RAM, and keyboard input."""
    
    def __init__(self):
        self._rom = []
        self._ram = [0]*(1 << 14)
        self._screen = [0]*(1 << 13)
        self._keyboard = 0
        
        self.__dirty = True
        
        
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

        while self._pc <= len(instructions):
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
