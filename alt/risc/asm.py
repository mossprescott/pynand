"""Assembler for RiSC, using the HACK assembler's syntax for labels, comments, etc.

Examples:

// A single-line comment starts with two slashes

// A label appears on a line by itself, surrounded by parens:
(main.main)

// Leading and trailing spaces are ignored; 2-space indent is typical
// Register names always look like r0..r7:
  add r1 r1 r2

// Immediate constant values must fit in the available bits, and may be explicitly signed:
  addi r1 r0 -10
  beq r0 r3 +1

// When loading a constant value, the low 6 bits *must* be 0; so to load -65, you have to
// be explicit about the two separate parts:
  lui r2 -64
  addi r2 r0 -1

// When lui refers to a label, the low bits are masked off silently:
  lui r2 @someHighAddress

// Simlarly with lli, which can *only* be used with a label:
  lli r2 @someHighAddress
"""

import re

from nand import parsing
from nand.solutions import solved_06
from nand.vector import extend_sign, unsigned

class MatchP(parsing.Parser):
    """Not using a lexer here, so it's helpful to be able to fallback to a regex, even if it
    does feel a bit dirty.
    """

    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, loc):
        val, loc = loc.current_token(), loc.advance()
        m = re.match(self.pattern, val)
        if m is not None:
            return m.group(1), loc
        else:
            raise parsing.ParseFailure(f"a token matching {self.pattern!r}", loc)


def parse_op(string, symbols):
    """Tricky: RiSC instructions can have references to labels embedded in them in more than one way.

    Since we've got a proper parser combinator library and know how to use it, might as well do that.
    """

    regP = MatchP("r([0-7])").map(int)

    def mask7(s):
        x = int(s)
        if -64 <= x < 64:
            return x & 0x7F
        else:
            raise Exception(f"Constant value doesn't fit in 7-bit immediate field: {x}")
    constP = MatchP(r"((?:-|\+)?\d+)").map(mask7).describe("constant value with up to 7 bits (including sign)")

    def rrrP(mnemonic, op):
        return (
            parsing.TokenP(mnemonic, None) << regP & regP & regP
        ).mapConstr(lambda a, b, c: (op << 13) | (a << 10) | (b << 7) | c).describe(f"'{mnemonic} rA rB rC'")

    def rrP(mnemonic, op):
        return (
            parsing.TokenP(mnemonic, None) << regP & regP
        ).mapConstr(lambda a, b: (op << 13) | (a << 10) | (b << 7)).describe(f"'{mnemonic} rA rB'")

    def rrcP(mnemonic, op):
        return (
            parsing.TokenP(mnemonic, None) << regP & regP & constP
        ).mapConstr(lambda a, b, i: (op << 13) | (a << 10) | (b << 7) | i).describe(f"'{mnemonic} rA rB [-512..511]'")

    def rxaP(mnemonic, op):
        def labelLower6(s):
            addr = symbols.get(s)
            if addr is None:
                raise Exception(f"Unresolved label: {s}")
            if not (0 <= addr < 32768):
                raise Exception(f"Address doesn't seem to make sense: {addr} (label: {s})")
            return unsigned(addr) & 0x3F
        labelP = MatchP(r"@([a-zA-Z].*)").map(labelLower6).describe("@label")

        return (
            parsing.TokenP(mnemonic, None) << regP & labelP
        ).mapConstr(lambda a, i: (op << 13) | (a << 10) | (a << 7) | i).describe(f"'{mnemonic} rA @label'")


    def riP(mnemonic, op):
        def shift6(s):
            x = int(s)
            if not (-32768 <= x < 32768):
                raise Exception(f"Constant value doesn't fit in 10-bit immediate field: {x}")
            if x & 0x3f != 0:
                raise Exception(f"Constant value has one or more 1s in the low 6 bits: {x} == {bin(x)}")
            return (unsigned(x) >> 6) & 0x3FF
        constP = MatchP(r"(-?\d+)").map(shift6).describe("constant value with zero in the low 6 bits")

        def labelUpper10(s):
            addr = symbols.get(s)
            if addr is None:
                raise Exception(f"Unresolved label: {s}")
            if not (0 <= addr < 32768):
                raise Exception(f"Address doesn't fit in 10-bit immediate field: {addr} (label: {s})")
            return unsigned(addr >> 6) & 0x3FF

        labelP = MatchP(r"@([a-zA-Z].*)").map(labelUpper10).describe("@label")

        return (
            parsing.TokenP(mnemonic, None) << regP & (constP | labelP)
        ).mapConstr(lambda a, i: (op << 13) | (a << 10) | i).describe(f"'{mnemonic} rA ([-32768..32704] | @label)'")


    instrP = (
          rrrP("add",  0b000)
        | rrcP("addi", 0b001)
        | rxaP("lli",  0b001)
        | rrrP("nand", 0b010)
        | riP( "lui",  0b011)
        | rrcP("lw",   0b100)  # Note: label not supported
        | rrcP("sw",   0b101)  # Note: label not supported
        | rrcP("beq",  0b110)  # TODO: labels (rroP)
        | rrP( "jalr", 0b111))


    # print(f"parse: {string}")
    return instrP.parse(string.split())


def assemble(lines, min_static=16, max_static=255):
    return solved_06.assemble(lines, parse_op=parse_op, min_static=min_static, max_static=max_static)
