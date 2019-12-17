"""A compiler from components to the form that can be efficiently evaluated."""

from nand.component import *
from nand.evaluator import NandVector, NandOp, DynamicDFFOp, MemoryOp

class NandVectorWrapper:
    def __init__(self, vector):
        self._vector = vector
        
    def __setattr__(self, name, value):
        """Set the value of a single- or multiple-bit input."""
        if name == '_vector': return object.__setattr__(self, name, value)
        
        if (name, None) in self._vector.inputs:
            self._vector.set((name, None), value)
        for i in range(16):
            if (name, i) in self._vector.inputs:
                self._vector.set((name, i), bool(value & (1 << i)))

    def tick(self):
        """Raise the common `clock` signal (and propagate state changes eagerly)."""
        # self._vector._propagate()  # TODO: overkill?
        self._vector.set(('common.clock', None), 1)  # TODO: first check that it was low
        self._vector._propagate()

    def tock(self):
        """Lower the common `clock` signal (and propagate state changes eagerly)."""
        # self._vector._propagate()  # TODO: overkill?
        self._vector.set(('common.clock', None), 0)  # TODO: first check that it was high
        self._vector._flop()

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

    def __repr__(self):
        return str(self.outputs())


def component_to_vector(comp):
    """Compile a component to a NandVector.
    
    1) assign each input and the output of each Nand gate to a unique bit
    2) map each of the component's outputs to the output of some Nand gate
    3) construct the op for each Nand gate, in the correct sequence.
    """
    
    inst = comp.root()
    
    seq = 2  # Note: the lowest bit is reserved for the constant 1
    def next_bit():
        nonlocal seq
        tmp = seq
        seq <<= 1
        return tmp
    
    all_bits = {}

    input_refs = set([
        ref
        for n in sorted_nodes(inst)
        for ref in n.refs()
        if ref.inst == inst
    ])
    # print(f"input_refs: {input_refs}")

    # first allocate a bit for each input:
    inputs = {}
    for ref in input_refs:
        inputs[(ref.name, ref.bit)] = all_bits[ref] = next_bit()
    # print(f"inputs: {inputs}")
    # print(f"   ...: {internal}")
    
    # now allocate bits for components:
    # - one for the output of each nand gate 
    # - one for each dynamic flip flop to store the state (which is also its output)
    # - 16 for the output of each memory
    # - one for the clock if any component refers to it
    for r in sorted_nodes(inst):
        if isinstance(r, (NandInstance, NandRootInstance, DynamicDFFInstance, DynamicDFFRootInstance)):
            # print(f"r: {r}")
            # print(f"  a: {r.a}")
            # print(f"  b: {r.b}")
            all_bits[InputRef(r, 'out')] = next_bit()
        elif isinstance(r, (MemoryInstance, MemoryRootInstance)):
            for i in range(16):
                all_bits[InputRef(r, 'out', i)] = next_bit()
        elif isinstance(r, (Instance, RootInstance, Const, CommonInstance, ForwardInstance)):
            # print(f"other: {r}")
            pass
        else:
            raise Exception(f"Unexpected instance: {r} ({r.__class__})")
            
        for ref in r.refs():
            # print(f"ref: {ref}")
            if isinstance(ref.inst, CommonInstance) and ref not in all_bits:
                inputs[('common.' + ref.name, ref.bit)] = all_bits[ref] = next_bit()
    # print(f"nands: {all_bits}")

    # map other component's outputs to nand outputs, transitively
    # TODO: replace this with recursive lookups that don't bloat all_bits (see the other branch)
    for _ in range(2):  # HACK: need multiple passes to wire forwarded bits
        for r in sorted_nodes(inst):
            if isinstance(r, Instance):
                # print(f"inst: {r}; {r.args}")
                for name, ref in r.args.items():
                    # print(f"  propagate: {(name, ref)}")
                    # propagate a single bit or up to 16 bits, whichever are present:
                    if ref in all_bits:
                        all_bits[InputRef(r, name)] = all_bits[ref]
                    for i in range(16):
                        bit_ref = ref[i]
                        if bit_ref in all_bits:
                            all_bits[InputRef(r, name, i)] = all_bits[bit_ref]
                for (name, bit), ref in r.outputs.dict.items(): 
                    # print(f"  output: {name}[{bit}]; {ref}")
                    if ref in all_bits:
                        all_bits[InputRef(r, name, bit)] = all_bits[ref]
                    if bit is None:
                        for i in range(16):
                            bit_ref = ref[i]
                            if bit_ref in all_bits:
                                all_bits[InputRef(r, name, i)] = all_bits[bit_ref]
            elif isinstance(r, ForwardInstance):
                # print(f"forward: {r}")
                for f in list(all_bits.keys()):
                    if f.inst == r.ref:
                        # print(f"propagate: {InputRef(r, f.name, f.bit)} -> {f}")
                        all_bits[InputRef(r, f.name, f.bit)] = all_bits[f]
            elif isinstance(r, (MemoryInstance, MemoryRootInstance)):
                # print(f"mem: {r}; {r.in_, r.load, r.address}")
                # print(f"all: {all_bits}")
                for i in range(16):
                    if r.in_[i] == Const(0):
                        all_bits[InputRef(r, "in_", i)] = 0b1
                    else:
                        if r.in_[i] in all_bits:
                            all_bits[InputRef(r, "in_", i)] = all_bits[r.in_[i]]
                all_bits[InputRef(r, "load")] = all_bits[r.load] if r.load != Const(0) else 0b1
                for i in range(r.address_bits):
                    if r.address[i] in all_bits:
                        all_bits[InputRef(r, "address", i)] = all_bits[r.address[i]]
            elif isinstance(r, (RootInstance, NandInstance, NandRootInstance, Const, CommonInstance, DynamicDFFInstance, DynamicDFFRootInstance)):
                # print(f"other: {r}")
                pass
            else:
                raise Exception(f"Unexpected instance: {r} ({r.__class__})")
    # print(f"all: {all_bits}")
    
    # extract output assignments:
    outputs = {}
    if isinstance(inst, RootInstance):
        for (pred_name, pred_index), pred_ref in inst.outputs.dict.items():
            # propagate a single bit or up to 16 bits, whichever are present:
            if pred_ref in all_bits:
                outputs[(pred_name, pred_index)] = all_bits[pred_ref]
            if pred_index is None:
                for i in range(16):
                    bit_ref = pred_ref[i]
                    if bit_ref in all_bits:
                        outputs[(pred_name, i)] = all_bits[bit_ref]
    elif isinstance(inst, (NandRootInstance, DynamicDFFRootInstance, MemoryRootInstance)):
        outputs[("out", None)] = all_bits[InputRef(inst, "out")]
    # print(f"outputs: {outputs}")
    
    # finally, construct an op for each nand, dff, and memory:
    ops = []
    for r in sorted_nodes(inst):
        if isinstance(r, (NandInstance, NandRootInstance)):
            # print(f"r: {r}")
            # print(f"  a: {r.a}")
            # print(f"  b: {r.b}")
            if r.a == Const(0) or r.b == Const(0):
                # use the constant lowest bit (which is always set):
                in_bits = 0b1  # Nand(a, 0) = !(a & 0) = 1
            else:
                def to_bits(ref):
                    if ref == Const(1): return 0  # Nand(a, 1) = !(a & 1) = !a
                    else: return all_bits[ref]
                in_bits = to_bits(r.a) | to_bits(r.b)
            out_bit = all_bits[InputRef(r, "out")]
            ops.append(NandOp(in_bits, out_bit))
        elif isinstance(r, (DynamicDFFInstance, DynamicDFFRootInstance)):
            in_bit = all_bits[r.in_]
            out_bit = all_bits[InputRef(r, "out")]
            ops.append(DynamicDFFOp(in_bit, out_bit))
        elif isinstance(r, (MemoryInstance, MemoryRootInstance)):
            in_bit_array = [all_bits[InputRef(r, "in_", i)] for i in range(16)]
            load_bit = all_bits[InputRef(r, "load")]
            address_bit_array = [all_bits[InputRef(r, "address", i)] for i in range(r.address_bits)]
            out_bit_array = [all_bits[InputRef(r, "out", i)] for i in range(16)]
            ops.append(MemoryOp(in_bit_array, load_bit, address_bit_array, out_bit_array))
    # print(f"ops: {ops}")
    # print(f"flip flops: {flip_flops}")
    
    internal = { (f"{ref.inst}.{ref.name}", ref.bit): bit 
                 for (ref, bit) in all_bits.items() 
                 if isinstance(ref.inst, Instance)
               }
    
    return NandVector(inputs, outputs, internal, ops)
    
def run(comp, **args):
    """Evaluate a component, accepting input values and returning a wrapper which:
    - exposes the outputs as attributes
    - can be retained to interact with the component in a stateful way
    """
    
    nv = component_to_vector(comp)

    w = NandVectorWrapper(nv)
    for name, value in args.items():
        w.__setattr__(name, value)
    return w
