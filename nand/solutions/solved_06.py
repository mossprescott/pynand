"""Solutions for project 06.

SPOILER ALERT: this files contains a complete assembler.
If you want to solve them on your own, stop reading now!
"""

# Disclaimer: this implementation was written quickly and seems to work, but those are the only good
# things that can be said about it.

import re

ALU_CONTROL = {
    # These match the bit patterns used in Add and Max:
    "0":   0b101010,
    "A":   0b110000,
    "D":   0b001100,
    "D-A": 0b010011,
    "D+A": 0b000010,
    "1":   0b111111,
    "-1":  0b111010,
    "D&A": 0b000000,
    "D|A": 0b010101,
    "A-D": 0b000111,
    "!D":  0b001011,
    "!A":  0b110001,
    "D+1": 0b011111,
    "A+1": 0b110111,
    "D-1": 0b001110,
    "A-1": 0b110010,
    "-D":  0b001111,
    "-A":  0b110011,
    # Redundant spellings so you don't have to remember which way to write them:
    "A+D": 0b000010,
    "A&D": 0b000000,
    "A|D": 0b010101,
}

JMP_CONTROL = {
    "LT": 0b100,
    "LE": 0b110,
    "EQ": 0b010,
    "NE": 0b101,
    "GE": 0b011,
    "GT": 0b001,
    "MP": 0b111,
}

def register_names(count):
    """Names for the first locations in low memory: R0, R1, ..."""
    return { f"R{i}": i for i in range(count) }


BUILTIN_SYMBOLS = {
    **{
        "SP":       0,
        "LCL":      1,
        "ARG":      2,
        "THIS":     3,
        "THAT":     4,
        "SCREEN":   0x4000,
        "KEYBOARD": 0x6000,
    },
    **register_names(16)
}


def parse_op(string, symbols=None):
    """Parse a single assembly op directly to the corresponding Hack instruction word.

    The op may be a numeric symbol (an A-command) or a C-command, but not a reference
    to a symbol or variable.

    :param symbols: a dictionary mapping symbol names to addresses (of labels in the code
    and memory locations allocated for "static" variables.) Note: not used in this implementation,
    but included in the signature in so that other compatible parsers can use it.

    Extra syntax:
    - Constant values may be specified in hex, e.g. @0x5555
    """

    m = re.match(r"@((0x[0-9a-fA-F]+)|([1-9][0-9]*)|0)", string)
    if m:
        value = eval(m.group(1))
        if value < 0 or value > 0x7FFF:
            raise ParseError(f"A-command value out of range: {value}")
        return value
    else:
        m = re.match(r"(?:([ADM]+)=)?([^;]+)(?:;J(..))?", string)
        if m:
            dest_str = m.group(1) or ""
            dest = 0
            if 'A' in dest_str:
                dest |= 0b100
            if 'D' in dest_str:
                dest |= 0b010
            if 'M' in dest_str:
                dest |= 0b001

            alu_str = m.group(2).replace('M', 'A')
            if alu_str in ALU_CONTROL:
                alu = ALU_CONTROL[alu_str]
                m_for_a = int('M' in m.group(2))
            else:
                raise ParseError(f"unrecognized alu op: {m.group(2)}")

            jmp_str = m.group(3)
            if jmp_str is None:
                jmp = 0
            elif jmp_str in JMP_CONTROL:
                jmp = JMP_CONTROL[jmp_str]
            else:
                raise ParseError(f"unrecognized jump: J{m.group(3)}")

            return (0b111 << 13) | (m_for_a << 12) | (alu << 6) | (dest << 3) | jmp
        else:
            raise ParseError(f"unrecognized: {string}")


def assemble(lines, parse_op=parse_op, min_static=16, max_static=255, start_addr=0, builtins=BUILTIN_SYMBOLS):
    """Parse a sequence of lines them as assembly commands, accounting for
    builtin symbols, labels, and variables.

    "//" denotes a comment and is ignored, along with the remainder of the line.
    Leading and trailing white space on each line is ignored.
    After comments and white space are stripped, blank lines are ignored.

    :return: A tuple containing (list of instruction words,
                dictionary mapping labels to locations in ROM,
                dictionary mapping non-label symbols to addresses in RAM).
    """

    # First pass: strip out non-instruction lines and extraneous characters:
    code_lines = []
    for line in lines:
        m = re.match(r"([^/]*)(?://.*)?", line)
        if m:
            string = m.group(1).strip()
        else:
            string = line.strip()

        if string:
            code_lines.append(string)

    # Second pass: resolve labels to locations
    symbols = {}
    loc = start_addr
    for line in code_lines:
        m = re.match(r"\((.*)\)", line)
        if m:
            name = m.group(1)
            if name in builtins:
                raise ParseError(f"Attempt to redefine builtin symbol {name} at location {loc}")
            elif name in symbols:
                # This isn't an error because allowing re-definition makes it easy to hackishly
                # override something (see alt/shift.py). Sorry, world.
                print(f"WARNING! Label {name} redefined at {loc} (previous location: {symbols[name]})")
            symbols[name] = loc
        else:
            loc += 1

    # Third pass: parse all other instructions, and resolve non-label symbols (i.e. "static" allocations.)
    ops = [0]*start_addr
    statics = {}
    next_static = min_static
    for line in code_lines:
        if "(" in line:
            pass
        else:
            m = re.match(r"@(\D.*)", line)
            if m:
                name = m.group(1)
                if name in builtins:
                    ops.append(builtins[name])
                elif name in symbols:
                    ops.append(symbols[name])
                elif name in statics:
                    ops.append(statics[name])
                else:
                    if next_static is None:
                        raise ParseError(f"Unable to allocate static storage for symbol {name}; no static allocation space available")
                    elif next_static > max_static:
                        raise ParseError(f"Unable to allocate static storage for symbol {name}; already used all {max_static - min_static + 1} available locations")
                    else:
                        statics[name] = next_static
                        ops.append(next_static)
                        next_static += 1
            else:
                ops.append(parse_op(line, symbols))

    return (ops, symbols, statics)


class ParseError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
