# Operating System
#
# See https://www.nand2tetris.org/project12

from nand import parsing, jack_ast

import project_10

# SOLVERS: remove this import to get started
from nand.solutions import solved_12


def parse_classVarDecs(src):
    return parsing.ManyP(project_10.ClassVarDecP).parse(project_10.lex(src))

def parse_subroutineDec(src):
    return project_10.SubroutineDecP.parse(project_10.lex(src))


# SOLVERS: un-comment and fill in the implementation
ARRAY_NEW = solved_12.ARRAY_NEW
# ARRAY_NEW = """
#     /** Constructs a new Array of the given size. */
#     function Array new(int size) {
#
#     }
# """

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


# SOLVERS: if you assume these fields you can implement the methods below one at a time
STRING_CLASS_VARS = parse_classVarDecs("""
    field int capacity;
    field Array chars;
    field int length;
""")

STRING_NEW = solved_12.STRING_NEW
# STRING_NEW = parse_subroutineDec("""
#     /** constructs a new empty string with a maximum length of maxLength
#      *  and initial length of 0. */
#     constructor String new(int maxLength) {
#     }
# """)

STRING_DISPOSE = solved_12.STRING_DISPOSE
# parse_subroutineDec("""
#     /** Disposes this string. */
#     method void dispose() {
#     }
# """)

STRING_LENGTH = solved_12.STRING_LENGTH
# parse_subroutineDec("""
#     /** Returns the current length of this string. */
#     method int length() {
#     }
# """)

STRING_CHAR_AT = solved_12.STRING_CHAR_AT
# parse_subroutineDec("""
#     /** Returns the character at the j-th location of this string. */
#     method char charAt(int j) {
#     }
# """)

STRING_SET_CHAR_AT = solved_12.STRING_SET_CHAR_AT
# parse_subroutineDec("""
#     /** Sets the character at the j-th location of this string to c. */
#     method void setCharAt(int j, char c) {
#     }
# """)

# Note: returning the String itself from this particular method makes it a bit
# more convenient to use this same method in the implementation of String constants.
STRING_APPEND_CHAR = solved_12.STRING_APPEND_CHAR
# parse_subroutineDec("""
#     /** Appends c to this string's end and returns this string. */
#     method String appendChar(char c) {
#     }
# """)

STRING_ERASE_LAST_CHAR = solved_12.STRING_ERASE_LAST_CHAR
# parse_subroutineDec("""
#     /** Erases the last character from this string. */
#     method void eraseLastChar() {
#     }
# """)

STRING_INT_VALUE = solved_12.STRING_INT_VALUE
# parse_subroutineDec("""
#     /** Returns the integer value of this string,
#      *  until a non-digit character is detected. */
#     method int intValue() {
#     }
# """)

STRING_SET_INT = solved_12.STRING_SET_INT
# parse_subroutineDec("""
#     /** Sets this string to hold a representation of the given value. */
#     method void setInt(int val) {
#     }
# """)

STRING_NEW_LINE = solved_12.STRING_NEW_LINE
# parse_subroutineDec("""
#     /** Returns the new line character. */
#     function char newLine() {
#     }
# """)

STRING_BACK_SPACE = solved_12.STRING_BACK_SPACE
# parse_subroutineDec("""
#     /** Returns the backspace character. */
#     function char backSpace() {
#     }
# """)

STRING_DOUBLE_QUOTE = solved_12.STRING_DOUBLE_QUOTE
# parse_subroutineDec("""
#     /** Returns the double quote (") character. */
#     function char doubleQuote() {
#     }
# """)


# Represents character strings. In addition for constructing and disposing
# strings, the class features methods for getting and setting individual
# characters of the string, for erasing the string's last character,
# for appending a character to the string's end, and more typical
# string-oriented operations.
STRING_CLASS = jack_ast.Class(
    name="String",
    varDecs=STRING_CLASS_VARS,
    subroutineDecs=[
        STRING_NEW,
        STRING_DISPOSE,
        STRING_LENGTH,
        STRING_CHAR_AT,
        STRING_SET_CHAR_AT,
        STRING_APPEND_CHAR,
        STRING_ERASE_LAST_CHAR,
        STRING_INT_VALUE,
        STRING_SET_INT,
        STRING_NEW_LINE,
        STRING_BACK_SPACE,
        STRING_DOUBLE_QUOTE,
    ])