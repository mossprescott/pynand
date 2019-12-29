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

        self.traces = fixed_point(f, self.traces, limit=3)  # HACK: 2 just checks the first pass was stable. 

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
