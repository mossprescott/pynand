"""Tools for assembling components into chips."""

import collections
import itertools

from nand.component import Component, Const, DFF

class IC:
    """An integrated circuit assembles one or more components by recording how their
    inputs and outputs are connected.

    An IC also acts as a component when it is assembled with other components into a
    larger chip.
    """

    def __init__(self, label, inputs, outputs):
        self.label = label
        self._inputs = inputs
        self._outputs = outputs
        self.wires = {}

    def inputs(self):
        return self._inputs

    def outputs(self):
        return self._outputs

    def wire(self, from_output, to_input):
        """Connect a single trace from an output of one component to an input of another.

        Note that the IC's inputs act as outputs to feed the inputs of components, and vice versa.
        Yes, that does seem confusing.

        Each input can be connected to exactly one output; an output may feed any number of
        inputs, or none at all. A new wiring overwrites any previous wiring to the same input.

        Both components become part of this circuit.

        The connection is checked on both ends to ensure that it specifies a valid name and bit.
        """

        if from_output.comp == root:
            relevant_outputs = self.inputs()
        else:
            relevant_outputs = from_output.comp.outputs()

        if to_input.comp == root:
            relevant_inputs = self.outputs()
        else:
            relevant_inputs = to_input.comp.inputs()

        if from_output.comp == self:
            raise WiringError("Tried to connect input to self; use `root` instead")
        elif to_input.comp == self:
            raise WiringError("Tried to connect output to self; use `root` instead")
        elif from_output.name not in relevant_outputs:
            raise WiringError(f"Component {self._comp_label(from_output.comp, self.sorted_components())} has no output '{from_output.name}'")
        elif from_output.bit < 0 or from_output.bit >= relevant_outputs[from_output.name]:
            raise WiringError(f"Tried to connect bit {from_output.bit} of {relevant_outputs[from_output.name]}-bit output {self._comp_label(from_output.comp, self.sorted_components())}.{from_output.name}")
        elif to_input.name not in relevant_inputs:
            raise WiringError(f"Component {self._comp_label(to_input.comp, self.sorted_components())} has no input '{to_input.name}'")
        elif to_input.bit < 0 or to_input.bit >= relevant_inputs[to_input.name]:
            raise WiringError(f"Tried to connect bit {to_input.bit} of {relevant_inputs[to_input.name]}-bit input {self._comp_label(to_input.comp, self.sorted_components())}.{to_input.name}")

        self.wires[to_input] = from_output


    def _comp_label(self, comp, all_comps):
        if comp == root:
            return "Root"
        else:
            if comp in all_comps:
                num = f"_{all_comps.index(comp)}"
            else:
                num = ""
            if isinstance(comp, IC):
                return f"{comp.label}{num}"
            else:
                return f"{comp.__class__.__name__}{num}"


    def copy(self):
        """Construct a new IC with all the same components and wiring. Note: this is a shallow copy,
        containing the same child components. Therefore, changes to the wiring of the new IC do not
        affect the original, but changes to the wiring of child components do.
        """
        ic = IC(f"{self.label}", self._inputs, self._outputs)
        ic.wires = self.wires.copy()
        return ic


    def flatten(self, primitives=None):
        """Construct a new IC which has the same structure as this one, but no nested ICs,
        except those whose labels are in `primitives`.
        That is, the wiring of all child ICs has been "inlined" into a single flat assembly.
        """
        if not primitives:
            primitives = set()

        flat_children = {}

        all_wires = {}

        for comp in self.sorted_components():
            if isinstance(comp, IC) and comp.label not in primitives:
                # print(f"flatten: {comp.label}")
                child = comp.flatten(primitives)
                flat_children[comp] = child
                for to_input, from_output in child.wires.items():
                    if from_output.comp == root:
                        from_output = from_output._replace(comp=child)
                    if to_input.comp == root:
                        to_input = to_input._replace(comp=child)
                    all_wires[to_input] = from_output

        for to_input, from_output in self.wires.items():
            if from_output.comp in flat_children:
                from_output = from_output._replace(comp=flat_children[from_output.comp])

            if to_input.comp in flat_children:
                to_input = to_input._replace(comp=flat_children[to_input.comp])

            all_wires[to_input] = from_output

        ic = IC(f"{self.label}[flat]", self._inputs, self._outputs)
        ic.wires = collapse_internal(all_wires)

        # Now prune wires that don't connect to any reachable compononent:
        reachable = set(ic.sorted_components() + [common, root])
        ic.wires = {
            t: f
            for (t, f) in ic.wires.items()
            if f.comp in reachable and t.comp in reachable
        }

        return ic


    def sorted_components(self):
        """List of all components (including only direct children), in the order that signals
        propagate.

        That is, when component A has an output that feeds an input of component B, A comes before B
        in the list. If there are reference cycles among "combinational" components, the components
        are ordered as if one such reference (chosen in no particular way) was removed.

        Components that have partially or completely sequential logic get special treatment:
        DFFs and Registers appear last in the result no matter what, which allows their inputs to
        be evaluated later as well. MemorySystem and the components supplying its `address` input
        are included in the main sequence, but its other inputs can appear later.

        The desired result is:
        - minimal "back-edges", where an output of a later component feeds an input of an earlier one
        - a back-edge whose source is definitely latched is ok (DFF/Register.out); these signals
            are available at any time
        - a back-edge which is used (by the target) only during the update phase is ok
            (MemorySystem.in_ and .load)

        Note: str() labels these back-edges so they can be visually confirmed, but these constraints
        aren't checked for you, and indeed the "vector" simulator can handle some circuits that don't
        obey them, by repeating propagation until a fixed point is found.

        TODO: generalize this and don't assume the behavior of Register/MemorySystem is as expected.
        It should be up to the caller to say what assumptions it wants to make; e.g. a simulator
        (codegen) that's already assuming some particular implementation.
        """

        # DFF/Register output never changes based on upstream combinational logic, so stop the
        # search at a DFF or Register.
        # Still need to update the _inputs_ of any such component each time, but can wait to do
        # it at the end.
        # For MemorySystem, the .address input is needed to determine .out, but .in_ and .load
        # are not used until the update phase.
        # 1) find all reachable components, including through DFFs, etc.
        # 2) add all the special components that were found to the list of "roots"
        # 3) run another search, first traversing only the non-seq. inputs, and then the
        #    special components after

        # Pre-compute wires _into_ each component:
        wires_by_target_comp = {}  # {target comp: (target (input) name, source comp)}
        for t, f in self.wires.items():
            if f.comp != root and f.comp != common:
                wires_by_target_comp.setdefault(t.comp, []).append((t.name, f.comp))

        def is_seq(from_comp, to_comp, input_name):
            """True if this particular input is latched, and therefore available in the combination phase.

            Note that the logic here is a bit tangled. Might get the same result more simply by
            treating the inputs of DFF/Register like the non-address inputs of MemorySystem, but
            that would change more things more places, so for now they get deferred entirely.
            """

            if isinstance(from_comp, DFF):
                return True
            elif isinstance(from_comp, IC) and from_comp.label == "Register":
                return True
            elif isinstance(to_comp, IC) and to_comp.label == "MemorySystem" and input_name != "address":
                # This is the tricky case. The address is needed to supply the correct output, but
                # other inputs (in_ and load) are only used at update time.
                return True
            else:
                return False

        def only_seq_output(from_comp):
            """True if *all* outputs are known to be latched, and therefore the component
            will be excluded from the initial search.
            """
            return isinstance(from_comp, DFF) or (isinstance(from_comp, IC) and from_comp.label == "Register")

        def has_seq_input(to_comp):
            """True if any input is not needed in the combination phase, and therefore some
            sources may have been left out.
            """
            return isinstance(to_comp, IC) and to_comp.label == "MemorySystem"

        def search(roots, ignore_dffs):
            # Note: a set for fast tests, and a list to remember the order
            visited = []
            visited_set = set()

            # The stack is never as deep as the full set of nodes, so just a list seems fast enough for now.
            stack = []

            def loop(n):
                if n not in visited_set and n not in stack:
                    stack.append(n)
                    name_comp = wires_by_target_comp.get(n, [])
                    for input_name, from_comp in sorted(name_comp, key=lambda t: t[0]):
                        if not (ignore_dffs and is_seq(from_comp, n, input_name)):
                            loop(from_comp)
                    stack.remove(n)
                    visited.append(n)
                    visited_set.add(n)
            for n in roots:
                if n in visited_set:
                    # Tricky: we already searched the inputs of n which are needed in the
                    # combinatorial phase. Now also may need to include those which are only
                    # used during update.
                    name_comp = wires_by_target_comp.get(n, [])
                    for _, from_comp in sorted(name_comp, key=lambda t: t[0]):
                        loop(from_comp)
                else:
                    loop(n)
            return visited

        # First pass: just find all the reachable components with sequential behavior, might need
        # to be evaluated for update.
        reachable_seq = [ n
            for n in search([root], False)
            if n != root and (only_seq_output(n) or has_seq_input(n))
        ]

        # Actual search: now search from the root (ignoring inputs for update phase), then from
        # extra components (and their sequential-only inputs).
        result = search([root] + reachable_seq, True)
        result.remove(root)

        return result


    def _connections_sort_key(self):
        all_comps = self.sorted_components()
        def by_component(conn):
            if conn.comp == root:
                num = -1  # inputs first
            elif conn.comp in all_comps:
                num = all_comps.index(conn.comp)
            else:
                num = -2
            return (num, conn.name, conn.bit)
        return by_component


    def __str__(self):
        """A multi-line summary of all the wiring."""
        # Sort wires by topological order of the "from" component, then name, then the "to" component and name.

        # TODO: render components in order, one per line, with neatly summarized inputs and outputs.

        all_comps = self.sorted_components()
        def to_index(c, root_val):
            if c == root:
                return root_val
            elif c not in all_comps:
                # Note: this can happen due to, say, a bug in flattening, and it's easier to debug if
                # str() stillworks in that case.
                return root_val*2  # even before/after inputs/outputs
            else:
                return all_comps.index(c)
        def by_component(t):
            ((fc, fn), (tc, tn)), _ = t
            # Sometimes it's interesting to see the wires by source:
            # return (to_index(fc, -1), fn, to_index(tc, 1000), tn)
            return (
                to_index(tc, 1000), tn,
                to_index(fc,   -1), fn
            )
        def back_edge_label(from_comp, to_comp):
            if from_comp not in all_comps or to_comp not in all_comps:
                return ""
            elif isinstance(from_comp, Const):
                return ""
            elif isinstance(from_comp, DFF):
                return " (latched)"
            elif all_comps.index(from_comp) > all_comps.index(to_comp):
                return " (back-edge)"
            else:
                return ""

        def wires(key, bit_pairs):
            (fc, fn), (tc, tn) = key
            def line(l, r, x):
                return f"  {l:21s} -> {r:21s}{x}"
            def comp_name_label(comp, name):
                if isinstance(comp, Const):
                    return hex(comp.value)
                elif comp == root or (comp == clock.comp and name == clock.name):
                    return name
                else:
                    return f"{self._comp_label(comp, all_comps)}.{name}"
            def conn_label(comp, name, bit):
                if isinstance(comp, Const):
                    return str(int(comp.value & (1 << bit) != 0))
                else:
                    if comp == root:
                        # Not really a typo; the dicts are actually reversed, although it doesn't really matter here.
                        inputs, outputs = self.outputs(), self.inputs()
                    else:
                        inputs, outputs = comp.inputs(), comp.outputs()
                    multibit = inputs.get(name, 0) > 1 or outputs.get(name, 0) > 1
                    bit_label = f"[{bit}]" if multibit else ""
                    return comp_name_label(comp, name) + bit_label

            # detect only the common case of all the bits wired in parallel:
            num_bits = len(bit_pairs)
            if num_bits > 1 and bit_pairs == set([(i, i) for i in range(num_bits)]):
                return [
                    line(f"{comp_name_label(fc, fn)}[0..{num_bits-1}]",
                         f"{comp_name_label(tc, tn)}[0..{num_bits-1}]",
                         back_edge_label(fc, tc))
                ]
            else:
                return [
                    line(conn_label(fc, fn, fb),
                         conn_label(tc, tn, tb),
                         back_edge_label(fc, tc))
                    for fb, tb in sorted(bit_pairs)
                    ]

        # Dictionary of ((from component, from name), (to_component, to_name)) -> set([(from_bit, to_bit)])
        component_name_pairs = {}
        for to_input, from_output in self.wires.items():
            key = ((from_output.comp, from_output.name), (to_input.comp, to_input.name))
            value = (from_output.bit, to_input.bit)
            component_name_pairs.setdefault(key, set()).add(value)

        ins = ', '.join(f"{name}[{bits}]" for name, bits in self.inputs().items())
        outs = ', '.join(f"{name}[{bits}]" for name, bits in self.outputs().items())
        return '\n'.join(itertools.chain(
                [f"{self.label}({ins}; {outs}):"],
                *[wires(*args) for args in sorted(component_name_pairs.items(), key=by_component)]
            ))


    def __repr__(self):
        # HACK
        return self.label


