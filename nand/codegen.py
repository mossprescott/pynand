"""A faster evaluator, which assumes that certain components are defined in the usual way.

This is meant to be flexible enough to implement new ALUs, new ISAs, and other variations, and yet
fast enough to run interactive programs (about 100 kHz).

The following components are assumed to have the conventional behavior, and are implemented
directly in Python:
- Nand, of course
- common 1-bit functions: Not, And, Or
- common 16-bit functions: Not16, And16, Add16, Inc16, Mux16
- a couple of oddballs: Zero16 (which could be generalized to Eq16), Neg16
- Register
- ROM: there should no more than one ROM present
- MemorySystem: there should be no more than one MemorySystem present

A few more are implemented so that this simulator can also be used (and tested) with smaller
chips:
- DFF
- DMux
- DMux8Way
- Mux8Way16
- TODO: RAM, separately from MemorySystem

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

from nand.component import Nand, Const, DFF, ROM
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


def run_compiled(ic):
    """Prepare an IC for simulation, generate a Cython-compatible implementation on the file
    system, then use pyximport to translate it to C, compile it, and finally return an object
    which exposes the inputs and outputs as attributes. If the IC is Computer, it also provides
    access to the ROM, RAM, etc.

    With the simplest possible annotations, which just put the chip's evaluation loop into
    raw integers, it seems to go about 4x faster than the normal interpreter.
    """

    class_name, lines = generate_python(ic, prefix_super=True, cython=True)

    module_name = f"compiled_{class_name}"
    temp_path = f"generated/{module_name}.pyx"

    with open(temp_path, "w") as f:
        for l in lines:
            f.write(l)
            f.write("\n")

    print(f"wrote {temp_path}")

    # Yikes:
    import pyximport  # type: ignore
    pyximport.install()
    exec(f"import generated.{module_name}")
    chip_class = eval(f"generated.{module_name}.{class_name}")

    print(f"loaded {class_name}")

    return chip_class()


PRIMITIVES = set([
    "Nand",
    "Not16", "And16", "Add16", "Mux16", "Zero16", "Neg16",  # These are enough for the ALU
    "Inc16", "Register",  # Needed for PC
    "Not", "And", "Or",  # Needed for CPU
    "MemorySystem",  # Needed for Computer
    # Additional components used in the exercises, but not typically used in a full computer sim:
    "DMux", "DMux8Way", "Mux8Way16",
    # Additional for alternative CPUs:
    "Dec16", "Eq16", "Mask15", "ShiftR16",
])


SPECIAL = set([
    "Register", "ROM",
    "DMux", "DMux8Way", "Mux8Way16",
    "Add16", "Inc16", "Dec16",
])
"""Primitives that require special handling, and therefore can't be inlined."""

