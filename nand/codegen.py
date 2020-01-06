from nand.component import Nand, Const
from nand.integration import IC, Connection, root
from nand.optimize import simplify

PRIMITIVES = set([
    "Nand",
    "Not16", "And16", "Add16", "Mux16", "Zero16",  # These are enough for the ALU
    # "Not", "And", "Or", "Xor",
    "Inc16", "Register"  # Needed for PC
])

def translate(ic):
    """Given an IC, generate the Python source of a class which implements the chip, as a sequence of lines."""

    # flat = simplify(ic.flatten(primitives=PRIMITIVES))  # TODO: don't flatten everything in simplify
    flat = ic.flatten(primitives=PRIMITIVES)
    # print(flat)
    all_comps = flat.sorted_components()

    lines = []
    def l(indent, str):
        lines.append("    "*indent + str)

    def src(conn):
        # TODO: deal with lots of cases
        if conn.comp == root:
            return f"self._{conn.name}"
        elif isinstance(conn.comp, Const):
            return conn.comp.value
        else:
            local_name = f"_{all_comps.index(conn.comp)}_{conn.name}"
            if conn.bit != 0:
                return f"{local_name} & (1 << {conn.bit}) != 0"
            elif conn.comp.label == "Register":
                return f"self.{local_name}"
            else:
                return local_name

    def unary16(comp, template):
        # TODO: check for parallel wiring; deal with it if not
        in_conn = ic.wires[Connection(comp, "in_", 0)]  # HACK
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src(in_conn))}")
        
    def binary16(comp, template):
        # TODO: check for parallel wiring; deal with it if not
        a_conn = ic.wires[Connection(comp, "a", 0)]  # HACK
        b_conn = ic.wires[Connection(comp, "b", 0)]  # HACK
        l(2, f"_{all_comps.index(comp)}_out = {template.format(src(a_conn), src(b_conn))}")

    class_name = f"{ic.label}_gen"
    l(0, f"class {class_name}(Chip):")
    l(1,   f"def __init__(self):")
    l(2,     f"Chip.__init__(self, {ic.inputs()!r}, {ic.outputs()!r})")
    for name in flat.inputs():
        l(2, f"self._{name} = 0  # input")
    for name in flat.outputs():
        l(2, f"self._{name} = 0  # output")
    for comp in all_comps:
        if isinstance(comp, IC) and comp.label == "Register":
            l(2, f"self._{all_comps.index(comp)}_out = 0  # register")
    l(0, "")
    
    l(1, f"def _combine(self):"),
    l(2, "def extend_sign(x):")
    l(3, "return (-1 & ~0xffff) | x if x & 0x8000 != 0 else x")
    for comp in all_comps:
        if isinstance(comp, Nand):
            a_conn = ic.wires[Connection(comp, "a", 0)]
            b_conn = ic.wires[Connection(comp, "b", 0)]
            l(2, f"_{all_comps.index(comp)}_out = not ({src(a_conn)} and {src(b_conn)})")
        elif isinstance(comp, Const):
            pass
        elif comp.label == 'Not16':
            unary16(comp, "~{}")
        elif comp.label == 'And16':
            binary16(comp, "{} & {}")
        elif comp.label == 'Add16':
            binary16(comp, "extend_sign({} + {})")
        elif comp.label == 'Mux16':
            sel_conn = ic.wires[Connection(comp, "sel", 0)]
            binary16(comp, f"{{}} if not {src(sel_conn)} else {{}}")
        elif comp.label == 'Zero16':
            unary16(comp, "{} == 0")
        elif comp.label == 'Inc16':
            unary16(comp, "extend_sign({} + 1)")
        elif comp.label == "Register":
            pass  # nothing to do here
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")
    for name, bits in flat.outputs().items():
        # TODO: handle bits > 1
        conn = flat.wires[Connection(root, name, 0)]
        l(2, f"self._{name} = {src(conn)}")
    l(0, "")
    
    l(1, f"def _sequence(self):")
    l(2,   "def extend_sign(x):")
    l(3,     "return (-1 & ~0xffff) | x if x & 0x8000 != 0 else x")
    for comp in all_comps:
        if isinstance(comp, Nand):
            a_conn = ic.wires[Connection(comp, "a", 0)]
            b_conn = ic.wires[Connection(comp, "b", 0)]
            l(2, f"_{all_comps.index(comp)}_out = not ({src(a_conn)} and {src(b_conn)})")
        elif isinstance(comp, Const):
            pass
        elif comp.label == 'Not16':
            unary16(comp, "~{}")
        elif comp.label == 'And16':
            binary16(comp, "{} & {}")
        elif comp.label == 'Add16':
            binary16(comp, "extend_sign({} + {})")
        elif comp.label == 'Mux16':
            sel_conn = ic.wires[Connection(comp, "sel", 0)]
            binary16(comp, f"{{}} if not {src(sel_conn)} else {{}}")
        elif comp.label == 'Zero16':
            unary16(comp, "{} == 0")
        elif comp.label == 'Inc16':
            unary16(comp, "extend_sign({} + 1)")
        elif comp.label == "Register":
            pass
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")
    l(2, "# Now update state:")
    for comp in all_comps:
        if not isinstance(comp, IC):
            pass
        elif comp.label == "Register":
            # TODO: check for parallel wiring; deal with it if not
            in_conn = ic.wires[Connection(comp, "in_", 0)]
            load_conn = ic.wires[Connection(comp, "load", 0)]
            l(2, f"if {src(load_conn)}:")
            l(3,   f"self._{all_comps.index(comp)}_out = {src(in_conn)}")
        elif comp.label in ('Not16', 'And16', 'Add16', 'Mux16', 'Zero16', 'Inc16'):
            pass
        else:
            # print(f"TODO: {comp.label}")
            raise Exception(f"Unrecognized primitive: {comp}")
    l(0, "")


    # print(flat)
    print('\n'.join(f"{str(i+1).rjust(3)}: {l}" for (i, l) in enumerate(lines)))

    eval(compile('\n'.join(lines),
            filename="<generated>",
            mode='single'))
    
    return locals()[class_name]


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
            self._combine()
        return object.__getattribute__(self, f"_{name}")

    def tick(self):
        pass

    def tock(self):
        if self.__dirty:
            self._combine()
        self._sequence()
