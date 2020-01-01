import collections
from pprint import pprint  # HACK

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
        self.root = Root(self)
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

        if from_output.name not in from_output.comp.outputs():
            raise WiringError(f"Component {self._comp_label(from_output.comp, self.sorted_components())} has no output '{from_output.name}'")
        elif from_output.bit < 0 or from_output.bit >= from_output.comp.outputs()[from_output.name]:
            raise WiringError(f"Tried to connect bit {from_output.bit} of {from_output.comp.outputs()[from_output.name]}-bit output {self._comp_label(from_output.comp, self.sorted_components())}.{from_output.name}")
        elif to_input.name not in to_input.comp.inputs():
            raise WiringError(f"Component {self._comp_label(to_input.comp, self.sorted_components())} has no input '{to_input.name}'")
        elif to_input.bit < 0 or to_input.bit >= to_input.comp.inputs()[to_input.name]:
            raise WiringError(f"Tried to connect bit {to_input.bit} of {to_input.comp.inputs()[to_input.name]}-bit input {self._comp_label(to_input.comp, self.sorted_components())}.{to_input.name}")

        self.wires[to_input] = from_output

    def _comp_label(self, comp, all_comps):
        if comp == self.root:
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

    def _connection_label(self, conn, all_comps):
        if isinstance(conn.comp, Const):
            return str(int(conn.comp.value & (1 << conn.bit) != 0))
        else:
            multi_bit = conn.comp.inputs().get(conn.name, 0) > 1 or conn.comp.outputs().get(conn.name, 0) > 1
            comp = "" if conn.comp == self.root else f"{self._comp_label(conn.comp, all_comps)}."
            bit = f"[{conn.bit}]" if multi_bit else ""
            return f"{comp}{conn.name}{bit}"


    def flatten(self):
        """Construct a new IC which has the same structure as this one, but no nested ICs.
        That is, the wiring of all child ICs has been "inlined" into a single flat assembly.
        """

        ic = IC(f"{self.label}[flat]", self._inputs, self._outputs)

        flat_children = {}

        all_wires = {}
        
        for comp in self.sorted_components():
            if isinstance(comp, IC):
                child = comp.flatten()
                flat_children[comp] = child
                for to_input, from_output in child.wires.items():
                    if from_output.comp == child.root:
                        from_output = from_output._replace(comp=child)
                    if to_input.comp == child.root:
                        to_input = to_input._replace(comp=child)
                    all_wires[to_input] = from_output

        for to_input, from_output in self.wires.items():
            if from_output.comp in flat_children:
                from_output = from_output._replace(comp=flat_children[from_output.comp])
            elif from_output.comp == self.root:
                from_output = from_output._replace(comp=ic.root)

            if to_input.comp in flat_children:
                to_input = to_input._replace(comp=flat_children[to_input.comp])
            elif to_input.comp == self.root:
                to_input = to_input._replace(comp=ic.root)

            all_wires[to_input] = from_output

        ic.wires = collapse_internal(all_wires)
        
        # Now prune wires that don't connect to any reachable compononent:
        reachable = set(ic.sorted_components() + [common, ic.root])
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
            if f.comp != self.root and f.comp != common:
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

        reachable = dfs([self.root], False)
        reachable.remove(self.root)
        
        dffs = [n for n in reachable if not n.has_combine_ops()]
        result = dfs([self.root] + dffs, True)
        result.remove(self.root)

        return result


    def simplify(self):
        """Construct a new chip which is logically identical to this one, but may be smaller
        and more efficient by the removal of certain recognized patterns. More effective after 
        flatten().
        
        When a constant is the input of a Nand, that gate is replaced with either a constant or the 
        other input: Nand(a, 0) = 1; Nand(a, 1) = Not(a)
        
        When a series of two Nands negate and then re-negate the same single value, the second Nand 
        is always removed, and the first may be as well if it's otherwise unused.
        """

        # Note: it feels dirty having any special-casing for specific components here.
        # Maybe this function belongs in a separate "optimize" module.
        from nand.component import Nand

        ic = IC(f"{self.label}[simple]", self._inputs, self._outputs)

        new_wires = {}
        for to_input, from_output in self.wires.items():
            if from_output.comp == self.root:
                from_output = from_output._replace(comp=ic.root)

            if to_input.comp == self.root:
                to_input = to_input._replace(comp=ic.root)

            new_wires[to_input] = from_output

        def const_value(conn):
            if isinstance(conn.comp, Const):
                return conn.comp.value & (1 << conn.bit) != 0
            else:
                return None

        def rewrite(old_conn, new_conn):
            for t, f in list(new_wires.items()):
                if f == old_conn:
                    new_wires[t] = new_conn

        done = False
        while not done:
            done = True
            for comp in set([c.comp for c in new_wires.keys()] + [c.comp for c in new_wires.values()]):
                if isinstance(comp, Nand):
                    a_src = new_wires[Connection(comp, "a", 0)]
                    b_src = new_wires[Connection(comp, "b", 0)]

                    a_val = const_value(a_src)
                    b_val = const_value(b_src)

                    if a_val == False or b_val == False:
                        # Remove this Nand and rewrite its output as Const(1):
                        del new_wires[Connection(comp, "a", 0)]
                        del new_wires[Connection(comp, "b", 0)]
                        old_conn = Connection(comp, "out", 0)
                        new_conn = Connection(Const(1, 1), "out", 0)
                        rewrite(old_conn, new_conn)
                        done = False
                    elif a_val == True and b_val == True:
                        # Remove this Nand and rewrite its output as Const(0):
                        del new_wires[Connection(comp, "a", 0)]
                        del new_wires[Connection(comp, "b", 0)]
                        old_conn = Connection(comp, "out", 0)
                        new_conn = Connection(Const(1, 0), "out", 0)
                        rewrite(old_conn, new_conn)
                        done = False
                    elif a_val == True:
                        # Rewite to eliminate the Const:
                        new_wires[Connection(comp, "a", 0)] = b_src
                        done = False
                    elif b_val == True:
                        # Rewite to eliminate the Const:
                        new_wires[Connection(comp, "b", 0)] = a_src
                        done = False
                    elif a_src == b_src:
                        if isinstance(a_src.comp, Nand):
                            src_a_src = new_wires[Connection(a_src.comp, "a", 0)]
                            src_b_src = new_wires[Connection(a_src.comp, "b", 0)]
                            if src_a_src == src_b_src:
                                # Remove this Nand and rewrite its output as src's src:
                                del new_wires[Connection(comp, "a", 0)]
                                del new_wires[Connection(comp, "b", 0)]
                                old_conn = Connection(comp, "out", 0)
                                new_conn = src_a_src
                                rewrite(old_conn, new_conn)
                                # TODO: remove a_src.comp if not referenced?
                                done = False

        ic.wires = new_wires

        return ic.flatten()  # HACK: a cheap way to remove dangling wires


    def synthesize(self):
        """Compile the chip down to traces and ops for evaluation.

        Returns a NandVector.
        """
        return self.flatten().simplify()._synthesize()

    def _synthesize(self):
        # check for missing wires?
        # check for unused components?

        all_comps = self.sorted_components()
        def by_component(conn):
            if conn.comp == self.root:
                num = -1  # inputs first 
            elif conn.comp in all_comps:
                num = all_comps.index(conn.comp)
            else:
                num = -2
            return (num, conn.name, conn.bit)                

        # Assign a bit for each output connection:
        all_bits = {}
        all_bits[clock] = 0  # TODO: only if it's used somewhere?
        next_bit = 1
        for conn in sorted(set(self.wires.values()), key=by_component):
            if conn != clock:
                all_bits[conn] = next_bit
                next_bit += 1
        
        # Construct map of IC inputs, directly from all_bits:
        inputs = {
            (name, bit): 1 << all_bits[Connection(self.root, name, bit)]
            for name, bits in self._inputs.items()
            for bit in range(bits)  # TODO: None if single bit?
        }
        
        inputs[("common.clock", 0)] = 1 << all_bits[clock]  # HACK

        # Construct map of IC ouputs, mapped to all_bits via wires:
        outputs = {
            (name, bit): 1 << all_bits[self.wires[Connection(self.root, name, bit)]]
            for name, bits in self._outputs.items()
            for bit in range(bits)  # TODO: None if single bit?
        }

        internal = {}  # TODO

        # Construct a map of the traces for each single component, and ask it for its ops:
        initialize_ops = []
        combine_ops = []
        sequence_ops = []
        for comp in self.sorted_components():
            traces = {}
            for name, bits in comp.inputs().items():
                traces[name] = [1 << all_bits[self.wires[Connection(comp, name, bit)]] for bit in range(bits)]
            for name, bits in comp.outputs().items():
                traces[name] = [1 << all_bits[Connection(comp, name, bit)] for bit in range(bits)]
            initialize_ops += comp.initialize(**traces)
            combine_ops += comp.combine(**traces)
            sequence_ops += comp.sequence(**traces)

        return NandVector(inputs, outputs, internal, initialize_ops, combine_ops, sequence_ops)


    def __str__(self):
        """A multi-line summary of all the wiring."""
        # Sort wires by topological order of the "from" component, then name, then the "to" component and name.
        
        # TODO: render components in order, one per line, with neatly summarized inputs and outputs.
        
        all_comps = self.sorted_components()
        def to_index(c, root):
            if c == self.root:
                return root
            elif c not in all_comps:
                # Note: this can happen due to, say, a bug in flattening, and it's easier to debug if
                # str() stillworks in that case.
                return root*2  # even before/after inputs/outputs
            else:
                return all_comps.index(c)
        def by_component(t):
            # Sometimes it's interesting to see the wires by source:
            # return (to_index(t[1].comp, -1), t[1].name, to_index(t[0].comp, 1000), t[0].name)
            return (to_index(t[0].comp, 1000), t[0].name, to_index(t[1].comp, -1), t[1].name)
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

        ins = ', '.join(f"{name}[{bits}]" for name, bits in self.inputs().items())
        outs = ', '.join(f"{name}[{bits}]" for name, bits in self.outputs().items())
        return '\n'.join(
            [f"{self.label}({ins}; {outs}):"] +
            [ f"  {self._connection_label(from_output, all_comps):16s} -> {self._connection_label(to_input, all_comps):16s}{back_edge_label(from_output.comp, to_input.comp)}"
              for to_input, from_output in sorted(self.wires.items(), key=by_component)
            ])

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
    """Pseudo-component providing access to an IC's inputs and outputs (under the opposite names).
    """

    def __init__(self, ic):
        self.ic = ic

    def inputs(self):
        return self.ic.outputs()

    def outputs(self):
        return self.ic.inputs()


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