def generate_python(ic, inline=True, prefix_super=False, cython=False):
    """Given an IC, generate the Python source of a class which implements the chip, as a sequence of lines."""

    class_name = f"{ic.label}_gen"
    ic = ic.flatten(primitives=PRIMITIVES)
    # ic = simplify(ic.flatten(primitives=PRIMITIVES))  # TODO: don't flatten everything in simplify

    # print(ic)

    all_comps = ic.sorted_components()

    if any(conn == clock for conn in ic.wires.values()):
        raise NotImplementedError("This simulator cannot handle chips that refer to 'clock' directly.")

    if any(isinstance(c, IC) and c.label == 'MemorySystem' for c in all_comps):
        supr = "SOC"
    else:
        supr = "Chip"

    lines = []
    def l(indent, str):
        l = "    "*indent + str
        lines.append(l)

    def inlinable(comp):
        """If a component has only one output and it's only connected to one input, it can be
        inlined, and its evaluation may be skipped thanks to short-circuiting.
        This alone is good for about 20% speedup.
        """
        if inline:
            connections = set((f.name, t.comp, t.name) for (t, f) in ic.wires.items() if f.comp == comp)
            return len(connections) <= 1
        else:
            return False

    def output_name(comp):
        if comp.label == "DFF":
            return f"_{all_comps.index(comp)}_dff"
        elif comp.label == "Register":
            return f"_{all_comps.index(comp)}_reg"
        elif comp.label == "MemorySystem":
            return f"_{all_comps.index(comp)}_mem"
        else:
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
            elif conn.comp.label == "DFF":
                value = f"_{all_comps.index(conn.comp)}_dff"
            # elif conn.comp.label == "Register":
            #     value = f"_{all_comps.index(conn.comp)}_reg"
            else:
                value = f"_{all_comps.index(conn.comp)}_{conn.name}"
        elif conn.comp.label == "DFF":
            value = f"_{all_comps.index(conn.comp)}_dff"
        # elif conn.comp.label == "Register":
        #     value = f"_{all_comps.index(conn.comp)}_reg"
        elif conn.comp.label == "MemorySystem" and conn.name == "tty_ready":
            # Tricky: this seems pretty bogus. MemorySystem is the first primitive
            # which has more than one output, and it can be computed from the
            # special state.
            value = f"self._tty == 0"
        else:
            value = f"_{all_comps.index(conn.comp)}_{conn.name}"

        if conn.bit != 0 or any(c.comp == conn.comp and c.name == conn.name and c.bit != 0 for c in ic.wires.values()):
            # Note: assuming the value is used as a condition and not actually comparing with 0
            # saves ~5%. But could be dangerous?
            return f"({value} & {hex(1 << conn.bit)})"
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
                return f"_{all_comps.index(conn.comp)}_reg"
            elif conn.comp.label == "MemorySystem":
                return f"_{all_comps.index(conn.comp)}_mem"
            elif inlinable(conn.comp):
                expr = component_expr(conn.comp)
                if expr:
                    return f"({expr})"

            return f"_{all_comps.index(conn.comp)}_{conn.name}"  # but it's always "out"?
        else:
            return "extend_sign(" + " | ".join(f"(bool({src_one(comp, name, i)}) << {i})" for i in range(bits)) + ")"

    def unary1(comp, template):
        return template.format(src_one(comp, 'in_'))

    def binary1(comp, template):
        return template.format(a=src_one(comp, 'a'), b=src_one(comp, 'b'))

    def unary16(comp, template, bits=None):
        return template.format(src_many(comp, 'in_', bits))

    def binary16(comp, template):
        return template.format(a=src_many(comp, 'a'), b=src_many(comp, 'b'))

    def component_expr(comp):
        if isinstance(comp, Nand):
            return binary1(comp, "not ({a} and {b})")
        elif isinstance(comp, Const):
            return None
        elif comp.label == 'Not':
            return unary1(comp, "not {}")
        elif comp.label == 'And':
            return binary1(comp, "{a} and {b}")
        elif comp.label == 'Or':
            return binary1(comp, "{a} or {b}")
        elif comp.label == 'Not16':
            return unary16(comp, "~{}")
        elif comp.label == 'And16':
            return binary16(comp, "{a} & {b}")
        elif comp.label == 'Add16':
            return None
        elif comp.label == 'Mux16':
            sel = src_one(comp, 'sel')
            # TODO: simplify the IC to eliminate these constants instead
            if sel == 0:
                return src_many(comp, 'a')
            elif sel == 1:
                return src_many(comp, 'b')
            else:
                return binary16(comp, f"{{b}} if {sel} else {{a}}")
        elif comp.label == 'Zero16':
            return unary16(comp, "{} == 0")
        elif comp.label == 'Eq16':
            return binary16(comp, "({a} & 0xffff) == ({b} & 0xffff)")
        elif comp.label == 'Neg16':
            return unary16(comp, "{} < 0")
        elif comp.label == 'Inc16':
            return None
        elif comp.label == 'Dec16':
            return None
        elif comp.label == 'Mask15':
            # So, yeah, this isn't really all that general in application. Need some way to
            # represent arbitrary mask/shift/rotate operations?
            return unary16(comp, "{} & 0x7fff", bits=15)
        elif comp.label == 'ShiftR16':
            # So, yeah, this isn't really all that general in application. Need some way to
            # represent arbitrary mask/shift/rotate operations?
            return unary16(comp, "{} >> 1")
        elif comp.label == 'DMux':
            return None  # note: multiple outputs doesn't really inline
        elif comp.label == 'DMux8Way':
            return None  # note: multiple outputs doesn't really inline
        elif comp.label == 'Mux8Way16':
            # TODO: this one _could_ be inlined with a large nested if/else expr.
            return None
        elif comp.label == "Register":
            return None
        elif comp.label == "MemorySystem":
            return None
        elif isinstance(comp, DFF):
            return None
        elif isinstance(comp, ROM):
            # Note: the ROM is read on every cycle, so no point in trying to inline it away
            return None
        else:
            raise Exception(f"Unrecognized primitive: {comp}")

    if cython:
        l(0, "import cython")
        l(0, "from nand.codegen import *")
        l(0, "")

    l(0, f"class {class_name}({supr}):")
    l(1,   f"def __init__(self):")
    l(2,     f"{supr}.__init__(self)")
    for name in ic.inputs():
        l(2, f"self._{name} = 0  # input")
    for name in ic.outputs():
        l(2, f"self._{name} = 0  # output")
    for comp in all_comps:
        if isinstance(comp, IC) and comp.label == "Register":
            l(2, f"self.{output_name(comp)} = 0")
        elif isinstance(comp, DFF):
            l(2, f"self.{output_name(comp)} = False")
    l(0, "")

    l(1, f"def _eval(self, update_state, cycles=1):")

    if cython:
        for comp in all_comps:
            if comp.label in SPECIAL or (comp.label != "Const" and not inlinable(comp)):
                for name, bits in comp.outputs().items():
                    cython_type = "bool" if bits == 1 else "int"
                    comp_name = f"_{all_comps.index(comp)}_{name}"
                    l(2, f"{comp_name}: cython.{cython_type}")
        l(2, "")

    l(2,   f"for _ in range(cycles):")
    for comp in all_comps:
        if comp.label in ("DFF", "Register"):
            comp_name = output_name(comp)
            l(3, f"{comp_name} = self.{comp_name}")
        elif comp.label == "MemorySystem":
            comp_name = output_name(comp)
            l(3, f"if 0 <= self._latched_address < 0x4000:")
            l(4,   f"{comp_name} = self._ram[self._latched_address]")
            l(3, f"elif 0x4000 <= self._latched_address < 0x6000:")
            l(4,   f"{comp_name} = self._screen[self._latched_address & 0x1fff]")
            l(3, f"elif self._latched_address == 0x6000:")
            l(4,   f"{comp_name} = self._keyboard")
            l(3, f"else:")
            l(4,   f"{comp_name} = 0")

            # l(3, f"{comp_name} = self._ram[self._latched_address] if 0 <= self._latched_address < 0x4000 else (self._screen[self._latched_address & 0x1fff] if 0x4000 <= self._latched_address < 0x6000 else (self._keyboard if self._latched_address == 0x6000 else 0))")
    for comp in all_comps:
        if isinstance(comp, (Const, DFF)):
            pass
        elif comp.label in ("Register", "MemorySystem"):
            pass
        elif isinstance(comp, ROM):
            # TODO: trap index errors with try/except
            l(3, f"{output_name(comp)} = self._rom[{src_many(comp, 'address', comp.address_bits)}]")
        elif comp.label == "DMux":
            in_name = f"_{all_comps.index(comp)}_in"
            sel_name = f"_{all_comps.index(comp)}_sel"
            l(3, f"{in_name} = {src_one(comp, 'in_')}")
            l(3, f"{sel_name} = {src_one(comp, 'sel')}")
            l(3, f"_{all_comps.index(comp)}_a = {in_name} if not {sel_name} else 0")
            l(3, f"_{all_comps.index(comp)}_b = {in_name} if {sel_name} else 0")
        elif comp.label == "DMux8Way":
            in_name = f"_{all_comps.index(comp)}_in"
            sel_name = f"_{all_comps.index(comp)}_sel"
            l(3, f"{in_name} = {src_one(comp, 'in_')}")
            l(3, f"{sel_name} = {src_many(comp, 'sel', 3)} & 0x07")
            for i, c in enumerate("abcdefgh"):
                l(3, f"_{all_comps.index(comp)}_{c} = {in_name} if {sel_name} == {i} else 0")
        elif comp.label == "Mux8Way16":
            # TODO: this could be flattened to one expression and/or inlined
            sel_name = f"_{all_comps.index(comp)}_sel"
            out_name = f"_{all_comps.index(comp)}_out"
            l(3, f"{sel_name} = {src_many(comp, 'sel', 3)} & 0x07")
            l(3, f"if {sel_name} == 0:")
            l(4,   f"{out_name} = {src_many(comp, 'a')}")
            l(3, f"elif {sel_name} == 1:")
            l(4,   f"{out_name} = {src_many(comp, 'b')}")
            l(3, f"elif {sel_name} == 2:")
            l(4,   f"{out_name} = {src_many(comp, 'c')}")
            l(3, f"elif {sel_name} == 3:")
            l(4,   f"{out_name} = {src_many(comp, 'd')}")
            l(3, f"elif {sel_name} == 4:")
            l(4,   f"{out_name} = {src_many(comp, 'e')}")
            l(3, f"elif {sel_name} == 5:")
            l(4,   f"{out_name} = {src_many(comp, 'f')}")
            l(3, f"elif {sel_name} == 6:")
            l(4,   f"{out_name} = {src_many(comp, 'g')}")
            l(3, f"elif {sel_name} == 7:")
            l(4,   f"{out_name} = {src_many(comp, 'h')}")
        elif comp.label == "Add16":
            out_name = output_name(comp)
            l(3, f"{out_name} = {src_many(comp, 'a')} + {src_many(comp, 'b')}")
            l(3, f"if {out_name} < -32768: {out_name} += 65536")
            l(3, f"if {out_name} > 32767: {out_name} -= 65536")
        elif comp.label == "Inc16":
            out_name = output_name(comp)
            l(3, f"{out_name} = {src_many(comp, 'in_')} + 1")
            l(3, f"if {out_name} > 32767: {out_name} -= 65536")
        elif comp.label == "Dec16":
            out_name = output_name(comp)
            l(3, f"{out_name} = {src_many(comp, 'in_')} - 1")
            l(3, f"if {out_name} < -32768: {out_name} += 65536")
        elif not inlinable(comp):
            expr = component_expr(comp)
            if expr:
                l(3, f"{output_name(comp)} = {expr}")
            else:
                raise Exception(f"Unrecognized primitive: {comp}")

    for name, bits in ic.outputs().items():
        if bits == 1:
            l(3, f"self._{name} = bool({src_one(root, name)})")
        else:
            l(3, f"self._{name} = {src_many(root, name, bits)}")

    l(3, "if update_state:")
    any_state = False
    for comp in all_comps:
        if isinstance(comp, DFF):
            l(4, f"self.{output_name(comp)} = {src_one(comp, 'in_')}")
            any_state = True
        elif comp.label == "Register":
            load = src_one(comp, 'load')
            # TODO: simplify the IC to eliminate these constants instead
            if load == 1:
                l(4, f"self.{output_name(comp)} = {src_many(comp, 'in_')}")
            else:
                l(4, f"if {load}:")
                l(5,   f"self.{output_name(comp)} = {src_many(comp, 'in_')}")
            any_state = True
        elif comp.label == "MemorySystem":
            # Note: we also write to the latched address, because that's what's most useful
            in_name = f"_{all_comps.index(comp)}_in"
            l(4, f"if {src_one(comp, 'load')}:")
            l(5,   f"{in_name} = {src_many(comp, 'in_')}")
            l(5,   f"if 0 <= self._latched_address < 0x4000:")
            l(6,     f"self._ram[self._latched_address] = {in_name}")
            l(5,   f"elif 0x4000 <= self._latched_address < 0x6000:")
            l(6,     f"self._screen[self._latched_address & 0x1fff] = {in_name}")
            l(5,   f"elif self._latched_address == 0x6000:")
            l(6,     f"self._tty = {in_name}")
            l(6,     f"self._tty_ready = {in_name} != 0")
            address_expr = src_many(comp, 'address', 14)
            l(4, f"self._latched_address = {address_expr}")
            any_state = True
        elif isinstance(comp, (Const, ROM)):
            pass
        elif comp.label in PRIMITIVES:
            # All combinational components: nothing to do here
            pass
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")
    if not any_state:
        l(4,   "pass")
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

    Note: "clock" isn't exposed as an input, and it's state isn't properly updated, so
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

    def ticktock(self, cycles=1):
        """Equivalent to tick(); tock()."""
        self._eval(True, cycles)


