"""Wrappers around IC and NandVector providing a more compact way of constructing and interacting with chips.
"""
from nand.compiler import NandVectorWrapper  # HACK
import nand_new.component
from nand_new.integration import IC, Connection

class Chip:
    def __init__(self, constr):
        self.constr = constr

    def __call__(self, **args):
        """Construct a sub-component, with inputs specified by `args`."""

        comp = self.constr()

        return Instance(comp, args)


class Ref:
    """Names a single- or multiple-bit signal."""

    def __init__(self, inst, name, bit):
        self.inst = inst
        self.name = name
        self.bit = bit

    def __repr__(self):
        bit_str = f"[{self.bit}]" if self.bit is not None else ""
        return f"{self.inst.ic}.{self.name}{bit_str}"


class Instance:
    def __init__(self, ic, args):
        self.ic = ic
        self.args = args

    def __getattr__(self, name):
        # TODO: check ic's outputs
        return Ref(self, name, None)


def build(builder):
    class InputCollector:
        def __init__(self, inst):
            self.inst = inst
            self.dict = {}

        def __getattr__(self, name):
            self.dict[name] = None
            return Ref(self.inst, name, None)

    class OutputCollector:
        def __init__(self, inst):
            self.inst = inst
            self.dict = {}

        def __setattr__(self, name, value):
            if name in ('inst', 'dict'):   # hack for initialization-time
                return object.__setattr__(self, name, value)
            self.dict[name] = value

    def instances(to_search):
        result = set([])
        while to_search:
            inst, to_search = to_search[0], to_search[1:]
            result.add(inst)
            for ref in inst.args.values():
                if ref.inst not in result:
                    to_search.append(ref.inst)
        return result

    def constr():
        builder_name = builder.__name__
        if builder_name.startswith("mk"):
            name = builder_name[2:]
        else:
            name = builder_name

        # Tricky: inputs/outputs aren't known yet, but need the IC to be initialized so we can refer
        # to it via an Instance
        ic = IC(name, {}, {})
        inst = Instance(ic, {})
        input_coll = InputCollector(inst)
        output_coll = OutputCollector(inst)
        builder(input_coll, output_coll)

        ic._inputs = {name: 1 for name in input_coll.dict}
        ic._outputs = {name: 1 for name in output_coll.dict}

        for name, ref in output_coll.dict.items():
            ic.wire(Connection(ref.inst.ic, ref.name, ref.bit or 0), Connection(ic.root, name, 0))

        for inst in instances([ref.inst for ref in output_coll.dict.values()]):
            for name, ref in inst.args.items():
                if ref.inst.ic == ic:
                    source_comp = ref.inst.ic.root
                else:
                    source_comp = ref.inst.ic
                source = Connection(source_comp, ref.name, ref.bit or 0)
                target = Connection(inst.ic, name, 0)
                ic.wire(source, target)

        # TODO: check for any un-wired or mis-wired inputs (and outputs?)

        return ic

    return Chip(constr)


def run(chip, **args):
    """Construct a complete IC, synthesize it, and wrap it for easy access."""
    w = NandVectorWrapper(chip.constr().synthesize())
    for name, value in args.items():
        w.__setattr__(name, value)
    return w


Nand = Chip(nand_new.component.Nand)

