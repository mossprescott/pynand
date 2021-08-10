from nand.solutions import solved_10

def _parse_jack_file(class_name):
    with open(f"nand/solutions/solved_12/{class_name}.jack") as f:
        src = "\n".join(f.readlines())
        # raise Exception(src)
        # raise Exception(solved_10.lex(src))
        return solved_10.ClassP.parse(solved_10.lex(src))

def _find_subroutine(class_ast, sub_name):
    for sd in class_ast.subroutineDecs:
        if sd.name == sub_name:
            return sd
    raise Exception("Not found: {class_ast.name}.{sub_name}")


####################
## Array.jack
####################

_ARRAY_CLASS = _parse_jack_file("Array")

ARRAY_NEW     = _find_subroutine(_ARRAY_CLASS, "new")
ARRAY_DISPOSE = _find_subroutine(_ARRAY_CLASS, "dispose")


####################
## String.jack
####################

_STRING_CLASS = _parse_jack_file("String")

STRING_VAR_DECS = _STRING_CLASS.varDecs

STRING_NEW             = _find_subroutine(_STRING_CLASS, "new")
STRING_DISPOSE         = _find_subroutine(_STRING_CLASS, "dispose")
STRING_LENGTH          = _find_subroutine(_STRING_CLASS, "length")
STRING_CHAR_AT         = _find_subroutine(_STRING_CLASS, "charAt")
STRING_SET_CHAR_AT     = _find_subroutine(_STRING_CLASS, "setCharAt")
STRING_APPEND_CHAR     = _find_subroutine(_STRING_CLASS, "appendChar")
STRING_ERASE_LAST_CHAR = _find_subroutine(_STRING_CLASS, "eraseLastChar")
STRING_INT_VALUE       = _find_subroutine(_STRING_CLASS, "intValue")
STRING_SET_INT         = _find_subroutine(_STRING_CLASS, "setInt")
STRING_NEW_LINE        = _find_subroutine(_STRING_CLASS, "newLine")
STRING_BACK_SPACE      = _find_subroutine(_STRING_CLASS, "backSpace")
STRING_DOUBLE_QUOTE    = _find_subroutine(_STRING_CLASS, "doubleQuote")


####################
## Memory.jack
####################

_MEMORY_CLASS = _parse_jack_file("Memory")

MEMORY_VAR_DECS = _MEMORY_CLASS.varDecs

MEMORY_INIT     = _find_subroutine(_MEMORY_CLASS, "init")
MEMORY_PEEK     = _find_subroutine(_MEMORY_CLASS, "peek")
MEMORY_POKE     = _find_subroutine(_MEMORY_CLASS, "poke")
MEMORY_ALLOC    = _find_subroutine(_MEMORY_CLASS, "alloc")
MEMORY_DE_ALLOC = _find_subroutine(_MEMORY_CLASS, "deAlloc")


####################
## Output.jack
####################

_OUTPUT_CLASS = _parse_jack_file("Output")

OUTPUT_INIT         = _find_subroutine(_OUTPUT_CLASS, "init")
OUTPUT_MOVE_CURSOR  = _find_subroutine(_OUTPUT_CLASS, "moveCursor")
OUTPUT_PRINT_CHAR   = _find_subroutine(_OUTPUT_CLASS, "printChar")
OUTPUT_PRINT_STRING = _find_subroutine(_OUTPUT_CLASS, "printString")
OUTPUT_PRINT_INT    = _find_subroutine(_OUTPUT_CLASS, "printInt")
OUTPUT_PRINTLN      = _find_subroutine(_OUTPUT_CLASS, "println")
OUTPUT_BACK_SPACE   = _find_subroutine(_OUTPUT_CLASS, "backSpace")


# A bunch of code follows which is all related to generating an implementation of Output.printChar.
# CHAR_MAPS contains the raw values, as provided by the authors (but also including "A"), and
# could be used to generate an alternative implementation.

