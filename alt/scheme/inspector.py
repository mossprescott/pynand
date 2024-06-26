"""Python wrappers for Scheme types, for tracing purposes."""

from nand.vector import extend_sign, unsigned
from alt import big

# Seems like overkill
SHOW_SAVED_STACKS = False

class Inspector:
    def __init__(self, computer, symbols, stack_loc, rom_base=big.ROM_BASE, rom_limit=big.HEAP_BASE):
        self.stack_loc = stack_loc

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

    def is_labeled(self, addr):
        return addr in self.symbols_by_addr

    def show_instr(self, addr):
        x, y, z = self.peek(addr), self.peek(addr+1), self.peek(addr+2)

        def show_target(with_value):
            """The target of a jump/call, get, or set: either a slot index or global."""

            # FIXME: use the rvm's actual/current value
            MAX_SLOT = big.ROM_BASE-1
            if 0 <= y <= MAX_SLOT:
                return f"#{y}"
            else:
                return self.show_symbol(y, with_value=with_value)

        if x == 0 and z == 0:
            return f"jump {show_target(True)}"
        elif x == 0:
            return f"call {show_target(True)}" # -> {self.show_addr(z)}"
        elif x == 1:
            return f"set {show_target(False)}" # -> {self.show_addr(z)}"
        elif x == 2:
            return f"get {show_target(False)}" # -> {self.show_addr(z)}"
        elif x == 3:
            return f"const {self.show_obj(y)}" # -> {self.show_addr(z)}"
        elif x == 4:
            return f"if -> {self.show_addr(y)} else {self.show_addr(z)}"
        elif x == 5:
            return "halt"
        else:
            return f"not an instr: {(x, y, z)}"


    def show_symbol(self, addr, with_value=False):
        val, name, z = self.peek(addr), self.peek(addr+1), self.peek(addr+2)
        assert z == 2
        rib_num = (addr - big.HEAP_BASE)//3
        name_and_addr = f"{self._obj(name)}{self.show_addr(addr)}(_{rib_num})"
        if with_value:
            return f"{name_and_addr} = {self._obj(val)}"
        else:
            return name_and_addr


    def _obj(self, val, max_depth=10):
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
                car = self._obj(x)
                if max_depth > 0:
                    cdr = self._obj(y, max_depth=max_depth-1)
                else:
                    cdr = ["..."]
                if isinstance(cdr, list):
                    return [car] + cdr
                else:
                    # In at least one case, this is a "jump" instruction during compilation
                    return (car, cdr, z)
            elif z == 1:  # proc
                if 0 <= x < len(PRIMITIVES):
                    return f"proc({PRIMITIVES[x]})"
                else:
                    num_args, instr = self.peek(x), self.peek(x+2)
                    return f"proc(args={num_args}, env={list_str(self.stack(y))}, instr={self.show_addr(instr)}){self.show_addr(val)}"
            elif z == 2:  # symbol
                return f"symbol({self._obj(y)} = {self._obj(x)})"
            elif z == 3:  # string
                chars = self._obj(x, max_depth=y)
                if len(chars) != y:
                    print(f"bad string: {chars, y, z}")
                return "".join(chr(c) for c in chars)
            elif z == 4:  # vector
                elems = self._obj(x)
                if not isinstance(elems, list) or len(elems) != y:
                    raw = (elems, self._obj(y), z)
                    print(f"bad vector: {raw}")
                    return raw
                else:
                    return elems
            elif z == 5:
                # Unexpected, but show the contents just in case
                return f"special({self.show_obj(x)}, {self.show_obj(y)}){self.show_addr(val)}"
            else:
                return f"TODO: ({x}, {y}, {z})"


    def show_obj(self, val):
        """Show an object, which may be an integer, special value, or rib."""

        return str(self._obj(val))


    def stack(self, addr=None):
        """Contents of the stack, bottom to top."""
        if addr is None:
            addr = self.peek(self.stack_loc)

        if self.symbols_by_addr.get(addr) == "rib_nil":
            # This appears only after the outer continuation is invoked:
            return []
        elif addr == 0:
            # sanity check
            return ["<0>!"]
        else:
            x, y, z = self.peek(addr), self.peek(addr+1), self.peek(addr+2)

            if z == 0:  # pair
                return self.stack(y) + [self._obj(x)]
            else:
                if SHOW_SAVED_STACKS:
                    saved_str = list_str(self.stack(x))
                    cont = f"cont(saved={saved_str}; {self.show_addr(z)}){self.show_addr(addr)}"
                else:
                    cont = f"cont({self.show_addr(z)}){self.show_addr(addr)}"

                if y == 0:
                    # outer continuation: there is no proc, and no further stack
                    return [cont]
                else:
                    # Note: no instruction ever actually looks at this entry. It's just holding `env`,
                    # which we're about to traverse. But need to show something so slot numbers make
                    # sense.
                    closure = "<closure>"
                    return self.stack(self.peek(y+1)) + [closure, cont]


    def show_stack(self):
        """Show the contents of the stack, which is a list composed of ordinary pairs and continuation
        ribs."""

        return ", ".join(str(o) for o in reversed(self.stack()))


def list_str(lst):
    """Looks like a list's repr(), but use str() on the elements to avoid quoting everything.

    Why do I have to write this? Or do I?
    """
    return "[" + ", ".join(str(x) for x in lst) + "]"


PRIMITIVES = {
    0: "rib",
    1: "id",
    2: "arg1",
    3: "arg2",
    4: "close",
    5: "rib?",
    6: "field0",
    7: "field1",
    8: "field2",
    9: "field0-set!",
    10: "field1-set!",
    11: "field2-set!",
    12: "eqv?",
    13: "<",
    14: "+",
    15: "-",
    16: "*",
    17: "quotient",
    18: "getchar",
    19: "putchar",
    # Extra:
    20: "peek",
    21: "poke",
    22: "halt",
    23: "screenAddr",
}