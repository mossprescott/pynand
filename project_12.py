# Operating System
#
# See https://www.nand2tetris.org/project12

from re import sub
from nand import parsing, jack_ast

import project_10

# SOLVERS: remove this import when you've implemented all the tagged fragments
from nand.solutions import solved_12


def parse_classVarDecs(src):
    return parsing.ManyP(project_10.ClassVarDecP).parse(project_10.lex(src))

def parse_subroutineDec(src):
    return project_10.SubroutineDecP.parse(project_10.lex(src))


#
# Array Library
#
# This is the simplest of the classes that make up the "OS" library.
# Your implementation should require no state and just a line or two
# per function.
#

# SOLVERS: You can define static and field variables here if you need them.
ARRAY_CLASS_VARS = parse_classVarDecs("""
    // static int ...;
    // field int ...;
""")


# SOLVERS: un-comment and fill in the implementation
ARRAY_NEW = solved_12.ARRAY_NEW
# ARRAY_NEW = """
#     /** Constructs a new Array of the given size. */
#     function Array new(int size) {
#
#     }
# """

# Example: this is probably the simplest method in the whole library.
ARRAY_DISPOSE = parse_subroutineDec("""
    /** Disposes this array. */
    method void dispose() {
      do Memory.deAlloc(this);
      return;
    }
""")

# Here's where the pieces get put together into an AST node that the compiler can consume:
ARRAY_CLASS = jack_ast.Class(
    name="Array",
    varDecs=ARRAY_CLASS_VARS,
    subroutineDecs=[
        ARRAY_NEW,
        ARRAY_DISPOSE,
    ])


#
# String Library
#
# These operations on Strings require a little more thought and considerably more code.
#

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


#
# Memory Library
#
# This class is mixed bag. peek() and poke() should be just a couple if lines each,
# once you figure out how to bend Array references to your will.
#
# A simple implementation of alloc() which doesn't re-use freed blocks can be quite
# simple (and will pass the first test). A more complete implementation can get pretty
# complex. The second test requires the most simple kind of re-use, and the third test
# tries to trip up your allocator by repeatedly allocating different-sized blocks. If
# you pass all three tests, your allocator
#

# SOLVERS: if you assume these fields you can implement the methods below one at a time
MEMORY_CLASS_VARS = parse_classVarDecs("""
    // static Array freePtr;
""")

MEMORY_INIT = solved_12.MEMORY_INIT
# MEMORY_INIT = parse_subroutineDec("""
#     /** Initializes the class. */
#     function void init() {
#     }
# """)

MEMORY_PEEK = solved_12.MEMORY_PEEK
# MEMORY_PEEK = parse_subroutineDec("""
#     /** Returns the RAM value at the given address. */
#     function int peek(int address) {
#     }
# """)

MEMORY_POKE = solved_12.MEMORY_POKE
# MEMORY_POKE = parse_subroutineDec("""
#     /** Sets the RAM value at the given address to the given value. */
#     function void poke(int address, int value) {
#     }
# """)

MEMORY_ALLOC = solved_12.MEMORY_ALLOC
# MEMORY_ALLOC = parse_subroutineDec("""
#     /** Finds an available RAM block of the given size and returns
#      *  a reference to its base address. */
#     function int alloc(int size) {
#     }
# """)

MEMORY_DE_ALLOC = solved_12.MEMORY_DE_ALLOC
# MEMORY_DE_ALLOC = parse_subroutineDec("""
#     /** De-allocates the given object (cast as an array) by making
#      *  it available for future allocations. */
#     function void deAlloc(Array o) {
#     }
# """)

MEMORY_CLASS = jack_ast.Class(
    name="Memory",
    varDecs=MEMORY_CLASS_VARS,
    subroutineDecs=[
        MEMORY_INIT,
        MEMORY_PEEK,
        MEMORY_POKE,
        MEMORY_ALLOC,
        MEMORY_DE_ALLOC,
    ])