CHAR_MAPS = {
    # Black square, used for displaying non-printable characters.
    0: [63,63,63,63,63,63,63,63,63,0,0],

    32: [0,0,0,0,0,0,0,0,0,0,0],          # (space)
    33: [12,30,30,30,12,12,0,12,12,0,0],  # !
    34: [54,54,20,0,0,0,0,0,0,0,0],       # "
    35: [0,18,18,63,18,18,63,18,18,0,0],  # #
    36: [12,30,51,3,30,48,51,30,12,12,0], # $
    37: [0,0,35,51,24,12,6,51,49,0,0],    # %
    38: [12,30,30,12,54,27,27,27,54,0,0], # &
    39: [12,12,6,0,0,0,0,0,0,0,0],        # '
    40: [24,12,6,6,6,6,6,12,24,0,0],      # (
    41: [6,12,24,24,24,24,24,12,6,0,0],   # )
    42: [0,0,0,51,30,63,30,51,0,0,0],     # *
    43: [0,0,0,12,12,63,12,12,0,0,0],     # +
    44: [0,0,0,0,0,0,0,12,12,6,0],        # ,
    45: [0,0,0,0,0,63,0,0,0,0,0],         # -
    46: [0,0,0,0,0,0,0,12,12,0,0],        # .
    47: [0,0,32,48,24,12,6,3,1,0,0],      # /

    48: [12,30,51,51,51,51,51,30,12,0,0], # 0
    49: [12,14,15,12,12,12,12,12,63,0,0], # 1
    50: [30,51,48,24,12,6,3,51,63,0,0],   # 2
    51: [30,51,48,48,28,48,48,51,30,0,0], # 3
    52: [16,24,28,26,25,63,24,24,60,0,0], # 4
    53: [63,3,3,31,48,48,48,51,30,0,0],   # 5
    54: [28,6,3,3,31,51,51,51,30,0,0],    # 6
    55: [63,49,48,48,24,12,12,12,12,0,0], # 7
    56: [30,51,51,51,30,51,51,51,30,0,0], # 8
    57: [30,51,51,51,62,48,48,24,14,0,0], # 9

    58: [0,0,12,12,0,0,12,12,0,0,0],      # :
    59: [0,0,12,12,0,0,12,12,6,0,0],      # ;
    60: [0,0,24,12,6,3,6,12,24,0,0],      # <
    61: [0,0,0,63,0,0,63,0,0,0,0],        # =
    62: [0,0,3,6,12,24,12,6,3,0,0],       # >
    64: [30,51,51,59,59,59,27,3,30,0,0],  # @
    63: [30,51,51,24,12,12,0,12,12,0,0],  # ?

    65: [30,51,51,51,63,51,51,51,51,0,0], # A
    66: [31,51,51,51,31,51,51,51,31,0,0], # B
    67: [28,54,35,3,3,3,35,54,28,0,0],    # C
    68: [15,27,51,51,51,51,51,27,15,0,0], # D
    69: [63,51,35,11,15,11,35,51,63,0,0], # E
    70: [63,51,35,11,15,11,3,3,3,0,0],    # F
    71: [28,54,35,3,59,51,51,54,44,0,0],  # G
    72: [51,51,51,51,63,51,51,51,51,0,0], # H
    73: [30,12,12,12,12,12,12,12,30,0,0], # I
    74: [60,24,24,24,24,24,27,27,14,0,0], # J
    75: [51,51,51,27,15,27,51,51,51,0,0], # K
    76: [3,3,3,3,3,3,35,51,63,0,0],       # L
    77: [33,51,63,63,51,51,51,51,51,0,0], # M
    78: [51,51,55,55,63,59,59,51,51,0,0], # N
    79: [30,51,51,51,51,51,51,51,30,0,0], # O
    80: [31,51,51,51,31,3,3,3,3,0,0],     # P
    81: [30,51,51,51,51,51,63,59,30,48,0],# Q
    82: [31,51,51,51,31,27,51,51,51,0,0], # R
    83: [30,51,51,6,28,48,51,51,30,0,0],  # S
    84: [63,63,45,12,12,12,12,12,30,0,0], # T
    85: [51,51,51,51,51,51,51,51,30,0,0], # U
    86: [51,51,51,51,51,30,30,12,12,0,0], # V
    87: [51,51,51,51,51,63,63,63,18,0,0], # W
    88: [51,51,30,30,12,30,30,51,51,0,0], # X
    89: [51,51,51,51,30,12,12,12,30,0,0], # Y
    90: [63,51,49,24,12,6,35,51,63,0,0],  # Z

    91: [30,6,6,6,6,6,6,6,30,0,0],          # [
    92: [0,0,1,3,6,12,24,48,32,0,0],        # \
    93: [30,24,24,24,24,24,24,24,30,0,0],   # ]
    94: [8,28,54,0,0,0,0,0,0,0,0],          # ^
    95: [0,0,0,0,0,0,0,0,0,63,0],           # _
    96: [6,12,24,0,0,0,0,0,0,0,0],          # `

    97: [0,0,0,14,24,30,27,27,54,0,0],      # a
    98: [3,3,3,15,27,51,51,51,30,0,0],      # b
    99: [0,0,0,30,51,3,3,51,30,0,0],        # c
    100: [48,48,48,60,54,51,51,51,30,0,0],  # d
    101: [0,0,0,30,51,63,3,51,30,0,0],      # e
    102: [28,54,38,6,15,6,6,6,15,0,0],      # f
    103: [0,0,30,51,51,51,62,48,51,30,0],   # g
    104: [3,3,3,27,55,51,51,51,51,0,0],     # h
    105: [12,12,0,14,12,12,12,12,30,0,0],   # i
    106: [48,48,0,56,48,48,48,48,51,30,0],  # j
    107: [3,3,3,51,27,15,15,27,51,0,0],     # k
    108: [14,12,12,12,12,12,12,12,30,0,0],  # l
    109: [0,0,0,29,63,43,43,43,43,0,0],     # m
    110: [0,0,0,29,51,51,51,51,51,0,0],     # n
    111: [0,0,0,30,51,51,51,51,30,0,0],     # o
    112: [0,0,0,30,51,51,51,31,3,3,0],      # p
    113: [0,0,0,30,51,51,51,62,48,48,0],    # q
    114: [0,0,0,29,55,51,3,3,7,0,0],        # r
    115: [0,0,0,30,51,6,24,51,30,0,0],      # s
    116: [4,6,6,15,6,6,6,54,28,0,0],        # t
    117: [0,0,0,27,27,27,27,27,54,0,0],     # u
    118: [0,0,0,51,51,51,51,30,12,0,0],     # v
    119: [0,0,0,51,51,51,63,63,18,0,0],     # w
    120: [0,0,0,51,30,12,12,30,51,0,0],     # x
    121: [0,0,0,51,51,51,62,48,24,15,0],    # y
    122: [0,0,0,63,27,12,6,51,63,0,0],      # z

    123: [56,12,12,12,7,12,12,12,56,0,0],   # {
    124: [12,12,12,12,12,12,12,12,12,0,0],  # |
    125: [7,12,12,12,56,12,12,12,7,0,0],    # }
    126: [38,45,25,0,0,0,0,0,0,0,0],        # ~
}

