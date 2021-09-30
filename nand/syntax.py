"""Wrappers around IC and NandVector providing a more compact way of constructing and interacting with chips.
"""


import nand.codegen
import nand.component
from nand.integration import IC, Connection, root, common
from nand.optimize import simplify


class Chip:
    """Wraps a component constructor, so that it can be called with arguments to
    construct an instance.
    """

    def __init__(self, constr):
        self.constr = constr

    def __call__(self, **args):
        """Construct a sub-component, with inputs specified by `args`."""

        comp = self.constr()

        missing_args = comp.inputs().keys() - args.keys()
        if missing_args:
            raise SyntaxError(f"Missing input(s): {missing_args}")

        def to_ref(name, val):
            if name not in comp.inputs():
                raise SyntaxError(f"Unrecognized input: {name!r}")

            if isinstance(val, Ref):
                return val
            elif isinstance(val, int):
                return _const_ref(comp.inputs()[name], val)
            else:
                raise SyntaxError(f"Expected a reference for input {name!r}, got {val}")

        arg_refs = {name: to_ref(name, val) for (name, val) in args.items()}

        return Instance(comp, arg_refs)

def _const_ref(bits, val):
    return Ref(Instance(nand.component.Const(bits, val), {}), "out", None)


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
        if self.inst == common:
            inst_str = "common"
        elif isinstance(self.inst, Lazy) and self.inst.inst is None:
            inst_str = "<lazy>"
        else:
            inst_str = self.inst._ic
        bit_str = f"[{self.bit}]" if self.bit is not None else ""
        return f"{inst_str}.{self.name}{bit_str}"


class Instance:
    """An instance of a certain component with particular input refs supplied, and providing
    output refs as attributes.
    """

    def __init__(self, ic, args):
        self._ic = ic
        self.args = args

    def __getattr__(self, name):
        if name not in self._ic.outputs():
            raise SyntaxError(f"Unrecognized output: {name!r}")

        return Ref(self, name, None)

    def __str__(self):
        return f"{self._ic}"


class Lazy:
    """Placeholder instance that allows inputs and outputs to be defined before the actual
    implementation is provided, so that circular references to be created.

    >>> @chip
    ... def Circular(inputs, outputs):
    ...     thing = lazy()
    ...     foo = Not(in_=thing.out)
    ...     thing.set(Not(foo.out))
    ...     outputs.out = thing.out

    # TODO: better example?
    """

    def __init__(self):
        self.inst = None

    def set(self, inst):
        if isinstance(inst, Instance):
            # TODO: checks that are possible only after the instance is resolved?
            self.inst = inst
        else:
            raise SyntaxError(f"Expected an instance, got {inst}")

    @property
    def _ic(self):
        if not self.inst:
            raise SyntaxError("Unresolved lazy reference")
        return self.inst._ic

    def __getattr__(self, name):
        return Ref(self, name, None)