def collapse_internal(graph):
    """Collapse _all_ paths, removing _every_ internal node.
    """

    result = graph.copy()

    to_delete = []
    for src, dst in graph.items():
        while dst in result:
            previous_dst = result[dst]
            result[src] = previous_dst
            to_delete.append(dst)
            dst = previous_dst

    for node in to_delete:
        if node in result:
            del result[node]

    return result


class Root:
    """Pseudo-component which stands in for the IC itself in connections. There is exactly one instance
    this class, `root`, which is used by every IC. Doing it that way makes it trivial to make a copy
    of an IC: just make a shallow copy of the `wires` dictionary.

    Note: inputs() and outputs() not defined here, because te result would be wrong. Anyone interested in
    inputs and outputs needs to special case the root and look at the IC itself.
    """

    def __init__(self):
        self.label = 'root'

    def inputs(self):
        raise NotImplementedError("Not a true component. Input and outputs are available from the IC.")

    def outputs(self):
        raise NotImplementedError("Not a true component. Input and outputs are available from the IC.")

root = Root()
"""A single instance of Root which should be the only instance ever."""


class Common:
    """Pseudo-component to which globally-available signals are attached. Namely, 'clock'.
    """
    def __init__(self):
        self.label = "common"

    def inputs(self):
        return {}

    def outputs(self):
        return {"clock": 1}

common = Common()
"""A single instance of Common which should be the only instance ever."""

Connection = collections.namedtuple('Connection', ('comp', 'name', 'bit'))

clock = Connection(common, "clock", 0)
"""'Output' connection from which the current value of the clock signal can be read.
This signal is available to all components, and updated externally.
"""

class WiringError(Exception):
    pass
