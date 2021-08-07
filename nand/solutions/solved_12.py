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

ARRAY_NEW = """
    /** Constructs a new Array of the given size. */
    function Array new(int size) {
        if (size < 0) {
            do Sys.error(2);
        }
        return Memory.alloc(size);
    }
"""


ARRAY_DISPOSE = """
    /** Disposes this array. */
    method void dispose() {
        do Memory.deAlloc(this);
        return;
    }
"""


ARRAY_CLASS = f"""
class Array {{
{ARRAY_NEW}
{ARRAY_DISPOSE}
}}
"""


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
