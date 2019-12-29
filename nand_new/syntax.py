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

    def __getitem__(self, key):
        """Called when the builder asks for a bit slice of an input."""
        return Ref(self.inst, self.name, key)

    def __repr__(self):
        bit_str = f"[{self.bit}]" if self.bit is not None else ""
        return f"{self.inst.ic}.{self.name}{bit_str}"


class Instance:
    def __init__(self, ic, args):
        self.ic = ic
        def to_ref(name, val):
            if name not in ic.inputs():
                raise SyntaxError(f"Unexpected argument: {name}")

            if isinstance(val, Ref):
                return val
            elif isinstance(val, int):
                return Ref(Instance(nand_new.component.Const(ic.inputs()[name], val), {}), "out", None)
            else:
                raise SyntaxError(f"Expected a reference for input '{name}', got {val}")

        self.args = {name: to_ref(name, val) for (name, val) in args.items()}

    def __getattr__(self, name):
        # TODO: check ic's outputs
        return Ref(self, name, None)

    def __str__(self):
        return f"{self.ic}"

def build(builder):
    class InputCollector:
        def __init__(self, inst):
            self.inst = inst
            self.dict = {}

        def __getattr__(self, name):
            self.dict[name] = None  # TODO: not actually used?
            return Ref(self.inst, name, None)

    class OutputCollector:
        def __init__(self, inst):
            self.inst = inst
            self.dict = {}

        def __setattr__(self, name, value):
            if name in ('inst', 'dict'):   # hack for initialization-time
                return object.__setattr__(self, name, value)

            if not isinstance(value, Ref):
                raise SyntaxError(f"Expected a reference for output '{name}', got {value}")
                
            self.dict[(name, None)] = value

        def __getattr__(self, name):
            """Called when the builder is going to assign to a bit slice of an output."""
            return OutputSlice(self, name)

    class OutputSlice:
        def __init__(self, output_coll, name):
            self.output_coll = output_coll
            self.name = name

        def __setitem__(self, key, value):
            """Value is an int between 0 and 15, or (eventually) a slice object with
            .start and .step on the same interval.
            """
            self.output_coll.dict[(self.name, key)] = value
        
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

        # Now set up inputs and outputs, before doing any wiring:
        input_name_bit = []
        for inst in instances([ref.inst for ref in output_coll.dict.values()]):
            for name, ref in inst.args.items():
                if ref.inst.ic == ic:
                    if ref.bit is not None:
                        input_name_bit.append((ref.name, ref.bit))
                    else:
                        input_name_bit.append((ref.name, inst.ic.inputs()[name]-1))
        for (name, bit), ref in sorted(list(output_coll.dict.items())):
            if ref.inst.ic == ic:
                # FIXME: dup from above
                if ref.bit is not None:
                    input_name_bit.append((ref.name, ref.bit))
                else:
                    # Note: we don't infer bit widths from outside, so just assume bit 0 when
                    # an input is copied directly to an output.
                    input_name_bit.append((ref.name, 0))
        ic._inputs = {name: bit+1 for (name, bit) in sorted(input_name_bit)}
        
        output_name_bit = []
        for (name, bit), ref in output_coll.dict.items():
            if bit is not None:
                max_bit = bit
            elif ref.inst.ic == ic:
                # Note: we don't infer bit widths from outside, so just assume bit 0 when
                # an input is copied directly to an output.
                max_bit = 0
            elif ref.bit is not None:
                # referencing a particular bit makes this a single-bit
                max_bit = 0
            else:
                max_bit = ref.inst.ic.outputs()[ref.name]-1
            output_name_bit.append((name, max_bit))
        ic._outputs = {name: bit+1 for (name, bit) in sorted(output_name_bit)}


        for (name, bit), ref in output_coll.dict.items():
            from_comp = ic.root if ref.inst.ic == ic else ref.inst.ic
            if bit is None and ref.bit is None:
                for i in range(from_comp.outputs()[ref.name]):
                    ic.wire(Connection(from_comp, ref.name, i), Connection(ic.root, name, i))
            else:
                ic.wire(Connection(from_comp, ref.name, ref.bit or 0), Connection(ic.root, name, bit or 0))

        for inst in instances([ref.inst for ref in output_coll.dict.values()]):
            for name, ref in inst.args.items():
                if ref.inst.ic == ic:
                    source_comp = ref.inst.ic.root
                else:
                    source_comp = ref.inst.ic
                if ref.bit is None:
                    target_bits = inst.ic.inputs()[name]
                    for i in range(target_bits):
                        source = Connection(source_comp, ref.name, i)
                        target = Connection(inst.ic, name, i)
                        ic.wire(source, target)
                else:
                    source = Connection(source_comp, ref.name, ref.bit)
                    target = Connection(inst.ic, name, 0)
                    ic.wire(source, target)
                        

        # TODO: check for any un-wired or mis-wired inputs (and outputs?)

        return ic

    return Chip(constr)


def run(chip, **args):
    """Construct a complete IC, synthesize it, and wrap it for easy access."""
    w = NandVectorWrapper(_constr(chip).synthesize())
    for name, value in args.items():
        w.__setattr__(name, value)
    return w


def gate_count(chip):
    """Count the base Components of each type in all the ICs of a chip.
    
    Note: components that are constructed by the builder but don't actually affect any output
    are not included (since they don't actually appear in the constructed IC).
    
    Note: it would be simpler to count after flattening, but at present flatten() is actually
    removing some gates, and the intended use here is to verify the implementation is as
    expected, before any "optimization" we might be able to do.
    
    TODO: have some variants/options for counting the ICs as well as counting components before
    and after flattening.
    """
    counts = {}
    def loop(ic):
        for c in ic.sorted_components():
            if isinstance(c, IC):
                loop(c)
            else:
                key = c.label.lower() + "s"  # e.g. "Nand" -> "nands"
                counts[key] = counts.get(key, 0) + 1
    loop(_constr(chip))
    return counts


def _constr(chip):
    """Construct an IC. If the Chip wraps a Component, a trivial IC is constructed around it so
    we can treat everything the same.
    """
    
    comp = chip.constr()
    if isinstance(comp, IC):
        ic = comp
    else:
        ic = IC(comp.label, comp.inputs(), comp.outputs())
        for name, bits in comp.inputs().items():
            for i in range(bits):
                ic.wire(Connection(ic.root, name, i), Connection(comp, name, i))
        for name, bits in comp.outputs().items():
            for i in range(bits):
                ic.wire(Connection(comp, name, i), Connection(ic.root, name, i))
    return ic


Nand = Chip(nand_new.component.Nand)
