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

# SOLVERS: un-comment and fill in the implementation
STRING_NEW = solved_12.STRING_NEW
# STRING_NEW = parse_subroutineDec("""
#     /** constructs a new empty string with a maximum length of maxLength
#      *  and initial length of 0. */
#     constructor String new(int maxLength) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_DISPOSE = solved_12.STRING_DISPOSE
# STRING_DISPOSE = parse_subroutineDec("""
#     /** Disposes this string. */
#     method void dispose() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_LENGTH = solved_12.STRING_LENGTH
# STRING_LENGTH = parse_subroutineDec("""
#     /** Returns the current length of this string. */
#     method int length() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_CHAR_AT = solved_12.STRING_CHAR_AT
# STRING_CHAR_AT = parse_subroutineDec("""
#     /** Returns the character at the j-th location of this string. */
#     method char charAt(int j) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_SET_CHAR_AT = solved_12.STRING_SET_CHAR_AT
# parse_subroutineDec("""
#     /** Sets the character at the j-th location of this string to c. */
#     method void setCharAt(int j, char c) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
# Note: returning the String itself from this particular method makes it a bit
# more convenient to use this same method in the implementation of String constants.
STRING_APPEND_CHAR = solved_12.STRING_APPEND_CHAR
# STRING_APPEND_CHAR = parse_subroutineDec("""
#     /** Appends c to this string's end and returns this string. */
#     method String appendChar(char c) {
#         ...
#
#         return this;
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_ERASE_LAST_CHAR = solved_12.STRING_ERASE_LAST_CHAR
# STRING_ERASE_LAST_CHAR = parse_subroutineDec("""
#     /** Erases the last character from this string. */
#     method void eraseLastChar() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_INT_VALUE = solved_12.STRING_INT_VALUE
# STRING_INT_VALUE = parse_subroutineDec("""
#     /** Returns the integer value of this string,
#      *  until a non-digit character is detected. */
#     method int intValue() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_SET_INT = solved_12.STRING_SET_INT
# STRING_SET_INT = parse_subroutineDec("""
#     /** Sets this string to hold a representation of the given value. */
#     method void setInt(int val) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_NEW_LINE = solved_12.STRING_NEW_LINE
# STRING_NEW_LINE = parse_subroutineDec("""
#     /** Returns the new line character. */
#     function char newLine() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_BACK_SPACE = solved_12.STRING_BACK_SPACE
# STRING_BACK_SPACE = parse_subroutineDec("""
#     /** Returns the backspace character. */
#     function char backSpace() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
STRING_DOUBLE_QUOTE = solved_12.STRING_DOUBLE_QUOTE
# STRING_DOUBLE_QUOTE = parse_subroutineDec("""
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
# you pass all three tests, your allocator is probably better than what you got
# from your OS/compiler vendor in the 80s.
#

# SOLVERS: put any static state here
# The bundled solution actually doesn't use a static to hold free list head pointer,
# and it's memory layout isn't quite the same as what the course materials describe.
# TODO: adopt the authors' design in solved_12, so that incremental solving will be more
# feasible.
MEMORY_CLASS_VARS = parse_classVarDecs("""
    // static Array freePtr;
""")

# SOLVERS: un-comment and fill in the implementation
MEMORY_INIT = solved_12.MEMORY_INIT
# MEMORY_INIT = parse_subroutineDec("""
#     /** Initializes the class. */
#     function void init() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
MEMORY_PEEK = solved_12.MEMORY_PEEK
# MEMORY_PEEK = parse_subroutineDec("""
#     /** Returns the RAM value at the given address. */
#     function int peek(int address) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
MEMORY_POKE = solved_12.MEMORY_POKE
# MEMORY_POKE = parse_subroutineDec("""
#     /** Sets the RAM value at the given address to the given value. */
#     function void poke(int address, int value) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
MEMORY_ALLOC = solved_12.MEMORY_ALLOC
# MEMORY_ALLOC = parse_subroutineDec("""
#     /** Finds an available RAM block of the given size and returns
#      *  a reference to its base address. */
#     function int alloc(int size) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
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
    // You could pre-allocate a buffer and re-use it for each input; the docs don't really
    // say one way or the other.
    // static String inputBuffer;