class SOC(Chip):
    """Super for chips that include a full computer with ROM, RAM, keyboard input, and "TTY" output."""

    def __init__(self):
        self._rom = []
        self._latched_address = 0
        self._ram = [0]*(1 << 14)
        self._screen = [0]*(1 << 13)
        self._keyboard = 0
        self._tty = 0

        self.__dirty = True


    def init_rom(self, instructions):
        """Overwrite the top of the ROM with a sequence of instructions.

        A two-instruction infinite loop is written immediately
        after the program, which could in theory be used to detect termination.
        """

        size = len(instructions)

        # Assuming a 15-bit ROM, as we do here, we can't address more than 32K of instructions:
        if size >= 2**15:
            raise Exception(f"Too many instructions: {size:0,d} >= {2**15:0,d}")

        contents = instructions + [
            size,  # @size (which is the address of this instruction)
            0b111_0_000000_000_111,  # JMP
        ]
        self._rom = contents
        # TODO: surprisingly, this is not faster (no apparent effect):
        # self._rom = array.array('H', contents)

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

    def get_tty(self):
        """Read one word of output which has been written to the tty port, and reset it to 0."""
        val = self._tty
        self._tty = 0
        return val

    # Tricky: SP might get special treatment in some implementations, so provide a named property
    # That subclasses can override.
    @property
    def sp(self):
        return self._ram[0]
