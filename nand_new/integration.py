from nand_new.component import Component

class IC:
    """An integrated circuit assembles one or more components by recording how their 
    inputs and outputs are connected.
    
    An IC also acts as a component when it is assembled with other components into a 
    larger chip.
    """
    
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs
        self.root = Root(self)
        self.components = {}
        self.wires = {}
        
    def wire(self, from_output, to_input):
        """Connect a single trace from an output of one component to an input of another. 
        
        Note that the IC's inputs act as outputs to feed the inputs of components, and vice versa.
        Yes, that does seem confusing.
        
        Each input can be connected to exactly one output; an output may feed any number of 
        inputs, or none at all. A new wiring overwrites any previous wiring to the same input.
        
        Both components become part of this circuit.
        
        The connection is checked on both ends to ensure that it specifies a valid name and bit.
        Note: if a WiringError is thrown, both components are nevertheless tracked as being part 
        of the IC. TODO: maybe clean that up after the fact?
        """
        
        self._add_component(from_output.comp)
        self._add_component(to_input.comp)

        if from_output.name not in from_output.comp.outputs():
            raise WiringError(f"Component {self._comp_label(from_output.comp)} has no output '{from_output.name}'")
        elif from_output.bit < 0 or from_output.bit >= from_output.comp.outputs()[from_output.name]:
            raise WiringError(f"Tried to connect bit {from_output.bit} of {from_output.comp.outputs()[from_output.name]}-bit output {self._comp_label(from_output.comp)}.{from_output.name}")
        elif to_input.name not in to_input.comp.inputs():
            raise WiringError(f"Component {self._comp_label(to_input.comp)} has no input '{to_input.name}'")
        elif to_input.bit < 0 or to_input.bit >= to_input.comp.inputs()[to_input.name]:
            raise WiringError(f"Tried to connect bit {to_input.bit} of {to_input.comp.inputs()[to_input.name]}-bit input {self._comp_label(to_input.comp)}.{to_input.name}")
            
        self.wires[to_input] = from_output
        
    def _add_component(self, comp):
        if comp != self.root and comp not in self.components:
            self.components[comp] = len(self.components)
        
    def _comp_label(self, comp):
        if comp == self.root:
            return "Root"
        else:
            return f"{comp.__class__.__name__}_{self.components[comp]}"
        
    def flatten(self):
        """Construct a new IC which has the same structure as this one, but no nested ICs.
        That is, the wiring of all child ICs has been "inlined" into a single flat assembly.
        """
        raise NotImplementedError


class Root:
    """Pseudo-component providing access to an ICs inputs and outputs (under the opposite names).
    """
    
    def __init__(self, ic):
        self.ic = ic

    def inputs(self):
        return self.ic.outputs

    def outputs(self):
        return self.ic.inputs
        

class Connection:
    def __init__(self, comp, name, bit):
        # assert 0 <= bit < 16  # wait and signal a WiringError
        self.comp = comp
        self.name = name
        self.bit = bit
    
    
class WiringError(Exception):
    def __init__(self, msg):
        Exception(msg)
    