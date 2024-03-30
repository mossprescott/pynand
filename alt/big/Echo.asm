// Read characters from the keyboard and echo them to the screen, starting at the top line.
// - backspace (129) will delete characters to the left, until the beginning of the current line
// - newline (128) moves the insertion point to the beginning of the next line
// - typing off the end of the line wraps to the next line
// - when continuing past the bottom line, the previous 24 lines are "scrolled" up, and the
//   top line is discarded
// - esc (140) stops accepting input, tells the simulator the program is complete
//
// Future: make it a free-form editor, showing a window of 25 lines from a 32K buffer?

//
// Initialize some state:
//

// PREVIOUS_KEY: key code that was down on previous iteration
@PREVIOUS_KEY
M=0
// INSERTION_COLUMN: insertion point column/2
@INSERTION_COLUMN
M=0
// INSERTION_HIGH: insertion point column odd/even flag (i.e. the low bit)
@INSERTION_HIGH
M=0
// CURRENT_LINE: current line
@CURRENT_LINE
M=0


//
// Infinite loop:
//

(loop)
// Read current key down:
@KEYBOARD
D=M

// Compare with previous:
@R0
M=D
@PREVIOUS_KEY
D=M-D
@loop
D;JEQ
@R0
D=M
// Store current key:
@PREVIOUS_KEY
M=D

// Compare with zero (no key down):
@loop
D;JEQ

// Compare with ESC:
@140
D=A
@PREVIOUS_KEY
D=M-D
@halt
D;JEQ

// TODO: backspace (@129)
// TODO: newline (@128)

// R0 = address of insertion point:
// TODO: half-word
@INSERTION_COLUMN
D=M
@SCREEN
D=D+A
@R0
M=D
// Write current key to the screen
@PREVIOUS_KEY
D=M
@R0
A=M
M=D
// Also echo to the TTY for debug purposes
@KEYBOARD
M=D

// Move to the right:
// TODO: half-word at a time
@INSERTION_COLUMN
M=M+1

@loop
0;JMP


//
// Halt loop: required by the harness, but also a place to go on ESC
//

(halt)
@halt
0;JMP
