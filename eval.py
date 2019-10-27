"""A new evaluator, based on bit vectors."""

class State:
    def __init__(self, inputs, outputs, ops):
        self.inputs = inputs
        self.outputs = outputs
        self.ops = ops
        
        self.traces = 0
        self.dirty = True
        
    def set_input(self, name, value):
        if value:
            self.traces |= self.inputs[name]
        else:
            self.traces &= ~self.inputs[name]
        self.dirty = True
        
    def _propagate(self):
        if not self.dirty: return
        
        for i in range(10):
            tmp = self.traces
            for (in_bits, out_bits) in self.ops:
                if (tmp & in_bits) == in_bits:
                    tmp &= ~out_bits
                else:
                    tmp |= out_bits
            if tmp == self.traces: 
                break
            else:
                self.traces = tmp
        else:
            raise Exception("state did not settle after 10 loops")
        
        self.dirty = False
            
    def get_output(self, name):
        self._propagate()
        
        return bool(self.traces & self.outputs[name])
        

    # nand = Nand(a=a, b=b).out
    # nandANand = Nand(a=a, b=nand).out
    # nandBNand = Nand(a=nand, b=b).out
    # outputs.out = Nand(a=nandANand, b=nandBNand).out

xor = State(
    {'a': 0b000001, 'b': 0b000010},
    {'out': 0b100000},
    [ (0b000011, 0b000100),  # Nand(a, b) -> nand
      (0b000101, 0b001000),  # Nand(a, nand) -> na
      (0b000110, 0b010000),  # Nand(b, nand) -> nb
      (0b011000, 0b100000)   # Nand(na, na) -> out
    ]
)


assert xor.get_output('out') == False

xor.set_input('a', True)
assert xor.get_output('out') == True

xor.set_input('b', True)
assert xor.get_output('out') == False

xor.set_input('a', False)
assert xor.get_output('out') == True