def generate_switch(var, bits, content):
    """Generate a giant nested Jack if/else matching each possible value
    from 0 to 127, with bodies from the provided map.
    """
    def indent(lines):
        return ["    " + l for l in lines]

    def gen(b, x):
        if b == 0:
            return content.get(x, [])
        else:
            cond = f"if ({var} & {1 << (b-1)})"
            true_body = gen(b-1, 2*x + 1)
            false_body = gen(b-1, 2*x)

            if true_body == [] and false_body == []:
                return []
            else:
                if len(true_body) > 1:
                    true_lines = [cond + "{"] + indent(true_body) + ["}"]
                else:
                    true_lines = [f"{cond} {{ {' '.join(true_body)} }}"]
                if len(false_body) == 0:
                    false_lines = []
                elif len(false_body) > 1:
                    false_lines = ["else {"] + indent(false_body) + ["}"]
                else:
                    false_lines = [f"else {{       {' '.join(false_body)} }}"]
                return true_lines + false_lines

    return gen(bits, 0)

def generate_print_char_switch(font=CHAR_MAPS):
    def body_lines(val, rows):
        args = ", ".join(str((r << 8) | r) for r in rows)
        return [f"do Output._drawChar({args}); return;  /* {hex(val)} = {val} */"]

    bodies = { k: body_lines(k, v) for k, v in font.items() if k != 0 }
    print("\n".join("        " + l for l in generate_switch("c", 7, bodies)))

    print()
    print("        // Fallback: the black box")
    print("\n".join("        " + l for l in body_lines(0, font[0])))

if __name__ == '__main__':
    generate_print_char_switch()
