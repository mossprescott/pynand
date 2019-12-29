"""Components which can be combined into a graph to define a complete chip.
"""

class Component:
    """Defines the interface for a component, including what traces it reads and writes, and when."""

    def inputs(self):
        """Dictionary of named input signals, and the number of bits for each.

        Note: the keys must be distinct from the keys of outputs().
        """
        raise NotImplementedError

    def outputs(self):
        """Dictionary of named output signals, and the number of bits for each. A trace will be
        allocated for each bit.

        Note: the keys must be distinct from the keys of inputs().
        """
        raise NotImplementedError

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


class Const(Component):
    """Mostly fictional component which just supplies a constant value. No runtime cost. 
    """
    
    def __init__(self, value):
        self.value = value
    
    def inputs(self):
        return {}
        
    def outputs(self):
        return {"out": 1}
    
    def initialize(self, out):
        assert len(out) == 1
        def f(traces):
            return set_trace(out[0], self.value, traces)
        return [f]

    
class Nand(Component):
    """A single nand gate, which has two inputs and a single output named 'out'."""

    def inputs(self):
        return {"a": 1, "b": 1}

    def outputs(self):
        return {"out": 1}

    def combine(self, a, b, out):
        assert len(a) == 1 and len(b) == 1 and len(out) == 1
        def nand(traces):
            a_val = tst_trace(a[0], traces)
            b_val = tst_trace(b[0], traces)
            out_val = not (a_val and b_val)
            return set_trace(out[0], out_val, traces)
        return [nand]


class DFF(Component):
    """Single-bit "dynamic" flip-flop, which latches its input, presenting it on the output
    during the next clock cycle.
    """

    def inputs(self):
        return {"in_": 1}

    def outputs(self):
        return {"out": 1}

    def sequence(self, in_, out):
        assert len(in_) == 1 and len(out) == 1
        def flop(traces):
            val = tst_trace(in_[0], traces)
            return set_trace(out[0], val, traces)
        return [flop]


class ROM(Component):
    """Read-only memory containing 2^address_bits words (16 bits each) which can be read but
    not written by the chip.

    The entire contents can be over-written from outside when initializing the assembled chip
    (so, really it's an EEPROM.)
    """

    def __init__(self, address_bits):
        self.address_bits = address_bits
        self.storage = []

    def program(self, words):
        """Replace the contents of the ROM with the provided words. Any leftover address space is
        effectively filled with zero values."""
        self.storage = list(words)

    def inputs(self):
        return {"address": self.address_bits}

    def outputs(self):
        return {"out": 16}

    def combine(self, address, out):
        assert len(address) == self.address_bits and len(out) == 16
        def read(traces):
            address_val = get_multiple_traces(address, traces)
            if address_val < len(self.storage):
                out_val = self.storage[address_val]
            else:
                out_val = 0
            return set_multiple_traces(out, out_val, traces)
        return [read]

class RAM(Component):
    """Memory containing 2^n words which can be read and written by the chip.
    """
    def __init__(self, address_bits):
        self.address_bits = address_bits
        self.storage = [0]*(2**self.address_bits)

    def get(self, address):
        """Peek at the value in a single cell."""
        return self.storage[address]

    def set(self, address, value):
        """Poke a value into a single cell.

        TODO: keep track of which cells are updated, for efficient updates when used as the
        screen buffer?
        """
        self.storage[address] = value

    def inputs(self):
        return {"in_": 16, "load": 1, "address": self.address_bits}

    def outputs(self):
        return {"out": 16}

    def combine(self, address, out, **_unused):
        """Note: only using one of the inputs."""
        assert len(address) == self.address_bits and len(out) == 16
        def read(traces):
            address_val = get_multiple_traces(address, traces)
            out_val = self.get(address_val)
            return set_multiple_traces(out, out_val, traces)
        return [read]

    def sequence(self, in_, load, address, **_unused):
        """Note: not using `out`."""
        assert len(in_) == 16 and len(load) == 1 and len(address) == self.address_bits
        def write(traces):
            load_val = tst_trace(load[0], traces)
            if load_val:
                in_val = get_multiple_traces(in_, traces)
                address_val = get_multiple_traces(address, traces)
                self.set(address_val, in_val)
        return [write]


class Input(Component):
    """Single-word device which presents some input from outside the computer.
    """

    def __init__(self):
        self.value = 0

    def set(self, value):
        """Provide the value that will appear at the output."""
        self.value = value

    def inputs(self):
        return {}

    def outputs(self):
        return {"out": 16}

    def combine(self, out):
        assert len(out) == 16
        def read(traces):
            return set_multiple_traces(out, self.value, traces)
        return [read]


# TODO: Output, (potentially) accepting one word of output on each clock cycle?
