from nand.component import Nand
from nand.integration import Connection, root
from nand.optimize import simplify

PRIMITIVES = set([
    "Nand"
])

def translate(ic):
    """Given an IC, generate the Python source of a class which implements the chip, as a sequence of lines."""

    flat = simplify(ic.flatten(primitives=PRIMITIVES))
    all_comps = flat.sorted_components()

    lines = []
    def l(indent, str):
        lines.append("    "*indent + str)

    def src(conn):
        # TODO: deal with lots of cases
        if conn.comp == root:
            return f"self._{conn.name}"
        else:
            return f"_{all_comps.index(conn.comp)}_{conn.name}"

    class_name = f"{ic.label}_gen"
    l(0, f"class {class_name}(Chip):")
    l(1,   f"def __init__(self):")
    l(2,     f"Chip.__init__(self, {ic.inputs()!r}, {ic.outputs()!r})")
    for name in flat.inputs():
        l(2, f"self._{name} = 0")
    for name in flat.outputs():
        l(2, f"self._{name} = 0")
    l(0, "")
    
    l(1, f"def _combine(self):"),
    for comp in all_comps:
        if isinstance(comp, Nand):
            a_conn = ic.wires[Connection(comp, "a", 0)]
            b_conn = ic.wires[Connection(comp, "b", 0)]
            l(2, f"_{all_comps.index(comp)}_out = not ({src(a_conn)} and {src(b_conn)})")
        else:
            raise Exception(f"Unrecognized primitive: {comp}")
    for name, bits in flat.outputs().items():
        # TODO: handle bits > 1
        conn = flat.wires[Connection(root, name, 0)]
        l(2, f"self._{name} = {src(conn)}")
    l(0, "")
    
    l(1, f"def _sequence(self):")
        # TODO
    l(2, f"pass")
    
    print(flat)
    print('\n'.join(lines))

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

    def ticktock(self):
        if self.__dirty:
            self._combine()
        self._sequence()
