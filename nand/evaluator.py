"""A low-level, precise evaluator, which can simulate _any_ IC based on Nand gates, as well as any 
custom component which can express its behavior in terms of updating bits in a state vector. 

This simulation allows all the components of the Nand2Tetris course to be designed and tested,
without relying on any pre-defined components. However, very large chips such as large RAMs 
constructed from Nands or even DFFs are too slow to simulate directly, so predefined ROM and RAM
components are provided instead for use in the full CPU/Computer.

Getting this level of performance out of such a low-level simulation, in Python, is a bit of a feat,
so there's a lot of low-level bit slicing tricks being employed here. Compare with the much simpler, 
faster, but more limited simulator in codegen.py.
"""

from nand.component import Nand, Const, DFF, RAM, ROM, Input
from nand.integration import Connection, root, clock

def synthesize(ic):
    """Compile the chip down to traces and ops for evaluation.

    Returns a NandVector.
    """
    ic = ic.flatten()
            
    # TODO: check for missing wires?
    # TODO: check for unused components?

    any_clock_references = any([True for conn in ic.wires.values() if conn == clock])

    # Assign a bit for each output connection:
    all_bits = {}
    next_bit = 0
    if any_clock_references:
        all_bits[clock] = next_bit
        next_bit += 1
        
    for conn in sorted(set(ic.wires.values()), key=ic._connections_sort_key()):
        if conn != clock:
            all_bits[conn] = next_bit
            next_bit += 1
    
    # Construct map of IC inputs, directly from all_bits:
    inputs = {
        (name, bit): 1 << all_bits[Connection(root, name, bit)]
        for name, bits in ic._inputs.items()
        for bit in range(bits)
    }
    
    if any_clock_references:
        inputs[("common.clock", 0)] = 1 << all_bits[clock]

    # Construct map of IC ouputs, mapped to all_bits via wires:
    outputs = {
        (name, bit): 1 << all_bits[ic.wires[Connection(root, name, bit)]]
        for name, bits in ic._outputs.items()
        for bit in range(bits)
    }

    internal = {}  # TODO

    sorted_comps = ic.sorted_components()

    # For each component, construct a map of its traces' bit masks, and ask the component for its ops:
    initialize_ops = []
    combine_ops = []
    sequence_ops = []
    for comp in sorted_comps:
        traces = {}
        for name, bits in comp.inputs().items():
            traces[name] = [1 << all_bits[ic.wires[Connection(comp, name, bit)]] for bit in range(bits)]
        for name, bits in comp.outputs().items():
            traces[name] = [1 << all_bits[Connection(comp, name, bit)] for bit in range(bits)]
        ops = component_ops(comp)
        initialize_ops += ops.initialize(**traces)
        combine_ops += ops.combine(**traces)
        sequence_ops += ops.sequence(**traces)

    back_edge_from_components = set()
    for to_input, from_output in ic.wires.items():
        if (not isinstance(from_output.comp, Const)
            and from_output.comp in sorted_comps
            and to_input.comp in sorted_comps
            and not isinstance(from_output.comp, DFF)
            and sorted_comps.index(from_output.comp) > sorted_comps.index(to_input.comp)):
            back_edge_from_components.add(from_output.comp)
    non_back_edge_mask = 0
    for conn, bit in all_bits.items():
        if conn.comp not in back_edge_from_components:
            non_back_edge_mask |= 1 << bit

    return NandVector(inputs, outputs, internal, initialize_ops, combine_ops, sequence_ops, non_back_edge_mask)

    
def component_ops(comp):
    if isinstance(comp, Nand):
        return NandOps()
    elif isinstance(comp, Const):
        return ConstOps(comp)
    elif isinstance(comp, DFF):
        return DFFOps()
    elif isinstance(comp, ROM):
        return ROMOps(comp)
    elif isinstance(comp, RAM):
        return RAMOps(comp)
    elif isinstance(comp, Input):
        return InputOps()
    else:
        raise Exception(f"unrecognized component: {comp}")


