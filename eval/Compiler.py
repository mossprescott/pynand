# TODO: what to call this module?

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
