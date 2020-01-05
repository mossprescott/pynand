from nand.optimize import simplify

def translate(ic):
    """Given an IC, generate the Python source of a class which implements the chip, as a sequence of lines."""

    flat = simplify(ic.flatten())

    class_name = f"{ic.label}_gen"
    lines = [
        f"class {class_name}(Chip):",
        f"    def __init__(self):",
        f"        Chip.__init__(self, {ic.inputs()!r}, {ic.outputs()!r})",
        # TODO
        f"        self._a = 0",
        f"        self._b = 0",
        f"        self._out = 0",
        f"",
        f"    def _combine(self):",
        # TODO
        f"        _0 = not (self._a and self._b)",
        f"        self._out = _0",
        f"",
        f"    def _sequence(self):",
        # TODO
        f"        pass",
    ]

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