def build(builder, comp_name=None):
    """Construct a Chip based on a builder function. See @chip."""

    if comp_name is None and builder.__name__.startswith("mk"):
        comp_name = builder.__name__[2:]

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

            if isinstance(value, Ref):
                ref = value
            elif isinstance(value, int) and 0 <= value <= 1:
                ref = _const_ref(1, value)
            else:
                raise SyntaxError(f"Expected a reference or single-bit constant for output '{name}', got {value}")

            self.dict[(name, None)] = ref

        def __getattr__(self, name):
            """Called when the builder is going to assign to a bit slice of an output."""
            return OutputSlice(self, name)

    class OutputSlice:
        def __init__(self, output_coll, name):
            self.output_coll = output_coll
            self.name = name

        def __setitem__(self, key, value):
            """Key is an int between 0 and 15, or (eventually) a slice object with
            .start and .step on the same interval.
            """
            if isinstance(value, Ref):
                ref = value
            elif isinstance(value, int) and 0 <= value <= 1:
                ref = _const_ref(1, value)
            else:
                raise SyntaxError(f"Expected a reference or single-bit constant for output '{self.name}[{key}]', got {value}")

            self.output_coll.dict[(self.name, key)] = ref

    def instances(to_search):
        result = set([])
        while to_search:
            inst, to_search = to_search[0], to_search[1:]

            if isinstance(inst, Lazy):
                # Explicitly exclude these refs from the search
                if inst.inst is not None and inst.inst not in result:
                    to_search.append(inst.inst)
            elif inst != common:
                result.add(inst)
                for ref in inst.args.values():
                    if ref.inst not in result:
                        to_search.append(ref.inst)

        return result

    def constr():
        # Tricky: inputs/outputs aren't known yet, but need the IC to be initialized so we can refer
        # to it via an Instance
        ic = IC(comp_name, {}, {})
        inst = Instance(ic, {})
        input_coll = InputCollector(inst)
        output_coll = OutputCollector(inst)
        builder(input_coll, output_coll)

        # Now set up inputs and outputs, before doing any wiring:
        input_name_bit = []
        for inst in instances([ref.inst for ref in output_coll.dict.values()]):
            for name, ref in inst.args.items():
                if ref.inst != common and ref.inst._ic == ic:
                    if ref.bit is not None:
                        input_name_bit.append((ref.name, ref.bit))
                    else:
                        input_name_bit.append((ref.name, inst._ic.inputs()[name]-1))
        for (name, bit), ref in sorted(list(output_coll.dict.items())):
            if ref.inst != common and ref.inst._ic == ic:
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
            elif ref == clock:
                max_bit = 0
            elif ref.inst._ic == ic:
                # Note: we don't infer bit widths from outside, so just assume bit 0 when
                # an input is copied directly to an output.
                max_bit = 0
            elif ref.bit is not None:
                # referencing a particular bit makes this a single-bit
                max_bit = 0
            else:
                max_bit = ref.inst._ic.outputs()[ref.name]-1
            output_name_bit.append((name, max_bit))
        ic._outputs = {name: bit+1 for (name, bit) in sorted(output_name_bit)}


        for (name, bit), ref in output_coll.dict.items():
            if ref.inst == common:
                from_comp = common  # HACK
                from_outputs = common.outputs()
            elif ref.inst._ic == ic:
                from_comp = root
                from_outputs = ic.inputs()
            else:
                from_comp = ref.inst._ic
                from_outputs = from_comp.outputs()

            if bit is None and ref.bit is None:
                for i in range(from_outputs[ref.name]):
                    ic.wire(Connection(from_comp, ref.name, i), Connection(root, name, i))
            else:
                ic.wire(Connection(from_comp, ref.name, ref.bit or 0), Connection(root, name, bit or 0))

        for inst in instances([ref.inst for ref in output_coll.dict.values()]):
            for name, ref in inst.args.items():
                if ref.inst == common:
                    source_comp = common  # HACK
                elif ref.inst._ic == ic:
                    source_comp = root
                else:
                    source_comp = ref.inst._ic

                if ref.bit is None:
                    target_bits = inst._ic.inputs()[name]
                    for i in range(target_bits):
                        source = Connection(source_comp, ref.name, i)
                        target = Connection(inst._ic, name, i)
                        ic.wire(source, target)
                else:
                    source = Connection(source_comp, ref.name, ref.bit)
                    target = Connection(inst._ic, name, 0)
                    ic.wire(source, target)


        # TODO: check for any un-wired or mis-wired inputs (and outputs?)

        return ic

    return Chip(constr)


def chip(func):
    """Decorate a function which uses the provided inputs and outputs to construct a Component.

    The resulting chip can be used as a component in defining additional chips, or can be used
    directly via run():

    >>> @chip
    ... def Invert(inputs, outputs):
    ...     outputs.out = Nand(a=inputs.in_, b=inputs.in_).out
    ...
    >>> invert = run(Invert)
    >>> invert.out
    1
    >>> invert.in_ = 1
    >>> invert.out
    0
    """
    return build(func, func.__name__)


def run(chip, optimize=True, simulator='vector', **args):
    """Construct a complete IC, synthesize it, wrap it for easy access, and initialize inputs.

    `simulator` can be 'vector', for the slow, precise simulator, or 'codegen', for the fast,
    less flexible one. For the adventurous, there is also 'compiled', which is the same as codegen,
    but run through cython's static compiler. See the README.

    Inputs can be provided as additional keyword arguments, or by setting properties on the
    resulting object.
    """

    ic = _constr(chip)

    if simulator == 'compiled':
        w = nand.codegen.run_compiled(ic)
    elif simulator == 'codegen':
        w = nand.codegen.run(ic)
    elif simulator == 'vector':
        w = nand.vector.run(ic, optimize)
    else:
        raise Exception(f"Unrecognized simulator: {simulator}")

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
            elif not isinstance(c, (nand.component.Const, nand.integration.Common)):
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
                ic.wire(Connection(root, name, i), Connection(comp, name, i))
        for name, bits in comp.outputs().items():
            for i in range(bits):
                ic.wire(Connection(comp, name, i), Connection(root, name, i))
    return ic


lazy = Lazy
"""Backward compatibility. Lower case maybe feels more like syntax and less like a kind of component?"""

clock = Ref(common, "clock", None)

Nand = Chip(nand.component.Nand)
DFF = Chip(nand.component.DFF)
def ROM(address_bits):
    return Chip(lambda: nand.component.ROM(address_bits))
def RAM(address_bits):
    return Chip(lambda: nand.component.RAM(address_bits))
Input = Chip(nand.component.Input)
Output = Chip(nand.component.Output)
