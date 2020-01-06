from nand.component import Nand, Const
from nand.integration import IC, Connection, root
from nand.optimize import simplify


PRIMITIVES = set([
    "Nand",
    "Not16", "And16", "Add16", "Mux16", "Zero16",  # These are enough for the ALU
    "Inc16", "Register",  # Needed for PC
    "Not", "And", "Or",  # Needed for CPU
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

    lines = []
    def l(indent, str):
        l = "    "*indent + str
        # print(f"> {l}")
        lines.append(l)

    def src1(comp, name):
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

    def src16(comp, name):
        conn0 = ic.wires[Connection(comp, name, 0)]
        if conn0.bit != 0:
            raise Exception("TODO: unexpected wiring for 16-bit component")
        for i in range(1, 16):
            conn_i = ic.wires[Connection(comp, name, i)]
            if conn_i.comp != conn0.comp or conn_i.name != conn0.name or conn_i.bit != i:
                raise Exception("TODO: unexpected wiring for 16-bit component")
        
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
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src1(comp, 'in_'))}")

    def binary1(comp, template):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src1(comp, 'a'), src1(comp, 'b'))}")

    def unary16(comp, template):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src16(comp, 'in_'))}")
        
    def binary16(comp, template):
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src16(comp, 'a'), src16(comp, 'b'))}")

    l(0, f"class {class_name}(Chip):")
    l(1,   f"def __init__(self):")
    l(2,     f"Chip.__init__(self, {ic.inputs()!r}, {ic.outputs()!r})")
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
            binary16(comp, f"{{}} if not {src1(comp, 'sel')} else {{}}")
        elif comp.label == 'Zero16':
            unary16(comp, "{} == 0")
        elif comp.label == 'Inc16':
            unary16(comp, "extend_sign({} + 1)")
        elif comp.label == "Register":
            l(2, f"# _{all_comps.index(comp)}_out is a Register; updated later")
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")

    for name, bits in ic.outputs().items():
        if bits == 1:
            l(2, f"self._{name} = {src1(root, name)}")
        else:
            l(2, f"self._{name} = {src16(root, name)}")

    l(2, "if update_state:")
    l(3,   "pass")
    for comp in all_comps:
        if not isinstance(comp, IC) or comp.label in ('Not', 'And', 'Or', 'Not16', 'And16', 'Add16', 'Mux16', 'Zero16', 'Inc16'):
            # All combinational components: nothing to do here
            pass
        elif comp.label == "Register":
            # l(3, f"print('register: {all_comps.index(comp)}')")  # HACK
            l(3, f"if {src1(comp, 'load')}:")
            l(4,   f"self._{all_comps.index(comp)}_out = {src16(comp, 'in_')}")
            # l(4,   f"print('  loaded: ' + str({src16(comp, 'in_')}))")  # HACK
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
        pass

    def tock(self):
        self._eval(True)
