"""A new evaluator, based on bit vectors."""

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
    """

    def __init__(self, inputs, outputs, internal, combine_ops, sequence_ops, start=0):
        self.inputs = inputs
        self.outputs = outputs
        self.internal = internal
        self.combine_ops = combine_ops
        self.sequence_ops = sequence_ops

        self.traces = start
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
            for f in self.combine_ops:
                ts = f(ts)
            return ts

        # FIXME: the number of repeats here increased to 3 for the full CPU with the first 
        # runtime, then increased to 5 when it was re-implemented. That suggests that the
        # sorting of components is not quite right. If anything, now that all the gates are
        # flattened the sort should be more effective.
        self.traces = fixed_point(f, self.traces, limit=5)

        self.dirty = False


    # TODO: unify this with the state of the clock (not otherwise known here at present)
    def _flop(self):
        """Simulate advancing the clock, by copying the input of each flip-flop to its output.
        """
        
        self._propagate()
        
        for f in self.sequence_ops:
            self.traces = f(self.traces)

        self.dirty = True


def fixed_point(f, x, limit=50):
    for i in range(limit):
        tmp = f(x)
        if tmp == x:
            return x
        else:
            x = tmp
    else:
        raise Exception(f"state did not settle after {limit} loops")


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


def nand_op(a_mask, b_mask, out_mask):
    """Combine two tests into one mask/compare operation for the common case of Nand."""
    in_mask = a_mask | b_mask
    def nand(traces):
        """Note: this is _the_ hot function, taking ~2/3 of the time during simulation.
        Probably could make it even cheaper by returning just the masks and letting the
        evaluator's loop do the work itself instead of dispatching to a separate function
        for each op.
        """
        if traces & in_mask == in_mask:
            return traces & ~out_mask
        else:
            return traces | out_mask
    return nand


def custom_op(f):
    """Wrap a non-Nand op to be executed during simulation."""
    return f