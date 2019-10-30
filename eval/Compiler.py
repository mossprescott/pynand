# TODO: what to call this module?

from eval.Nand import NandInstance, InputRef, _sorted_nodes, INPUT_INSTANCE
from eval.NandVector import NandVector

class NandVectorWrapper:
    def __init__(self, vector):
        self._vector = vector
        
    def __setattr__(self, name, value):
        """Set the value of an input."""
        # TODO: handle multi-bit inputs
        if name == '_vector': return object.__setattr__(self, name, value)
 
        self._vector.set_input(name, value)

    def __getattr__(self, name):
        """Get the value of an input or output."""
        
        # TODO: handle multi-bit inputs/outputs
        return self._vector.get_output(name)


def component_to_vector(comp):
    """Compile a component to a NandVector.
    
    1) assign each input and the output of each Nand gate to a unique bit
    2) map each of the component's outputs to the output of some Nand gate
    3) construct the op for each Nand gate, in the correct sequence.
    """
    
    inst = comp()
    
    seq = 1
    def next_bit():
        nonlocal seq
        tmp = seq
        seq <<= 1
        return tmp
    
    internal = {}

    # first allocate a bit for each input:
    inputs = {}
    for n in inst.input_names():
        inputs[n] = next_bit()
        internal[InputRef(INPUT_INSTANCE, n)] = inputs[n]
    # print(f"inputs: {inputs}")
    # print(f"   ...: {internal}")
    
    # now allocate a bit for the output of each nand gate:
    for r in _sorted_nodes(inst):
        if isinstance(r, NandInstance):
            # print(f"r: {r}")
            # print(f"  a: {r.a}")
            # print(f"  b: {r.b}")
            internal[InputRef(r, 'out')] = next_bit()
    # print(f"nands: {internal}")

    # map other component's outputs to nand outputs, transitively
    for r in _sorted_nodes(inst):
        if not isinstance(r, NandInstance):
            for name, ref in r.args.items():
                internal[InputRef(r, name)] = internal[ref]
            for (name, bit), ref in r.outputs.dict.items(): 
                internal[InputRef(r, name, bit)] = internal[ref]
    # print(f"all: {internal}")
    
    # extract output assignments:
    outputs = {}
    for (pred_name, pred_index), pred_ref in inst.outputs.dict.items():
        outputs[pred_name] = internal[pred_ref]
    # print(f"outputs: {outputs}")
    
    # finally, construct an op for each nand:
    ops = []
    for r in _sorted_nodes(inst):
        if isinstance(r, NandInstance):
            # print(f"r: {r}")
            # print(f"  a: {r.a}")
            # print(f"  b: {r.b}")
            in_bits = internal[r.a] | internal[r.b] 
            out_bit = internal[InputRef(r, "out")]
            ops.append((in_bits, out_bit))
    
    return NandVector(inputs, outputs, ops)
    
def eval_fast(comp, **args):
    nv = component_to_vector(comp)

    for name, value in args.items():
        nv.set_input(name, value)

    return NandVectorWrapper(nv)