""")

# SOLVERS: un-comment and fill in the implementation
KEYBOARD_INIT = solved_12.KEYBOARD_INIT
# KEYBOARD_INIT = parse_subroutineDec("""
#     /** Initializes the keyboard. */
#     function void init() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
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

# SOLVERS: un-comment and fill in the implementation
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

# SOLVERS: un-comment and fill in the implementation
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

# SOLVERS: un-comment and fill in the implementation
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
# Use the provided font and this isn't all that involved.
#

# SOLVERS: if you assume these fields you can implement the methods below one at a time
OUTPUT_CLASS_VARS = parse_classVarDecs("""
    // Character map for displaying characters
    static Array charMaps;

    static int cursorY, cursorX;
    static String temp;
""")

# SOLVERS: un-comment and fill in the implementation
OUTPUT_INIT = solved_12.OUTPUT_INIT
# OUTPUT_INIT = parse_subroutineDec("""
#     /** Initializes the screen, and locates the cursor at the screen's top-left. */
#     function void init() {
#     }
# """)

# SOLVERS: you only need to provide the correct pixels for "A" (character 65) here.
# On the other hand, feel free to go nuts and design your own font. The test only requires
# that A, 6, and 7 are roughly as expected.
OUTPUT_INIT_MAP = solved_12.OUTPUT_INIT_MAP
# OUTPUT_INIT_MAP = parse_subroutineDec("""
#     // Initializes the character map array
#     function void initMap() {
#         var int i;

#         let charMaps = Array.new(127);

#         // Black square, used for displaying non-printable characters.
#         do Output.create(0,63,63,63,63,63,63,63,63,63,0,0);

#         // Assigns the bitmap for each character in the charachter set.
#         // The first parameter is the character index, the next 11 numbers
#         // are the values of each row in the frame that represents this character.
#         do Output.create(32,0,0,0,0,0,0,0,0,0,0,0);          //
#         do Output.create(33,12,30,30,30,12,12,0,12,12,0,0);  // !
#         do Output.create(34,54,54,20,0,0,0,0,0,0,0,0);       // "
#         do Output.create(35,0,18,18,63,18,18,63,18,18,0,0);  // #
#         do Output.create(36,12,30,51,3,30,48,51,30,12,12,0); // $
#         do Output.create(37,0,0,35,51,24,12,6,51,49,0,0);    // %
#         do Output.create(38,12,30,30,12,54,27,27,27,54,0,0); // &
#         do Output.create(39,12,12,6,0,0,0,0,0,0,0,0);        // '
#         do Output.create(40,24,12,6,6,6,6,6,12,24,0,0);      // (
#         do Output.create(41,6,12,24,24,24,24,24,12,6,0,0);   // )
#         do Output.create(42,0,0,0,51,30,63,30,51,0,0,0);     // *
#         do Output.create(43,0,0,0,12,12,63,12,12,0,0,0);     // +
#         do Output.create(44,0,0,0,0,0,0,0,12,12,6,0);        // ,
#         do Output.create(45,0,0,0,0,0,63,0,0,0,0,0);         // -
#         do Output.create(46,0,0,0,0,0,0,0,12,12,0,0);        // .
#         do Output.create(47,0,0,32,48,24,12,6,3,1,0,0);      // /

#         do Output.create(48,12,30,51,51,51,51,51,30,12,0,0); // 0
#         do Output.create(49,12,14,15,12,12,12,12,12,63,0,0); // 1
#         do Output.create(50,30,51,48,24,12,6,3,51,63,0,0);   // 2
#         do Output.create(51,30,51,48,48,28,48,48,51,30,0,0); // 3
#         do Output.create(52,16,24,28,26,25,63,24,24,60,0,0); // 4
#         do Output.create(53,63,3,3,31,48,48,48,51,30,0,0);   // 5
#         do Output.create(54,28,6,3,3,31,51,51,51,30,0,0);    // 6
#         do Output.create(55,63,49,48,48,24,12,12,12,12,0,0); // 7
#         do Output.create(56,30,51,51,51,30,51,51,51,30,0,0); // 8
#         do Output.create(57,30,51,51,51,62,48,48,24,14,0,0); // 9

