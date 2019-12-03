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

    def __init__(self, inputs, outputs, internal, ops):
        self.inputs = inputs
        self.outputs = outputs
        self.internal = internal
        self.ops = ops

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
            for op in self.ops:
                ts = op.propagate(ts)
            return ts

        self.traces = fixed_point(f, self.traces, limit=2)

        self.dirty = False


    # TODO: unify this with the state of the clock (not otherwise known here at present)
    def _flop(self):
        """Simulate advancing the clock, by copying the input of each flip-flop to its output.
        """
        
        self._propagate()
        
        for op in self.ops:
            self.traces = op.flop(self.traces)
        self.dirty = True

class VectorOp:
    # TODO: common code around addressing bits?

    def propagate(self, traces):
        """Update output bits based on the current values of input bits, taking a complete set of 
        traces and returning a new set of values for all traces.
        """
        return traces

    def flop(self, traces):
        """Update output bits which respond to the falling edge of the clock signal, taking a 
        complete set of traces and returning a new set of values for all traces.
        """
        return traces


class NandOp(VectorOp):
    """Implements the simplest component: a Nand gate. The single output is updated from inputs,
    and 
    """

    def __init__(self, in_bits, out_bit):
        self.in_bits = in_bits
        self.out_bit = out_bit

    def propagate(self, traces):
        """Apply NAND to the bits identified in `in_bits`, and store the result in the bit(s)
        identified in `out_bits`.

        If _all_ of the bits which are 1 in `in_bits` are also 1 in `traces`, then the result
        is `traces`, modified so that all the bits of `out_bits` are cleared (i.e. "not-and").
        Otherwise, those same bits are set.
        """
        if (traces & self.in_bits) == self.in_bits:
            return traces & ~self.out_bit
        else:
            return traces | self.out_bit
            
    def __eq__(self, other):
        return isinstance(other, NandOp) and self.in_bits == other.in_bits and self.out_bit == other.out_bit

    def __repr__(self):
        return f"NandOp({self.in_bits}, {self.out_bit})"

class DynamicDFFOp(VectorOp):
    def __init__(self, in_bit, out_bit):
        self.in_bit = in_bit
        self.out_bit = out_bit
        
    def flop(self, traces):
        """Copy a single bit located at in_bit to out_bit. Called on the falling edge of the clock.
        """
        if traces & self.in_bit == self.in_bit:
            return traces | self.out_bit
        else:
            return traces & ~self.out_bit

    def __eq__(self, other):
        return isinstance(other, DynamicDFFOp) and self.in_bit == other.in_bit and self.out_bit == other.out_bit

    def __repr__(self):
        return f"DynamicDFFOp({self.in_bit}, {self.out_bit})"


class MemoryOp(VectorOp):
    """Manages the memory's storage and also implements its update ops. Terrible idea?
    """
    
    def __init__(self, in_bit_array, load_bit, address_bit_array, out_bit_array):
        self.in_bit_array = in_bit_array
        self.load_bit = load_bit
        self.address_bit_array = address_bit_array
        self.out_bit_array = out_bit_array

        self.storage = [0] * (2**len(address_bit_array))
    
    def propagate(self, traces):
        """Retrieve the appropriate value from off-chip and update the `out` traces.
        """
        addr = self._from_bits(self.address_bit_array, traces)
        return self._update_bits(self.out_bit_array, traces, self.storage[addr])
        
    def flop(self, traces):
        """Update the state held in this object, if the `load` trace is asserted.
        No changes are made to the chip's traces.
        """
        
        if traces & self.load_bit != 0:
            addr = self._from_bits(self.address_bit_array, traces)
            in_ = self._from_bits(self.in_bit_array, traces)
            self.storage[addr] = in_

        return traces
            
    def _from_bits(self, bits, traces):
        """Extract a multiple-bit value from traces, where each bit is identified by the mask 
        in the corresponding position in bits.
        """
        
        val = 0
        for bit in reversed(bits):
            val <<= 1
            if traces & bit != 0:
                val |= 0b1
        return val

    def _update_bits(self, bits, traces, val):
        """Update the traces """
        for bit in bits:
            if val & 0b1 == 0:
                traces &= ~bit
            else:
                traces |= bit
            val >>= 1
        return traces

    def __eq__(self, other):
        return (isinstance(other, MemoryOp) 
            and self.in_bit_array == other.in_bit_array 
            and self.load_bit == other.load_bit
            and self.address_bit_array == other.address_bit_array
            and self.out_bit_array == other.out_bit_array)

    def __repr__(self):
        return f"MemoryOp(in: {self.in_bit_array}, load: {self.load_bit}, address: {self.address_bit_array}, out: {self.out_bit_array})"


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


