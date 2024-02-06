"""Python wrappers for Scheme types, for tracing purposes."""

from nand.vector import extend_sign, unsigned
from alt import big


class Inspector:
    def __init__(self, computer, symbols={}, rom_base=big.ROM_BASE, rom_limit=big.HEAP_BASE):
        def peek(addr):
            if rom_base <= addr < rom_limit:
                return computer.peek_rom(addr)
            else:
                return computer.peek(addr)

        self.peek = peek
        self.symbols_by_addr = { addr: name for (name, addr) in symbols.items() }


    def show_addr(self, addr):
        """Show an address (with "@"), using the symbol for addresses in ROM."""
        if addr in self.symbols_by_addr:
            return f"@{self.symbols_by_addr[addr]}"
        else:
            return f"@{unsigned(addr)}"


    def show_instr(self, addr):
        x, y, z = self.peek(addr), self.peek(addr+1), self.peek(addr+2)

        def show_target():
            """The target of a jump/call, get, or set: either a slot index or global."""

            # FIXME: use the rvm's actual/current value
            MAX_SLOT = big.ROM_BASE-1
            if 0 <= y <= MAX_SLOT:
                return f"#{y}"
            else:
                return self.show_addr(y)

        if x == 0 and z == 0:
            return f"jump {show_target()}"
        elif x == 0:
            return f"call {show_target()}" # -> {self.show_addr(z)}"
        elif x == 1:
            return f"set {show_target()}" # -> {self.show_addr(z)}"
        elif x == 2:
            return f"get {show_target()}" # -> {self.show_addr(z)}"
        elif x == 3:
            return f"const {self.show_obj(y)}" # -> {self.show_addr(z)}"
        elif x == 4:
            return f"if -> {self.show_addr(y)} else {self.show_addr(z)}"
        elif x == 5:
            return "halt"
        else:
            return f"not an instr: {(x, y, z)}"


    def _obj(self, val):
        """Python representation of an object, which may be an integer, special value, or rib."""

        # FIXME: check tag
        if -big.ROM_BASE < extend_sign(val) < big.ROM_BASE:
            return extend_sign(val)
        elif self.symbols_by_addr.get(val) == "rib_nil":
            return []
        elif self.symbols_by_addr.get(val) == "rib_true":
            return True
        elif self.symbols_by_addr.get(val) == "rib_false":
            return False
        else:
            x, y, z = self.peek(val), self.peek(val+1), self.peek(val+2)
            if z == 0:  # pair
                return [self._obj(x)] + self._obj(y)
            elif z == 1:  # proc
                MAX_PRIMITIVE = 31
                if 0 < x < MAX_PRIMITIVE:
                    return f"primitive(#{x})"  # TODO: lookup the primitive's name
                else:
                    num_args, instr = self.peek(x), self.peek(x+2)
                    return f"proc(args={num_args}, env={self.show_obj(y)}, instr={self.show_addr(instr)}){self.show_addr(val)}"
            # elif z == 2:  # symbol
            # elif z == 3:  # string
            # elif z == 4:  # vector
            elif z == 5:
                # Unexpected, but show the contents just in case
                return f"special({self.show_obj(x)}, {self.show_obj(y)}){self.show_addr(val)}"
            else:
                return f"TODO: ({x}, {y}, {z})"


    def show_obj(self, val):
        """Show an object, which may be an integer, special value, or rib."""

        return str(self._obj(val))


    def stack(self):
        """Contents of the stack, bottom to top."""

        def go(addr):
            if self.symbols_by_addr.get(addr) == "rib_nil":
                # This appears only after the outer continuation is invoked:
                return []
            elif addr == 0:
                # sanity check
                raise Exception("Unexpected zero pointer in stack")
            else:
                x, y, z = self.peek(addr), self.peek(addr+1), self.peek(addr+2)

                if z == 0:  # pair
                    return go(y) + [self._obj(x)]
                else:
                    # A continuation: (stack, closure, next instr)
                    return go(x) + [f"cont({self.show_addr(z)})"]
        SP = 0
        return go(self.peek(SP))


    def show_stack(self):
        """Show the contents of the stack, which is a list composed of ordinary pairs and continuation
        ribs."""

        return ", ".join(str(o) for o in self.stack())

