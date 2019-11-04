"""DSL for defining components in the style of Nand to Tetris.

See project_01.py and test_01.py for examples of how to use it. This code uses all sorts of hacks
to try to provide a nice HDL syntax.
"""

import collections

class NodeSeq:
    def __init__(self):
        self.seq = 0

    def next(self):
        tmp, self.seq = self.seq, self.seq+1
        return tmp

NODE_SEQ = NodeSeq()

class Component:
    def __init__(self, builder):
        self.builder = builder

    def __call__(self, **args):
        return Instance(self, **args)
        
    def root(self):
        return RootInstance(self)

class Args:
    def __init__(self, inst):
        self.inst = inst

    def __getattr__(self, name):
        """Called when the builder asks for an input to hand to an internal component."""
        return self.inst.args[name]

class InputRef:
    def __init__(self, inst, name, bit=None):
        self.inst = inst
        self.name = name
        self.bit = bit
        
    def __getitem__(self, key):
        """Called when the builder asks for a bit slice of an input."""
        return InputRef(self.inst, self.name, key)
        
    def __repr__(self):
        if self.bit is not None:
            return f"Ref({self.inst}.{self.name}[{self.bit}])"
        else:
            return f"Ref({self.inst}.{self.name})"
            
    def __eq__(self, other):
        return self.inst == other.inst and self.name == other.name and self.bit == other.bit
        
    def __hash__(self):
        return hash((self.inst, self.name, self.bit))

class Outputs:
    def __init__(self, comp):
        self.comp = comp
        self.dict = {}  # local output name -> child InputRef

    def __setattr__(self, name, value):
        """Called when the builder wires an internal component's output as an output of this component."""
        if name in ('comp', 'dict'):   # hack for initialization-time
            return object.__setattr__(self, name, value)

        # TODO: trap conflicting wiring (including with inputs)
        self.dict[(name, None)] = value
        
    def __getattr__(self, name):
        """Called when the builder is going to assign to a bit slice of an output."""
        return OutputSlice(self, name)

class OutputSlice:
    def __init__(self, outputs, name):
        self.outputs = outputs
        self.name = name
        
    def __setitem__(self, key, value):
        """Value is an int between 0 and 15, or (eventually) a slice object with
        .start and .step on the same interval.
        """
        self.outputs.dict[(self.name, key)] = value
        
    
class Instance:
    def __init__(self, comp, **args):
        self.comp = comp
        self.args = args
        self.seq = NODE_SEQ.next()

        inputs = Args(self)
        self.outputs = Outputs(self)

        comp.builder(inputs, self.outputs)

    def __getattr__(self, name):
        return InputRef(self, name)

    def refs(self):
        return set(self.outputs.dict.values())
        
    def __repr__(self):
        return f"instance{self.seq}"

class RootInstance:
    def __init__(self, comp):
        self.comp = comp

        self.inputs = Inputs(self)
        self.outputs = Outputs(self)
        comp.builder(self.inputs, self.outputs)
        
    # FIXME: copied from Instance
    def refs(self):
        return set(self.outputs.dict.values())

    def __repr__(self):
        return "root"

class Inputs:
    def __init__(self, inst):
        self.inst = inst

    def __getattr__(self, name):
        """Called when the builder asks for an input to hand to an internal component."""
        return InputRef(self.inst, name)
    
class NandComponent:
    def __call__(self, a, b):
        return NandInstance(a, b)

    def root(self):
        return NandRootInstance()

class NandInstance:
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.out = InputRef(self, 'out')
        self.seq = NODE_SEQ.next()

    def refs(self):
        return set([self.a, self.b])
        
    def __repr__(self):
        return f"nand{self.seq}"

class NandRootInstance:
    def __init__(self):
        self.a = InputRef(self, "a")
        self.b = InputRef(self, "b")
        self.outputs = {('out', None): None}
    
    def refs(self):
        return set([InputRef(self, "a"), InputRef(self, "b")])

    def __repr__(self):
        return f"nand"
    

Nand = NandComponent()


class Const:
    def __init__(self, value):
        self.value = value
        self.inst = self
        
    def refs(self):
        return set()
        
    def __getitem__(self, key):
        if key < 0 or key > 15:
            raise Exception(f"Bit slice out of range: {key}")
        return self
    
    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value
        
    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"const({self.value})"

def gate_count(comp):
    return sum(1 for n in _sorted_nodes(comp.root()) if isinstance(n, (NandInstance, NandRootInstance)))

def delay(self):
    raise NotImplemented()
    
# TODO: also answer questions about fan-out
# TODO: any other interesting properties?


def extend_sign(x):
    if x & 0x8000 != 0:
        return (-1 & ~0xffff) | x
    else:
        return x

def unsigned(x):
    return x & 0xffff

def _sorted_nodes(inst):
    """List of unique nodes, in topological order (so that evaluating them once 
    from left to right produces the correct result in the absence of cycles.)
    """
    # Search the node graph:
    nodes = [inst]
    visited = []  # a set would be more efficient but insertion order matters
    while nodes:
        n, nodes = nodes[0], nodes[1:]
        if n not in visited:
            visited.append(n)
            # print(f"n: {n}; {n.refs()}")
            nodes += [r.inst for r in n.refs()]
    visited.reverse()
    return visited
