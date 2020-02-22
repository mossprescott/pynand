"""A low-level, precise evaluator, which can simulate _any_ IC based on Nand gates, as well as any 
custom component which can express its behavior in terms of updating bits in a state vector.

This is fast enough for small tests, about 1 kHz, but not fast enough to run large interactive 
programs.

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
from nand.optimize import simplify


def run(ic, optimize = True):
    """Prepare an IC for simulation, returning an object which exposes the inputs and outputs
    as attributes. If the IC is Computer, it also provides access to the ROM, RAM, etc.
    """
    ic = ic.flatten()
    if optimize:
        ic = simplify(ic)
    nv, stateful = synthesize(ic)
    if any(isinstance(c, ROM) for c in ic.sorted_components()):
        w = NandVectorComputerWrapper(nv, stateful)
    else:
        w = NandVectorWrapper(nv)
    return w


def synthesize(ic):
    """Compile the chip down to traces and ops for evaluation.

    Returns a NandVector and a list of stateful components (e.g. RAMs).
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
        if Connection(root, name, bit) in all_bits  # Not all input bits are necessarily connected.
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
    stateful = []
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
        stateful.append(ops)

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

    return NandVector(inputs, outputs, internal, initialize_ops, combine_ops, sequence_ops, non_back_edge_mask), stateful

    
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
        return InputOps(comp)
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
            return set_multiple_traces(out, self.comp.value, traces)
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
        self.storage = []

    def program(self, words):
        """Replace the contents of the ROM with the provided words. Any leftover address space is
        effectively filled with zero values."""
        self.storage = list(words)

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
        self.storage = [0]*(2**comp.address_bits)

    def get(self, address):
        """Peek at the value in a single cell."""
        return self.storage[address]

    def set(self, address, value):
        """Poke a value into a single cell.

        TODO: keep track of which cells are updated, for efficient updates when used as the
        screen buffer?
        """
        self.storage[address] = value

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
    def __init__(self, comp):
        self.comp = comp
        self.value = 0

    def set(self, value):
        """Provide the value that will appear at the output."""
        self.value = value

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


class NandVectorWrapper:
    """Convenient syntax around a NandVector. You get one of these from run(chip).
    """
    
    def __init__(self, vector):
        self._vector = vector
        
    def __setattr__(self, name, value):
        """Set the value of a single- or multiple-bit input."""
        if name.startswith('_'): return object.__setattr__(self, name, value)
        
        if (name, None) in self._vector.inputs:
            self._vector.set((name, None), value)
        for i in range(16):
            if (name, i) in self._vector.inputs:
                self._vector.set((name, i), bool(value & (1 << i)))

    def tick(self):
        """Raise the common `clock` signal (and propagate state changes eagerly)."""
        if ('common.clock', 0) in self._vector.inputs:
            self._vector._propagate()
            self._vector.set(('common.clock', 0), 1)  # TODO: first check that it was low

    def tock(self):
        """Lower the common `clock` signal (and propagate state changes eagerly)."""
        if ('common.clock', 0) in self._vector.inputs:
            self._vector._propagate()
            self._vector.set(('common.clock', 0), 0)  # TODO: first check that it was high
        self._vector._flop()

    def ticktock(self, cycles=1):
        """Raise and then lower the common `clock` signal."""
        for _ in range(cycles):
            self.tick()
            self.tock()

    def __getattr__(self, name):
        """Get the value of a single- or multiple-bit output."""

        if (name, None) in self._vector.outputs:
            return extend_sign(self._vector.get((name, None)))
        else:
            tmp = 0
            for i in range(16):
                if (name, i) in self._vector.outputs and self._vector.get((name, i)):
                    tmp |= 1 << i
            return extend_sign(tmp)

    def get_internal(self, name):
        """Get the value of a single- or multiple-bit signal which is internal to the component."""
        if (name, None) in self._vector.internal:
            return extend_sign(self._vector.get_internal((name, None)))
        else:
            tmp = 0
            for i in range(16):
                if (name, i) in self._vector.internal and self._vector.get_internal((name, i)):
                    tmp |= 1 << i
            return extend_sign(tmp)

    def outputs(self):
        return dict([(name, self.__getattr__(name)) for (name, _) in self._vector.outputs.keys()])

    def internal(self):
        return dict([(name, self.get_internal(name)) for (name, _) in self._vector.internal.keys()])
        
    def components(self, types):
        """List of internal components (e.g. RAM, ROM).
        
        Note: types should be one or more of the types defined in nand.component, not the wrappers
        with the same names defined in this module.
        """
        return [c for c in self._components if isinstance(c, types)]

    def __repr__(self):
        return str(self.outputs())


class NandVectorComputerWrapper(NandVectorWrapper):
    """Wrapper with extra operations for the full Computer."""
    
    def __init__(self, vector, stateful):
        NandVectorWrapper.__init__(self, vector)
        self._stateful = stateful
        self._rom, = [c for c in self._stateful if isinstance(c, ROMOps)]
        self._mem, = [c for c in self._stateful if isinstance(c, RAMOps) and c.comp.address_bits == 14]
        self._screen, = [c for c in self._stateful if isinstance(c, RAMOps) and c.comp.address_bits == 13]
        self._keyboard, = [c for c in self._stateful if isinstance(c, InputOps)]

    def run_program(self, instructions):
        """Install and run a sequence of instructions, stopping when pc runs off the end."""

        self.init_rom(instructions)

        while self.pc <= len(instructions):
            self.ticktock()

    def reset_program(self):
        """Reset pc so the program will run again from the top."""

        self.reset = 1
        self.ticktock()
        self.reset = 0

    def init_rom(self, instructions):
        """Overwrite the top of the ROM with a sequence of instructions.

        If there's any space left over, an two-instruction infinite loop is written immediately
        after the program, which could in theory be used to detect termination.
        """

        size = len(instructions)

        # The ROM size limits the size of program that can run, not to mention, e.g. the format of 
        # instructions used to load jump targets.
        rom_max = 2**self._rom.comp.address_bits
        if size >= rom_max:
            raise Exception(f"Too many instructions: {size:0,d} >= {rom_max:0,d}")
            
        prg = instructions + [
            size,  # @size (which is the address of this instruction)
            0b111_0_000000_000_111,  # JMP
        ]
        self._rom.storage = prg

    def peek(self, address):
        """Read a single word from the Computer's memory."""
        return self._mem.storage[address]

    def poke(self, address, value):
        """Write a single word to the Computer's memory."""
        self._mem.storage[address] = value

    def peek_screen(self, address):
        """Read a value from the display RAM. Address must be between 0x000 and 0x1FFF."""
        return self._screen.storage[address]
    
    def poke_screen(self, address, value):
        """Write a value to the display RAM. Address must be between 0x000 and 0x1FFF."""
        self._screen.storage[address] = value
    
    def set_keydown(self, keycode):
        """Provide the code which identifies a single key which is currently pressed."""
        self._keyboard.value = keycode

    # Tricky: SP might get special treatment in some implementations, so provide a named property
    # that subclasses can override.
    @property
    def sp(self):
        return self.peek(0)