#         do Output.create(58,0,0,12,12,0,0,12,12,0,0,0);      // :
#         do Output.create(59,0,0,12,12,0,0,12,12,6,0,0);      // ;
#         do Output.create(60,0,0,24,12,6,3,6,12,24,0,0);      // <
#         do Output.create(61,0,0,0,63,0,0,63,0,0,0,0);        // =
#         do Output.create(62,0,0,3,6,12,24,12,6,3,0,0);       // >
#         do Output.create(64,30,51,51,59,59,59,27,3,30,0,0);  // @
#         do Output.create(63,30,51,51,24,12,12,0,12,12,0,0);  // ?

#         do Output.create(65,0,0,0,0,0,0,0,0,0,0,0);          // A ** TO BE FILLED **
#         do Output.create(66,31,51,51,51,31,51,51,51,31,0,0); // B
#         do Output.create(67,28,54,35,3,3,3,35,54,28,0,0);    // C
#         do Output.create(68,15,27,51,51,51,51,51,27,15,0,0); // D
#         do Output.create(69,63,51,35,11,15,11,35,51,63,0,0); // E
#         do Output.create(70,63,51,35,11,15,11,3,3,3,0,0);    // F
#         do Output.create(71,28,54,35,3,59,51,51,54,44,0,0);  // G
#         do Output.create(72,51,51,51,51,63,51,51,51,51,0,0); // H
#         do Output.create(73,30,12,12,12,12,12,12,12,30,0,0); // I
#         do Output.create(74,60,24,24,24,24,24,27,27,14,0,0); // J
#         do Output.create(75,51,51,51,27,15,27,51,51,51,0,0); // K
#         do Output.create(76,3,3,3,3,3,3,35,51,63,0,0);       // L
#         do Output.create(77,33,51,63,63,51,51,51,51,51,0,0); // M
#         do Output.create(78,51,51,55,55,63,59,59,51,51,0,0); // N
#         do Output.create(79,30,51,51,51,51,51,51,51,30,0,0); // O
#         do Output.create(80,31,51,51,51,31,3,3,3,3,0,0);     // P
#         do Output.create(81,30,51,51,51,51,51,63,59,30,48,0);// Q
#         do Output.create(82,31,51,51,51,31,27,51,51,51,0,0); // R
#         do Output.create(83,30,51,51,6,28,48,51,51,30,0,0);  // S
#         do Output.create(84,63,63,45,12,12,12,12,12,30,0,0); // T
#         do Output.create(85,51,51,51,51,51,51,51,51,30,0,0); // U
#         do Output.create(86,51,51,51,51,51,30,30,12,12,0,0); // V
#         do Output.create(87,51,51,51,51,51,63,63,63,18,0,0); // W
#         do Output.create(88,51,51,30,30,12,30,30,51,51,0,0); // X
#         do Output.create(89,51,51,51,51,30,12,12,12,30,0,0); // Y
#         do Output.create(90,63,51,49,24,12,6,35,51,63,0,0);  // Z

#         do Output.create(91,30,6,6,6,6,6,6,6,30,0,0);          // [
#         do Output.create(92,0,0,1,3,6,12,24,48,32,0,0);        // \
#         do Output.create(93,30,24,24,24,24,24,24,24,30,0,0);   // ]
#         do Output.create(94,8,28,54,0,0,0,0,0,0,0,0);          // ^
#         do Output.create(95,0,0,0,0,0,0,0,0,0,63,0);           // _
#         do Output.create(96,6,12,24,0,0,0,0,0,0,0,0);          // `

