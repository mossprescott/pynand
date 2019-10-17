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

MISSING_NODE = ('missing', 'missing')

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

class Outputs:
    def __init__(self, comp):
        self.comp = comp
        self.dict = {}  # local outout name -> (child instance, child output name)

    def __setattr__(self, name, value):
        """Called when the builder wires an internal component's output as an output of this component."""
        if name in ('comp', 'dict'):   # hack for initialization-time
            return object.__setattr__(self, name, value)

        # TODO: trap conflicting wiring (including with inputs)
        self.dict[name] = value

class Instance:
    def __init__(self, comp, **args):
        self.comp = comp
        self.args = args  # add...?
        self.seq = NODE_SEQ.next()

        inputs = Inputs(self)
        self.outputs = Outputs(self)

        self.comp.builder(inputs, self.outputs)

    def __getattr__(self, name):
        return (self, name)

    def update_state(self, state):
        """Update outputs found in `state`, based on the inputs found there."""

        # invoke each child:
        for (child, _) in set(self.outputs.dict.values()):
            child.update_state(state)

        # copy outputs:
        for name, ref in self.outputs.dict.items():
            state[(self, name)] = state[ref]

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
        self.out = (self, 'out')
        self.seq = NODE_SEQ.next()

    def refs(self):
        return set([self.a, self.b])

    def update_state(self, state):
        self.a[0].update_state(state)
        self.b[0].update_state(state)

        # meet(rubber, road):
        state[(self, 'out')] = int(not (state[self.a] and state[self.b]))

    def __repr__(self):
        return f"nand{self.seq}"

Nand = NandComponent()


class ResultOutputs:
    def __init__(self, values):
        self.values = values

    def __getattr__(self, name):
        """Called when an output value is requested from the result state."""
        if name != 'values':
            return self.values[name]

class EnvInstance:
    """Psuedo-instance that the supplied values hang off of."""
    def __init__(self, **args):
        self.seq = NODE_SEQ.next()

    def update_state(self, state):
        pass  # nothing to do

    def __repr__(self):
        return f"env{self.seq}"

def eval(comp, **args):
    env = EnvInstance()
    inst = comp(**{name: (env, name) for name in args})
    def zero(): return 0
    state = collections.defaultdict(zero, [((env, name), value) for (name, value) in args.items()])
    inst.update_state(state)
    return ResultOutputs({name: value for ((comp, name), value) in state.items() if comp == inst})

def gate_count(comp):
    # Search the node graph:
    inst = comp()
    nodes = [inst]
    visited = set()
    count = 0
    while nodes:
        n, nodes = nodes[0], nodes[1:]
        if n not in visited:
            visited.add(n)
            if isinstance(n, NandInstance):
                count += 1
            nodes += [r[0] for r in n.refs() if r != MISSING_NODE]
    return count

def delay(self):
    raise NotImplemented()

# TODO: also answer questions about fan-out
# TODO: any other interesting properties?


def pprint_state(state):
    return '{' + ', '.join(f"{c}.{n}: {v}" for (c, n), v in state.items()) + '}'
