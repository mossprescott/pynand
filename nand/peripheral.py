"""Components which can be combined into a graph to define a complete chip.
"""

class Component:
    """Defines the interface for a component."""
    
    # def refs(self):
    #     """Set of components """
    
    def outputs(self):
        """Set of Refs for the component's output traces."""
        raise NotImplementedError()
    
    # def wire(self, trace_map):
    #     """Stage 1: connect traces for static logic (connecting components).
    #
    #     Given a map of input refs to traces, return additional mapping of output refs to the same traces.
    #     """
    #
    #     return {}
    
    def combine(self, trace_map):
        """Stage 2: define combinational logic, as operations which are performed on the chip's traces
        to propagate signals.
        
        Given a map of input and output refs to traces, return a list of operations which update 
        the output traces.
        """
        
        return []

    def sequence(self, trace_map):
        """Stage 3: define sequential logic, as operations which are performed on the chip's traces 
        at the falling edge of the clock signal.
        
        Given a map of input and output refs to traces, return a list of operations which update 
        the output traces.
        """
        
        return []
        
    # def _ref(self, name):
    #     """Set of one InputRef for a named output."""
    #     return set([Ref(self, name, 0)])
        
    def _ref16(self, name):
        """Set of 16 InputRefs, one for each bit of a single named output."""
        return set([Ref(self, "out", i) for i in range(16)])


class Ref:
    def __init__(self, comp, name, bit):
        self.comp = comp
        self.name = name
        self.bit = bit

    def __repr__(self):
        return f"Ref({self.comp}, {self.name}, {self.bit})"

    def __eq__(self, other):
        return (isinstance(other, Ref)
            and self.comp == other.comp and self.name == other.name and self.bit == other.bit)

    def __hash__(self):
        return hash((self.comp, self.name, self.bit))

        
class Nand(Component):
    """A single nand gate, which has two inputs and a single output named 'out'"""
    
    def __init__(self, a_ref, b_ref):
        self.a_ref = a_ref
        self.b_ref = b_ref
        self.out_ref = Ref(self, "out", 0)

    def outputs(self):
        return set([self.out_ref])

    def combine(self, trace_map):
        a_mask = trace_map[self.a_ref]
        b_mask = trace_map[self.b_ref]
        out_mask = trace_map[self.out_ref]
        def nand(traces):
            a = traces & a_mask != 0
            b = traces & b_mask != 0
            if not (a and b):
                return traces | out_mask
            else:
                return traces & ~out_mask
        return [nand]


# class Integrated(Component):
#     """'Composite' component which assembles one or more other components, connecting their inputs
#     and outputs.
#     """
#
#     def __init__(self):
#         pass # TODO
#
#     def outputs(self):
#         """An integrated component has no outputs of its own."""
#         return set()
#
#     def wire(self, trace_map):
#         pass


class DFF(Component):
    """Single-bit "dynamic" flip-flop, which latches its input, presenting it on the output 
    during the next clock cycle.
    """
    
    def __init__(self, in_ref):
        self.in_ref = in_ref
        self.out_ref = Ref(self, "out", 0)
    
    def outputs(self):
        return set([self.out_ref])
    
    def sequence(self, trace_map):
        in_mask = trace_map[self.in_ref]
        out_mask = trace_map[self.out_ref]
        def flop(traces):
            in_ = traces & in_mask != 0
            if in_:
                return traces | out_mask
            else:
                return traces & ~out_mask
        return [flop]
        


class ROM(Component):
    """Read-only memory containing 2^n words which can be read but not written by the chip.
    
    The entire contents can be over-written from outside when initializing the assembled chip
    (so, really it's an EEPROM.)
    """
    
    def __init__(self, address_ref):
        self.storage = []
        
    def program(self, words):
        """Replace the contents of the ROM with the provided words. Any leftover address space is 
        effectively filled with zero values."""
        self.storage = list(words)
        
    def outputs(self):
        return self._ref16("out")

    def op(self):
        # TODO: args are the bit masks for each input and output
        # result is the propagate op
        pass
    

class RAM(Component):
    """Memory containing 2^n words which can be read and written by the chip.
    """
    def __init__(self, address):
        self.storage = [0]*(2**self.address_bits)
        
    def get(self, address):
        """Peek at the value in a single cell."""
        return self.storage[address]
        
    def set(self, address, value):
        """Poke a value into a single cell."""
        self.storage[address] = value
        
    def outputs(self):
        return self._ref16("out")

    def op(self):
        # TODO: args are the bit masks for each input and output
        # result is the propagate and flop ops
        pass
    

class Input(Component):
    """Single-word device which presents some input from outside the computer.
    """
    
    def __init__(self):
        self.value = 0
        
    def set(self, value):
        """Provide the value that will appear at the output"""
        self.value = value
        
    def outputs(self):
        return self._ref16("out")
        
    def op(self):
        # TODO: args are the bit masks for each input and output
        # result is the propagate op
        pass
    
    