#
# Keyboard Library
#
# Welcome to the world of real-time user interaction! Not a lot of code here, but probably
# some tricky cases to handle, and no real substitue for testing with the UI:
# ./computer.py .../KeyboardTest/
#

# SOLVERS: if you assume these fields you can implement the methods below one at a time
KEYBOARD_CLASS_VARS = parse_classVarDecs("""
""")

KEYBOARD_INIT = solved_12.KEYBOARD_INIT
# KEYBOARD_INIT = parse_subroutineDec("""
#     /** Initializes the keyboard. */
#     function void init() {
#     }
# """)

KEYBOARD_KEY_PRESSED = solved_12.KEYBOARD_KEY_PRESSED
# KEYBOARD_KEY_PRESSED = parse_subroutineDec("""
#     /**
#      * Returns the character of the currently pressed key on the keyboard;
#      * if no key is currently pressed, returns 0.
#      *
#      * Recognizes all ASCII characters, as well as the following keys:
#      * new line = 128 = String.newline()
#      * backspace = 129 = String.backspace()
#      * left arrow = 130
#      * up arrow = 131
#      * right arrow = 132
#      * down arrow = 133
#      * home = 134
#      * End = 135
#      * page up = 136
#      * page down = 137
#      * insert = 138
#      * delete = 139
#      * ESC = 140
#      * F1 - F12 = 141 - 152
#      */
#     function char keyPressed() {
#     }
# """)

KEYBOARD_READ_CHAR = solved_12.KEYBOARD_READ_CHAR
# KEYBOARD_READ_CHAR = parse_subroutineDec("""
#      /**
#      * Waits until a key is pressed on the keyboard and released,
#      * then echoes the key to the screen, and returns the character
#      * of the pressed key.
#      */
#     function char readChar() {
#     }
# """)

KEYBOARD_READ_LINE = solved_12.KEYBOARD_READ_LINE
# KEYBOARD_READ_LINE = parse_subroutineDec("""
#      /**
#      * Displays the message on the screen, reads from the keyboard the entered
#      * text until a newline character is detected, echoes the text to the screen,
#      * and returns its value. Also handles user backspaces.
#      */
#     function String readLine(String message) {
#     }
# """)

KEYBOARD_READ_INT = solved_12.KEYBOARD_READ_INT
# KEYBOARD_READ_INT = parse_subroutineDec("""
#      /**
#      * Displays the message on the screen, reads from the keyboard the entered
#      * text until a newline character is detected, echoes the text to the screen,
#      * and returns its integer value (until the first non-digit character in the
#      * entered text is detected). Also handles user backspaces.
#      */
#     function int readInt(String message) {
#     }
# """)

KEYBOARD_CLASS = jack_ast.Class(
    name = "Keyboard",
    varDecs=KEYBOARD_CLASS_VARS,
    subroutineDecs=[
        KEYBOARD_INIT,
        KEYBOARD_KEY_PRESSED,
        KEYBOARD_READ_CHAR,
        KEYBOARD_READ_LINE,
        KEYBOARD_READ_INT,
    ])


#
# Output Library
#
# Use the provided font and this isn't too bad, all things considered. Or stretch
# yourself and come up with an implementation that doesn't need millions of cycles
# to initialize itself!
#

# SOLVERS: if you assume these fields you can implement the methods below one at a time
OUTPUT_CLASS_VARS = parse_classVarDecs("""
    // Character map for displaying characters
    static Array charMaps;

    static int cursorY, cursorX;
    static String temp;
""")

OUTPUT_INIT = solved_12.OUTPUT_INIT
# TODO
OUTPUT_MOVE_CURSOR = solved_12.OUTPUT_MOVE_CURSOR
OUTPUT_PRINT_CHAR = solved_12.OUTPUT_PRINT_CHAR
OUTPUT_PRINT_STRING = solved_12.OUTPUT_PRINT_STRING
OUTPUT_PRINT_INT = solved_12.OUTPUT_PRINT_INT
OUTPUT_PRINTLN = solved_12.OUTPUT_PRINTLN
OUTPUT_BACK_SPACE = solved_12.OUTPUT_BACK_SPACE

