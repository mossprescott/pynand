"""Components which can be combined into a graph to define a complete chip.
"""

import itertools

class Component:
    """Defines the interface for a component, including what traces it reads and writes, and when."""

    def __init__(self):
        self.label = self.__class__.__name__

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


class Const(Component):
    """Mostly fictional component which just supplies a constant value. No runtime cost.
    """

    def __init__(self, bits, value):
        Component.__init__(self)
        self.bits = bits
        self.value = value

    def inputs(self):
        return {}

    def outputs(self):
        return {"out": self.bits}

    def __repr__(self):
        return f"Const({self.bits}, {self.value})"

    def __eq__(self, other):
        return isinstance(other, Const) and self.bits == other.bits and self.value == other.value

    def __hash__(self):
        return hash((self.bits, self.value))


class Nand(Component):
    """A single nand gate, which has two inputs and a single output named 'out'."""

    def inputs(self):
        return {"a": 1, "b": 1}

    def outputs(self):
        return {"out": 1}


class DFF(Component):
    """Single-bit "dynamic" flip-flop, which latches its input, presenting it on the output
    during the next clock cycle.
    """

    def inputs(self):
        return {"in_": 1}

    def outputs(self):
        return {"out": 1}


class ROM(Component):
    """Read-only memory containing 2^address_bits words (16 bits each) which can be read but
    not written by the chip.

    The entire contents can be over-written from outside when initializing the assembled chip
    (so, really it's an EEPROM.)

    Note: this component imposes no timing constraint; you can supply `address` and read the
    corresponding value from `out` without waiting for the next cycle. Not sure how realistic
    that is.
    """

    def __init__(self, address_bits):
        Component.__init__(self)
        self.address_bits = address_bits

    def inputs(self):
        return {"address": self.address_bits}

    def outputs(self):
        return {"out": 16}


class RAM(Component):
    """Memory containing 2^n words which can be read and written by the chip, with fixed
    latency of one cycle for both reads and writes. Throughput is one write and/or read per cycle.

    To read a previously set value, set `address`, wait one cycle, and then
    inspect `out`. This delay is meant to model the inherent trade-off of moving storage off-chip.

    To store a value, set `address` and `load`, wait one cycle, set `in_`, then wait again. The
    value provided in the second cycle is stored at the address provided in the first. That probably
    seems perverse. It turns out to be what you need to usefully read and write in the same cycle.

    For example, to pop from a stack that grows upward:
      A=0     // location of the stack pointer
      AM=M-1  // decrement the stack pointer in memory (read and write address 0)
      D=M     // read from the
    """
    def __init__(self, address_bits):
        Component.__init__(self)
        self.address_bits = address_bits

    def inputs(self):
        return {"in_": 16, "load": 1, "address": self.address_bits}

    def outputs(self):
        return {"out": 16}


class Input(Component):
    """Single-word device which presents some input from outside the computer
    (e.g. the keyboard or terminal.)
    """

    def __init__(self):
        Component.__init__(self)

    def inputs(self):
        return {}

    def outputs(self):
        return {"out": 16}


class Output(Component):
    """Single-word device which allows the computer to write data to some external
    device (e.g. a printer or terminal.)

    Properly, this component has no output, but in order to be added to a chip's
    wiring graph, it needs to have some output, so it provides `ready`, which is
    normally 1, but goes to 0 when a value has been written to the output and
    not yet consumed by whatever external process might be reading it. Note: a new
    value can still be written when the previous value has not been read; it will
    just overwrite it.
    """

    def __init__(self):
        Component.__init__(self)

    def inputs(self):
        return {"in_": 16, "load": 1}

    def outputs(self):
        return {"ready": 1}