#         do Output.create(97,0,0,0,14,24,30,27,27,54,0,0);      // a
#         do Output.create(98,3,3,3,15,27,51,51,51,30,0,0);      // b
#         do Output.create(99,0,0,0,30,51,3,3,51,30,0,0);        // c
#         do Output.create(100,48,48,48,60,54,51,51,51,30,0,0);  // d
#         do Output.create(101,0,0,0,30,51,63,3,51,30,0,0);      // e
#         do Output.create(102,28,54,38,6,15,6,6,6,15,0,0);      // f
#         do Output.create(103,0,0,30,51,51,51,62,48,51,30,0);   // g
#         do Output.create(104,3,3,3,27,55,51,51,51,51,0,0);     // h
#         do Output.create(105,12,12,0,14,12,12,12,12,30,0,0);   // i
#         do Output.create(106,48,48,0,56,48,48,48,48,51,30,0);  // j
#         do Output.create(107,3,3,3,51,27,15,15,27,51,0,0);     // k
#         do Output.create(108,14,12,12,12,12,12,12,12,30,0,0);  // l
#         do Output.create(109,0,0,0,29,63,43,43,43,43,0,0);     // m
#         do Output.create(110,0,0,0,29,51,51,51,51,51,0,0);     // n
#         do Output.create(111,0,0,0,30,51,51,51,51,30,0,0);     // o
#         do Output.create(112,0,0,0,30,51,51,51,31,3,3,0);      // p
#         do Output.create(113,0,0,0,30,51,51,51,62,48,48,0);    // q
#         do Output.create(114,0,0,0,29,55,51,3,3,7,0,0);        // r
#         do Output.create(115,0,0,0,30,51,6,24,51,30,0,0);      // s
#         do Output.create(116,4,6,6,15,6,6,6,54,28,0,0);        // t
#         do Output.create(117,0,0,0,27,27,27,27,27,54,0,0);     // u
#         do Output.create(118,0,0,0,51,51,51,51,30,12,0,0);     // v
#         do Output.create(119,0,0,0,51,51,51,63,63,18,0,0);     // w
#         do Output.create(120,0,0,0,51,30,12,12,30,51,0,0);     // x
#         do Output.create(121,0,0,0,51,51,51,62,48,24,15,0);    // y
#         do Output.create(122,0,0,0,63,27,12,6,51,63,0,0);      // z

#         do Output.create(123,56,12,12,12,7,12,12,12,56,0,0);   // {
#         do Output.create(124,12,12,12,12,12,12,12,12,12,0,0);  // |
#         do Output.create(125,7,12,12,12,56,12,12,12,7,0,0);    // }
#         do Output.create(126,38,45,25,0,0,0,0,0,0,0,0);        // ~

# 	    return;
#     }
# """)

# SOLVERS: this is provided for you
OUTPUT_CREATE = parse_subroutineDec("""
    // Creates the character map array of the given character index, using the given values.
    function void create(int index, int a, int b, int c, int d, int e,
                         int f, int g, int h, int i, int j, int k) {
	    var Array map;

	    let map = Array.new(11);
        let charMaps[index] = map;

        let map[0] = a;
        let map[1] = b;
        let map[2] = c;
        let map[3] = d;
        let map[4] = e;
        let map[5] = f;
        let map[6] = g;
        let map[7] = h;
        let map[8] = i;
        let map[9] = j;
        let map[10] = k;

        return;
    }
""")

# SOLVERS: you get this for free, too
OUTPUT_GET_MAP = parse_subroutineDec("""
    // Returns the character map (array of size 11) of the given character.
    // If the given character is invalid or non-printable, returns the
    // character map of a black square.
    function Array getMap(char c) {
        if ((c < 32) | (c > 126)) {
            let c = 0;
        }
        return charMaps[c];
    }
""")

# SOLVERS: un-comment and fill in the implementation
OUTPUT_MOVE_CURSOR = solved_12.OUTPUT_MOVE_CURSOR
# OUTPUT_MOVE_CURSOR = parse_subroutineDec("""
#     /** Moves the cursor to the j-th column of the i-th row,
#      *  and erases the character displayed there. */
#     function void moveCursor(int i, int j) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
OUTPUT_PRINT_CHAR = solved_12.OUTPUT_PRINT_CHAR
# OUTPUT_PRINT_CHAR = parse_subroutineDec("""
#     /** Displays the given character at the cursor location,
#      *  and advances the cursor one column forward. */
#     function void printChar(char c) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
OUTPUT_PRINT_STRING = solved_12.OUTPUT_PRINT_STRING
# OUTPUT_PRINT_STRING = parse_subroutineDec("""
#     /** displays the given string starting at the cursor location,
#      *  and advances the cursor appropriately. */
#     function void printString(String s) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
OUTPUT_PRINT_INT = solved_12.OUTPUT_PRINT_INT
# OUTPUT_PRINT_INT = parse_subroutineDec("""
#     /** Displays the given integer starting at the cursor location,
#      *  and advances the cursor appropriately. */
#     function void printInt(int i) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
OUTPUT_PRINTLN = solved_12.OUTPUT_PRINTLN
# OUTPUT_PRINTLN = parse_subroutineDec("""
#     /** Advances the cursor to the beginning of the next line. */
#     function void println() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
OUTPUT_BACK_SPACE = solved_12.OUTPUT_BACK_SPACE
# OUTPUT_BACK_SPACE = parse_subroutineDec("""
#     /** Moves the cursor one column back. */
#     function void backSpace() {
#     }
# """)