OUTPUT_CLASS = jack_ast.Class(
    name = "Output",
    varDecs=OUTPUT_CLASS_VARS,
    subroutineDecs=[
        OUTPUT_INIT,
        OUTPUT_MOVE_CURSOR,
        OUTPUT_PRINT_CHAR,
        OUTPUT_PRINT_STRING,
        OUTPUT_PRINT_INT,
        OUTPUT_PRINTLN,
        OUTPUT_BACK_SPACE,
    ])


#
# Math Library
#
# Take your time, read carefully, and remember to handle the edge cases!
#

# SOLVERS: if you assume these fields you can implement the methods below one at a time
MATH_CLASS_VARS = parse_classVarDecs("""
""")

MATH_INIT = solved_12.MATH_INIT
# MATH_INIT = parse_subroutineDec("""
#     /** Initializes the library. */
#     function void init() {
#     }
# """)

MATH_ABS = solved_12.MATH_ABS
# MATH_ABS = parse_subroutineDec("""
#     /** Returns the absolute value of x. */
#     function int abs(int x) {
#     }
# """)

MATH_MULTIPLY = solved_12.MATH_MULTIPLY
# MATH_MULTIPLY = parse_subroutineDec("""
#     /** Returns the product of x and y.
#      *  When a Jack compiler detects the multiplication operator '*' in the
#      *  program's code, it handles it by invoking this method. In other words,
#      *  the Jack expressions x*y and Math.multiply(x,y) return the same value.
#      */
#     function int multiply(int x, int y) {
#     }
# """)

MATH_DIVIDE = solved_12.MATH_DIVIDE
# MATH_DIVIDE = parse_subroutineDec("""
#     /** Returns the integer part of x/y.
#      *  When a Jack compiler detects the multiplication operator '/' in the
#      *  program's code, it handles it by invoking this method. In other words,
#      *  the Jack expressions x/y and Math.divide(x,y) return the same value.
#      */
#     function int divide(int x, int y) {
#     }
# """)

MATH_SQRT = solved_12.MATH_SQRT
# MATH_SQRT = parse_subroutineDec("""
#     /** Returns the integer part of the square root of x. */
#     function int sqrt(int x) {
#     }
# """)

MATH_MAX = solved_12.MATH_MAX
# MATH_MAX = parse_subroutineDec("""
#     /** Returns the greater number. */
#     function int max(int a, int b) {
#     }
# """)

MATH_MIN = solved_12.MATH_MIN
# MATH_MIN = parse_subroutineDec("""
#     /** Returns the smaller number. */
#     function int min(int a, int b) {
#     }
# """)

# Here's where the pieces get put together into an AST node that the compiler can consume:
MATH_CLASS = jack_ast.Class(
    name="Math",
    varDecs=MATH_CLASS_VARS,
    subroutineDecs=[
        MATH_INIT,
        MATH_ABS,
        MATH_MULTIPLY,
        MATH_DIVIDE,
        MATH_SQRT,
        MATH_MAX,
        MATH_MIN,
    ])

#
# Screen Library
#
# Lots of details to attend to here, and fairly important to handle some
# common "easy" cases to get decent speed.
#

# SOLVERS: if you assume these fields you can implement the methods below one at a time
SCREEN_CLASS_VARS = parse_classVarDecs("""
""")

SCREEN_INIT = solved_12.SCREEN_INIT
# SCREEN_INIT = parse_subroutineDec("""
#     /** Initializes the Screen. */
#     function void init() {
#     }
# """)

SCREEN_CLEAR_SCREEN = solved_12.SCREEN_CLEAR_SCREEN
# SCREEN_CLEAR_SCREEN = parse_subroutineDec("""
#     /** Erases the entire screen. */
#     function void clearScreen() {
#     }
# """)