class VectorOps:
    def initialize(self, **trace_map):
        """Stage 1: set non-zero initial values.
        """
        return []
        
    def combine(self, **trace_map):
        """Stage 2: define combinational logic, as operations which are performed on the chip's traces
        to propagate signals.

        Given a map of input and output refs to traces, return a list of operations which update
        the output traces.
        """
        return []

    def sequence(self, **trace_map):
        """Stage 3: define sequential logic, as operations which are performed on the chip's traces
        at the falling edge of the clock signal.

        Given a map of input and output refs to traces, return a list of operations which update
        the output traces.
        """
        return []

    # def has_combine_ops(self):
    #     """True if the component _ever_ updates any output in combinational fashion (as most do).
    #     False only for components which only ever latch inputs and update their outputs during
    #     flop/sequence.
    #
    #     This is useful for determining evaluation order: non-combinational components can be evaluated
    #     later, which can help to break cycles (the same cycles that these components tend to
    #     participate in.)
    #
    #     Current theory is that this only really needs to work for DFFs. Note that RAM, despite
    #     having both combinational and sequential behavior, actually treats its one output as
    #     combinational. However, if someone decides to implement a 16-bit Register with a purely
    #     latched output, this will handle that.
    #     """
    #
    #     trace_map = {
    #         name: [0]*bits
    #         for (name, bits) in itertools.chain(self.inputs().items(), self.outputs().items())
    #     }
    #     return len(self.combine(**trace_map)) > 0


class NandOps(VectorOps):
    def combine(self, a, b, out):
        assert len(a) == 1 and len(b) == 1 and len(out) == 1
        return [nand_op(a[0], b[0], out[0])]

class ConstOps(VectorOps):
    def __init__(self, comp):
        self.comp = comp

    def initialize(self, out):
        assert len(out) == self.comp.bits
        def f(traces):
            return set_multiple_traces(out, self.value, traces)
        return [custom_op(f)]

class DFFOps(VectorOps):
    def sequence(self, in_, out):
        assert len(in_) == 1 and len(out) == 1
        def flop(traces):
            val = tst_trace(in_[0], traces)
            return set_trace(out[0], val, traces)
        return [custom_op(flop)]

class ROMOps(VectorOps):
    def __init__(self, comp):
        self.comp = comp

    def combine(self, address, out):
        assert len(address) == self.comp.address_bits and len(out) == 16
        def read(traces):
            address_val = get_multiple_traces(address, traces)
            if address_val < len(self.storage):
                out_val = self.storage[address_val]
            else:
                out_val = 0
            return set_multiple_traces(out, out_val, traces)
        return [custom_op(read)]

class RAMOps(VectorOps):
    def __init__(self, comp):
        self.comp = comp

    def combine(self, address, out, **_unused):
        """Note: only using one of the inputs."""
        assert len(address) == self.comp.address_bits and len(out) == 16
        def read(traces):
            address_val = get_multiple_traces(address, traces)
            out_val = self.get(address_val)
            return set_multiple_traces(out, out_val, traces)
        return [custom_op(read)]

    def sequence(self, in_, load, address, **_unused):
        """Note: not using `out`."""
        assert len(in_) == 16 and len(load) == 1 and len(address) == self.comp.address_bits
        def write(traces):
            load_val = tst_trace(load[0], traces)
            if load_val:
                in_val = get_multiple_traces(in_, traces)
                address_val = get_multiple_traces(address, traces)
                self.set(address_val, in_val)
            return traces
        return [custom_op(write)]

class InputOps(VectorOps):
    def combine(self, out):
        assert len(out) == 16
        def read(traces):
            return set_multiple_traces(out, self.value, traces)
        return [custom_op(read)]


