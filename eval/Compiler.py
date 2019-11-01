# TODO: what to call this module?

from eval.Nand import InputRef, Instance, NandInstance, NandRootInstance, RootInstance, _sorted_nodes, INPUT_INSTANCE
from eval.NandVector import NandVector

class NandVectorWrapper:
    def __init__(self, vector):
        self._vector = vector
        
    def __setattr__(self, name, value):
        """Set the value of an input."""
        if name == '_vector': return object.__setattr__(self, name, value)
        
        if (name, None) in self._vector.inputs:
            self._vector.set_input((name, None), value)
        for i in range(16):
            if (name, i) in self._vector.inputs:
                self._vector.set_input((name, i), bool(value & (1 << i)))

    def __getattr__(self, name):
        """Get the value of an input or output."""

        if (name, None) in self._vector.outputs:
            return self._vector.get_output((name, None))
        else:
            tmp = 0
            for i in range(16):
                if (name, i) in self._vector.outputs and self._vector.get_output((name, i)):
                    tmp |= 1 << i
            return tmp

    def __repr__(self):
        return str(dict([(name, self.__getattr__(name)) for (name, _) in self._vector.outputs.keys()]))

def component_to_vector(comp):
    """Compile a component to a NandVector.
    
    1) assign each input and the output of each Nand gate to a unique bit
    2) map each of the component's outputs to the output of some Nand gate
    3) construct the op for each Nand gate, in the correct sequence.
    """
    
    inst = comp.root()
    
    seq = 1
    def next_bit():
        nonlocal seq
        tmp = seq
        seq <<= 1
        return tmp
    
    internal = {}

    input_refs = set([
        ref
        for n in _sorted_nodes(inst)
        for ref in n.refs()
        if ref.inst == inst
    ])
    # print(f"input_refs: {input_refs}")

    # first allocate a bit for each input:
    inputs = {}
    for ref in input_refs:
        inputs[(ref.name, ref.bit)] = internal[ref] = next_bit()
    # print(f"inputs: {inputs}")
    # print(f"   ...: {internal}")
    
    # now allocate a bit for the output of each nand gate:
    for r in _sorted_nodes(inst):
        if isinstance(r, (NandInstance, NandRootInstance)):
            # print(f"r: {r}")
            # print(f"  a: {r.a}")
            # print(f"  b: {r.b}")
            internal[InputRef(r, 'out')] = next_bit()
    # print(f"nands: {internal}")

    # map other component's outputs to nand outputs, transitively
    for r in _sorted_nodes(inst):
        if isinstance(r, Instance):
            # print(f"inst: {r}; {r.args}")
            for name, ref in r.args.items():
                # print(f"  propagate: {(name, ref)}")
                # propagate a single bit or upt to 16 bits, whichever are present:
                if ref in internal:
                    internal[InputRef(r, name)] = internal[ref]
                for i in range(16):
                    bit_ref = ref[i]
                    if bit_ref in internal:
                        internal[InputRef(r, name, i)] = internal[bit_ref]
            for (name, bit), ref in r.outputs.dict.items(): 
                internal[InputRef(r, name, bit)] = internal[ref]
        elif isinstance(r, RootInstance):
            # print(f"root: {r}")
            # for name, ref in r.args.items():
            #     print(f"  propagate from root: {(name, ref)}")
            # TODO
            pass
    # print(f"all: {internal}")
    
    # extract output assignments:
    outputs = {}
    if isinstance(inst, RootInstance):
        for (pred_name, pred_index), pred_ref in inst.outputs.dict.items():
            # propagate a single bit or upt to 16 bits, whichever are present:
            if pred_ref in internal:
                outputs[(pred_name, pred_index)] = internal[pred_ref]
            if pred_index is None:
                for i in range(16):
                    bit_ref = pred_ref[i]
                    if bit_ref in internal:
                        outputs[(pred_name, i)] = internal[bit_ref]
    elif isinstance(inst, NandRootInstance):
        outputs[("out", None)] = internal[InputRef(inst, "out")]
    # print(f"outputs: {outputs}")
    
    # finally, construct an op for each nand:
    ops = []
    for r in _sorted_nodes(inst):
        if isinstance(r, (NandInstance, NandRootInstance)):
            # print(f"r: {r}")
            # print(f"  a: {r.a}")
            # print(f"  b: {r.b}")
            in_bits = internal[r.a] | internal[r.b] 
            out_bit = internal[InputRef(r, "out")]
            ops.append((in_bits, out_bit))
    
    return NandVector(inputs, outputs, ops)
    
def eval_fast(comp, **args):
    nv = component_to_vector(comp)

    w = NandVectorWrapper(nv)
    for name, value in args.items():
        w.__setattr__(name, value)
    return w
