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

    def __init__(self, inputs, outputs, internal, ops, flip_flops):
        self.inputs = inputs
        self.outputs = outputs
        self.internal = internal
        self.ops = ops
        self.flip_flops = flip_flops

        self.traces = 0
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
            for (in_bits, out_bit) in self.ops:
                ts = nand_bits(in_bits, out_bit, ts)
            return ts

        self.traces = fixed_point(f, self.traces, limit=2)

        self.dirty = False


    # TODO: unify this with the state of the clock (not otherwise known here at present)
    def _flop(self):
        """Simulate advancing the clock, by copying the input of each flip-flop to its output.
        """
        
        self._propagate()
        
        for in_bit, out_bit in self.flip_flops:
            self.traces = copy_bit(in_bit, out_bit, self.traces)


def nand_bits(in_bits, out_bits, traces):
    """Apply NAND to the bits identified in `in_bits`, and store the result in the bit(s) identified
    in `out_bits`.

    If _all_ of the bits which are 1 in `in_bits` are also 1 in `traces`, then the result is `traces`,
    modified so that all the bits of `out_bits` are cleared (i.e. "not-and"). Otherwise, those same
    bits are set.
    """
    if (traces & in_bits) == in_bits:
        return traces & ~out_bits
    else:
        return traces | out_bits


def copy_bit(in_bit, out_bit, traces):
    """Copy a single bit located at in_bit to out_bit. Actually, this is complementary to nand_bits (i.e. 
    and_bits), but here it's used in a different way.
    """
    if traces & in_bit == in_bit:
        return traces | out_bit
    else:
        return traces & ~out_bit
    

def fixed_point(f, x, limit=50):
    for i in range(limit):
        tmp = f(x)
        if tmp == x:
            # raise Exception(f"iterations: {i}")
            # print(f"iterations: {i}")
            return x
        else:
            x = tmp
    else:
        raise Exception(f"state did not settle after {limit} loops")