class NandVector:
    """Tracks the true/false state of each of a set of bits, related by a sequence of Nand ops.

    Each value is represented as a single bit in a vector represented as an `int`.

    `inputs` maps the name/id of each input to a bit vector which is the location of the
    corresponding bit. `outputs` and `internal` have the same structure. Typically the three
    sets of bits are disjoint, but that's not strictly required.

    `ops` is a list of tuples (in_bits, out_bit). When any input changes, each op is applied in
    sequence (via `_nand_bits`), with just three bit-wise operations on the ints. In case there are
    any out-of-order or circular dependencies, the entire loop is repeated until no more changes are
    seen (or, if no fixed-point is found, an exception is raised.)
    
    `non_back_edge_mask` identifies bits which are known to be consumed only by "normal" references, 
    for which all updates are always seen in a single evaluation pass. If an evaluation pass only 
    changes bits which are in this mask, then evaluation is complete. If not, need to do another pass
    to propagate changes for reference cycles. The default, 0, is never wrong, but using it means 
    an extra evaluation pass each time to check for any change, with the last pass always making 
    no change (and therefore, just a waste.)
    """

    def __init__(self, inputs, outputs, internal, initialize_ops, combine_ops, sequence_ops, non_back_edge_mask=0):
        self.inputs = inputs
        self.outputs = outputs
        self.internal = internal
        self.combine_ops = combine_ops
        self.sequence_ops = sequence_ops
        self.non_back_edge_mask = non_back_edge_mask

        traces = 0
        for op in initialize_ops:
            traces = run_op(op, traces)
        self.traces = traces
        
        self.dirty = True

    def set(self, key, value):
        """Set the value of an input bit identified by key (found in `inputs`).
        """

        if value:
            self.traces |= self.inputs[key]
        else:
            self.traces &= ~self.inputs[key]
        self.dirty = True

    def get(self, key):
        """Get the value of an output bit identified by key (found in `outputs`).
        """

        self._propagate()

        return bool(self.traces & self.outputs[key])

    def get_internal(self, key):
        """Get the value of an internal bit identified by key (found in `internal`).
        """

        self._propagate()

        return bool(self.traces & self.internal[key])

    def _propagate(self):
        if not self.dirty: return

        def f(ts):
            for op in self.combine_ops:
                # ts = run_op(op, ts)

                # Warning: this is just 'run_op', inlined into the loop here to avoid a function
                # call and to make use of possibly more efficient "in-place" operations. Eliminating
                # that function call is good for ~20% speedup.
                if op[0] is None:
                    ts = op[1](ts)
                else:
                    in_mask, out_mask = op
                    if ts & in_mask == in_mask:
                        ts &= ~out_mask
                    else:
                        ts |= out_mask
            return ts

        # FIXME: the number of repeats here increased to 3 for the full CPU with the first 
        # runtime, then increased to 5 when it was re-implemented. That suggests that the
        # sorting of components is not quite right. If anything, now that all the gates are
        # flattened the sort should be more effective.
        limit = 4
        for i in range(limit):
            previous = self.traces
            self.traces = f(self.traces)
            if self.traces == previous:
                break
            changed = self.traces ^ previous
            if changed & ~self.non_back_edge_mask == 0:
                break
        else:
            raise Exception(f"state did not settle after {limit} loops")

        self.dirty = False


    # TODO: unify this with the state of the clock (not otherwise known here at present)
    def _flop(self):
        """Simulate advancing the clock, by copying the input of each flip-flop to its output,
        or whatever else the component needs to make happen.
        """
        
        self._propagate()
        
        for op in self.sequence_ops:
            self.traces = run_op(op, self.traces)

        self.dirty = True


def extend_sign(x):
    """Extend the sign of the low-16 bits of a value to the full width.
    """
    if x & 0x8000 != 0:
        return (-1 & ~0xffff) | x
    else:
        return x


def unsigned(x):
    """Extend the low 16-bits of an unsigned value to the full width, without sign extension.
    """
    return x & 0xffff


def tst_trace(mask, traces):
    return traces & mask != 0

def set_trace(mask, value, traces):
    if value:
        return traces | mask
    else:
        return traces & ~mask

def get_multiple_traces(masks, traces):
    val = 0
    for bit in reversed(masks):
        val = (val << 1) | int(tst_trace(bit, traces))
    return val

def set_multiple_traces(masks, value, traces):
    for bit in masks:
        traces = set_trace(bit, value & 0b1, traces)
        value >>= 1
    return traces


def run_op(op, traces):
    """Execute an op, which was constructed by either nand_op or custom_op, to update traces."""
    if op[0] is None:
        return op[1](traces)
    else:
        in_mask, out_mask = op
        if traces & in_mask == in_mask:
            return traces & ~out_mask
        else:
            return traces | out_mask


def nand_op(a_mask, b_mask, out_mask):
    """Combine two tests into one mask/compare operation for the common case of Nand."""

    # in_mask = a_mask | b_mask
    # def nand(traces):
    #     """Note: this is _the_ hot function, taking ~2/3 of the time during simulation.
    #     Probably could make it even cheaper by returning just the masks and letting the
    #     evaluator's loop do the work itself instead of dispatching to a separate function
    #     for each op.
    #     """
    #     if traces & in_mask == in_mask:
    #         return traces & ~out_mask
    #     else:
    #         return traces | out_mask
    # return nand

    # Just wrap up the two masks
    return (a_mask | b_mask, out_mask)


def custom_op(f):
    """Wrap a non-Nand op to be executed during simulation."""

    # return f

    # Wrap the function with a semaphore value to indicate it's not Nand
    return (None, f)
