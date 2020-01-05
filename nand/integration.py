import collections
import itertools

from nand.evaluator import NandVector
from nand.component import Component, Const

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

    def has_combine_ops(self):
        """Just return True, because that's virtually always the case and the answer only becomes
        interesting after flattening, when no child ICs are left anyway.
        """
        return True

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


    def flatten(self):
        """Construct a new IC which has the same structure as this one, but no nested ICs.
        That is, the wiring of all child ICs has been "inlined" into a single flat assembly.
        """

        flat_children = {}

        all_wires = {}
        
        for comp in self.sorted_components():
            if isinstance(comp, IC):
                child = comp.flatten()
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
        """List of all components (including only direct children), roughly in the order that 
        signals propagate.

        That is, when component A has an output that feeds an input of component B, A comes before B 
        in the list. If there are reference cycles, the components are ordered as if one such 
        reference (chosen in no particular way) was removed.
        
        DFFs (and other components that have _only_ sequential logic) get special treatment: 
        they appear last in the result no matter what, which allows their inputs to be evaluated 
        later as well.
        """
        
        # DFF output never changes based on upstream combinational logic
        # So stop the DFS at a DFF (or other sequential-only output)
        # Still need to update the _inputs_ of any such component each time, but
        #   can wait to do it at the end.
        # 1) find all reachable components, including through DFFs.
        # 2) add all the DFFs to the list of "roots"
        # 3) run another search, _not_ traversing the DFF inputs
        # How to apply this thinking to RAM? Can it be separated?

        # Pre-compute wires _into_ each component:
        wires_by_target_comp = {}  # {target comp: (target name, source comp)}
        for t, f in self.wires.items():
            if f.comp != root and f.comp != common:
                wires_by_target_comp.setdefault(t.comp, []).append((t.name, f.comp))

        def dfs(roots, ignore_dffs):
            # Note: a set for fast tests, and a list to remember the order
            visited = []
            visited_set = set()

            # The stack is never as deep as the full set of nodes, so just a list seems fast enough for now.
            stack = []

            def loop(n):
                if n not in visited_set and n not in stack:
                    stack.append(n)
                    name_comp = wires_by_target_comp.get(n, [])
                    for _, nxt in sorted(name_comp, key=lambda t: t[0]):
                        if not (ignore_dffs and not nxt.has_combine_ops()):
                            loop(nxt)
                    stack.remove(n)
                    visited.append(n)
                    visited_set.add(n)
            to_search = roots
            while to_search:
                n, to_search = to_search[0], to_search[1:]
                loop(n)
            return visited

        reachable = dfs([root], False)
        reachable.remove(root)
        
        dffs = [n for n in reachable if not n.has_combine_ops()]
        result = dfs([root] + dffs, True)
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


    def synthesize(self):
        """Compile the chip down to traces and ops for evaluation.

        Returns a NandVector.
        """
        return self.flatten()._synthesize()

    def _synthesize(self):
        # check for missing wires?
        # check for unused components?

        any_clock_references = any([True for conn in self.wires.values() if conn == clock])

        # Assign a bit for each output connection:
        all_bits = {}
        next_bit = 0
        if any_clock_references:
            all_bits[clock] = next_bit
            next_bit += 1
            
        for conn in sorted(set(self.wires.values()), key=self._connections_sort_key()):
            if conn != clock:
                all_bits[conn] = next_bit
                next_bit += 1
        
        # Construct map of IC inputs, directly from all_bits:
        inputs = {
            (name, bit): 1 << all_bits[Connection(root, name, bit)]
            for name, bits in self._inputs.items()
            for bit in range(bits)  # TODO: None if single bit?
        }
        
        if any_clock_references:
            inputs[("common.clock", 0)] = 1 << all_bits[clock]

        # Construct map of IC ouputs, mapped to all_bits via wires:
        outputs = {
            (name, bit): 1 << all_bits[self.wires[Connection(root, name, bit)]]
            for name, bits in self._outputs.items()
            for bit in range(bits)  # TODO: None if single bit?
        }

        internal = {}  # TODO

        sorted_comps = self.sorted_components()

        # For each component, construct a map of its traces' bit masks, and ask the component for its ops:
        initialize_ops = []
        combine_ops = []
        sequence_ops = []
        for comp in sorted_comps:
            traces = {}
            for name, bits in comp.inputs().items():
                traces[name] = [1 << all_bits[self.wires[Connection(comp, name, bit)]] for bit in range(bits)]
            for name, bits in comp.outputs().items():
                traces[name] = [1 << all_bits[Connection(comp, name, bit)] for bit in range(bits)]
            initialize_ops += comp.initialize(**traces)
            combine_ops += comp.combine(**traces)
            sequence_ops += comp.sequence(**traces)

        back_edge_from_components = set()
        for to_input, from_output in self.wires.items():
            if (not isinstance(from_output.comp, Const)
                and from_output.comp in sorted_comps
                and to_input.comp in sorted_comps
                and from_output.comp.has_combine_ops()
                and sorted_comps.index(from_output.comp) > sorted_comps.index(to_input.comp)):
                back_edge_from_components.add(from_output.comp)
        non_back_edge_mask = 0
        for conn, bit in all_bits.items():
            if conn.comp not in back_edge_from_components:
                non_back_edge_mask |= 1 << bit

        return NandVector(inputs, outputs, internal, initialize_ops, combine_ops, sequence_ops, non_back_edge_mask)


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
            elif not from_comp.has_combine_ops():
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