OUTPUT_CLASS = jack_ast.Class(
    name = "Output",
    varDecs=OUTPUT_CLASS_VARS,
    subroutineDecs=[
        OUTPUT_INIT,
        OUTPUT_INIT_MAP,
        OUTPUT_CREATE,
        OUTPUT_GET_MAP,
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
    // Not used by the included solution, but feel free to define and
    // initialize it if you want to follow the authors' plan.
    // static Array twoToThe;
""")

# SOLVERS: un-comment and fill in the implementation
MATH_INIT = solved_12.MATH_INIT
# MATH_INIT = parse_subroutineDec("""
#     /** Initializes the library. */
#     function void init() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
MATH_ABS = solved_12.MATH_ABS
# MATH_ABS = parse_subroutineDec("""
#     /** Returns the absolute value of x. */
#     function int abs(int x) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
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

# SOLVERS: un-comment and fill in the implementation
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

# SOLVERS: un-comment and fill in the implementation
MATH_SQRT = solved_12.MATH_SQRT
# MATH_SQRT = parse_subroutineDec("""
#     /** Returns the integer part of the square root of x. */
#     function int sqrt(int x) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
MATH_MAX = solved_12.MATH_MAX
# MATH_MAX = parse_subroutineDec("""
#     /** Returns the greater number. */
#     function int max(int a, int b) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
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
    static boolean color;

    // Array of 16 masks, each with the corresponding pixel set:
    static Array pixels;

    // Array of 16 masks, each with the corresponding pixel, and its neighbors to the left, set:
    static Array leftPixels;
""")

# SOLVERS: un-comment and fill in the implementation
SCREEN_INIT = solved_12.SCREEN_INIT
# SCREEN_INIT = parse_subroutineDec("""
#     /** Initializes the Screen. */
#     function void init() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SCREEN_CLEAR_SCREEN = solved_12.SCREEN_CLEAR_SCREEN
# SCREEN_CLEAR_SCREEN = parse_subroutineDec("""
#     /** Erases the entire screen. */
#     function void clearScreen() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SCREEN_SET_COLOR = solved_12.SCREEN_SET_COLOR
# SCREEN_SET_COLOR = parse_subroutineDec("""
#     /** Sets the current color, to be used for all subsequent drawXXX commands.
#      *  Black is represented by true, white by false. */
#     function void setColor(boolean b) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SCREEN_DRAW_PIXEL = solved_12.SCREEN_DRAW_PIXEL
# SCREEN_DRAW_PIXEL = parse_subroutineDec("""
#     /** Draws the (x,y) pixel, using the current color. */
#     function void drawPixel(int x, int y) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SCREEN_DRAW_LINE = solved_12.SCREEN_DRAW_LINE
# SCREEN_DRAW_LINE = parse_subroutineDec("""
#     /** Draws a line from pixel (x1,y1) to pixel (x2,y2), using the current color. */
#     function void drawLine(int x1, int y1, int x2, int y2) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SCREEN_DRAW_RECTANGLE = solved_12.SCREEN_DRAW_RECTANGLE
# SCREEN_DRAW_RECTANGLE = parse_subroutineDec("""
#     /** Draws a filled rectangle whose top left corner is (x1, y1)
#      * and bottom right corner is (x2,y2), using the current color. */
#     function void drawRectangle(int x1, int y1, int x2, int y2) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
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

# SOLVERS: un-comment and fill in the implementation
SYS_INIT = solved_12.SYS_INIT
# SYS_INIT = parse_subroutineDec("""
#     /** Performs all the initializations required by the OS. */
#     function void init() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SYS_HALT = solved_12.SYS_HALT
# SYS_HALT = parse_subroutineDec("""
#     /** Halts the program execution. */
#     function void halt() {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
SYS_WAIT = solved_12.SYS_WAIT
# SYS_WAIT = parse_subroutineDec("""
#     /** Waits approximately duration milliseconds and returns.  */
#     function void wait(int duration) {
#     }
# """)

# SOLVERS: un-comment and fill in the implementation
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
