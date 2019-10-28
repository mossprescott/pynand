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

class Inputs:
    def __init__(self, inst):
        self.inst = inst

    def __getattr__(self, name):
        """Called when the builder asks for an input to hand to an internal component."""
        # Tricky: need to be able to return (not fail) when called without args since we use this
        # to construct a bogus instance for counting gates, etc. But returning None is a terrible
        # idea the rest of the time.
        return self.inst.args.get(name, MISSING_NODE)

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

MISSING_NODE = InputRef('missing', 'missing')

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
        self.args = args  # add...?
        self.seq = NODE_SEQ.next()

        inputs = Inputs(self)
        self.outputs = Outputs(self)

        self.comp.builder(inputs, self.outputs)

    def __getattr__(self, name):
        return InputRef(self, name)

    def update_state(self, state):
        """Update outputs found in `state`, based on the inputs found there."""

        # copy outputs:
        for (name, bit), ref in self.outputs.dict.items():
            update_state_bit(state, InputRef(self, name, bit), lookup_state_bit(state, ref))

    def refs(self):
        return set(self.outputs.dict.values())

    def __repr__(self):
        return f"instance{self.seq}"

class NandComponent:
    def __call__(self, a, b):
        return NandInstance(a, b)

class NandInstance:
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.out = InputRef(self, 'out')
        self.seq = NODE_SEQ.next()

    def refs(self):
        return set([self.a, self.b])

    def update_state(self, state):
        a = lookup_state_bit(state, self.a)
        b = lookup_state_bit(state, self.b)

        # meet(rubber, road):
        out = int(not (a and b))

        update_state_bit(state, InputRef(self, 'out'), out)

    def __repr__(self):
        return f"nand{self.seq}"

Nand = NandComponent()


class Const:
    def __init__(self, value):
        self.value = value
        self.inst = self
        
    def refs(self):
        return set()
        
    def update_state(self, state):
        state[(self, None)] = self.value
        
    @property
    def name(self): 
        return None
        
    @property
    def bit(self):
        return None
    
    def __getitem__(self, key):
        if key < 0 or key > 15:
            raise Exception(f"Bit slice out of range: {key}")
        return self
    
    def __repr__(self):
        return f"const({self.value})"

class ResultOutputs:
    def __init__(self, values):
        self.values = values

    def __getattr__(self, name):
        """Called when an output value is requested from the result state."""
        if name != 'values':
            return self.values[name]

    def __repr__(self):
        return str(self.values)

class EnvInstance:
    """Pseudo-instance that the supplied values hang off of."""
    def __init__(self, **args):
        self.seq = NODE_SEQ.next()

    def update_state(self, state):
        pass  # nothing to do

    def refs(self):
        return set()

    def __repr__(self):
        return f"env{self.seq}"

def eval(comp, **args):
    env = EnvInstance()
    inst = comp(**{name: InputRef(env, name) for name in args})
    def zero(): return 0
    state = collections.defaultdict(zero, [((env, name), value) for (name, value) in args.items()])
    prev = state.copy()
    limit = 50
    for i in range(limit):
        for n in _sorted_nodes(inst):
            n.update_state(state)
        if state == prev: break
        prev = state.copy()
    else:
        raise Exception(f"outputs didn't stabilize after {limit} iterations")
        
    def extend_sign(x):
        if x & 0x8000 != 0:
            return (-1 & ~0xffff) | x
        else:
            return x
    return ResultOutputs({name: extend_sign(value) for ((comp, name), value) in state.items() if comp == inst})
    
def gate_count(comp):
    return sum(1 for n in _sorted_nodes(comp()) if isinstance(n, NandInstance))

def delay(self):
    raise NotImplemented()

# TODO: also answer questions about fan-out
# TODO: any other interesting properties?


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
            nodes += [r.inst for r in n.refs() if r.inst != MISSING_NODE.inst]
    visited.reverse()
    return visited

def pprint_state(state):
    return '{\n  ' + '\n  '.join(f"{c}.{n}: {v}" for (c, n), v in state.items()) + '\n}'

def lookup_state_bit(state, ref):
    val = state[(ref.inst, ref.name)]
    if ref.bit is not None:
        return val & (1 << ref.bit) != 0
    else:
        return val

def update_state_bit(state, ref, val):
    if ref.bit is not None:
        if val:
            state[(ref.inst, ref.name)] |= (1 << ref.bit)
        else:
            state[(ref.inst, ref.name)] &= ~(1 << ref.bit)
    else:
        state[(ref.inst, ref.name)] = val