SCREEN_SET_COLOR = solved_12.SCREEN_SET_COLOR
# SCREEN_SET_COLOR = parse_subroutineDec("""
#     /** Sets the current color, to be used for all subsequent drawXXX commands.
#      *  Black is represented by true, white by false. */
#     function void setColor(boolean b) {
#     }
# """)

SCREEN_DRAW_PIXEL = solved_12.SCREEN_DRAW_PIXEL
# SCREEN_DRAW_PIXEL = parse_subroutineDec("""
#     /** Draws the (x,y) pixel, using the current color. */
#     function void drawPixel(int x, int y) {
#     }
# """)

SCREEN_DRAW_LINE = solved_12.SCREEN_DRAW_LINE
# SCREEN_DRAW_LINE = parse_subroutineDec("""
#     /** Draws a line from pixel (x1,y1) to pixel (x2,y2), using the current color. */
#     function void drawLine(int x1, int y1, int x2, int y2) {
#     }
# """)

SCREEN_DRAW_RECTANGLE = solved_12.SCREEN_DRAW_RECTANGLE
# SCREEN_DRAW_RECTANGLE = parse_subroutineDec("""
#     /** Draws a filled rectangle whose top left corner is (x1, y1)
#      * and bottom right corner is (x2,y2), using the current color. */
#     function void drawRectangle(int x1, int y1, int x2, int y2) {
#     }
# """)

SCREEN_DRAW_CIRCLE = solved_12.SCREEN_DRAW_CIRCLE
# SCREEN_DRAW_CIRCLE = parse_subroutineDec("""
#     /** Draws a filled circle of radius r<=181 around (x,y), using the current color. */
#     function void drawCircle(int x, int y, int r) {
#     }
# """)

# Here's where the pieces get put together into an AST node that the compiler can consume:
SCREEN_CLASS = jack_ast.Class(
    name="Screen",
    varDecs=SCREEN_CLASS_VARS,
    subroutineDecs=[
        SCREEN_INIT,
        SCREEN_CLEAR_SCREEN,
        SCREEN_SET_COLOR,
        SCREEN_DRAW_PIXEL,
        SCREEN_DRAW_LINE,
        SCREEN_DRAW_RECTANGLE,
        SCREEN_DRAW_CIRCLE,
    ])


#
# Sys Library
#
# If you made it this far, the Sys class should be a walk in the park. Consider it your victory
# lap.
#

# SOLVERS: put any static/field variables here, if you need them:
SYS_CLASS_VARS = parse_classVarDecs("""
""")

SYS_INIT = solved_12.SYS_INIT
# SYS_INIT = parse_subroutineDec("""
#     /** Performs all the initializations required by the OS. */
#     function void init() {
#     }
# """)


SYS_HALT = solved_12.SYS_HALT
# SYS_HALT = parse_subroutineDec("""
#     /** Halts the program execution. */
#     function void halt() {
#     }
# """)

SYS_WAIT = solved_12.SYS_WAIT
# SYS_WAIT = parse_subroutineDec("""
#     /** Waits approximately duration milliseconds and returns.  */
#     function void wait(int duration) {
#     }
# """)

SYS_ERROR = solved_12.SYS_ERROR
# SYS_ERROR = parse_subroutineDec("""
#     /** Displays the given error code in the form "ERR<errorCode>",
#      *  and halts the program's execution. */
#     function void error(int errorCode) {
#     }
# """)


# Here's where the pieces get put together into an AST node that the compiler can consume:
SYS_CLASS = jack_ast.Class(
    name="Sys",
    varDecs=SYS_CLASS_VARS,
    subroutineDecs=[
        SYS_INIT,
        SYS_HALT,
        SYS_WAIT,
        SYS_ERROR,
    ])


# Put it all together:

OS_CLASSES = [
    ARRAY_CLASS,
    STRING_CLASS,
    MEMORY_CLASS,
    KEYBOARD_CLASS,
    OUTPUT_CLASS,
    MATH_CLASS,
    SCREEN_CLASS,
    SYS_CLASS,
]