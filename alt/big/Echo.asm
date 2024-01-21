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

// R0: previous key code
@R0
M=0
// R1: insertion point column/2
@R1
M=0
// R2: insertion point column odd/even flag (i.e. the low bit)
@R2
M=0
// R3: current line
@R3
M=0


//
// Infinite loop:
//

(loop)
// Read current key down:
@KEYBOARD
D=M

// Compare with previous:
@R5
M=D
@R0
D=M-D
@loop
D;JEQ
@R5
D=M
// Store current key:
@R0
M=D

// Compare with zero (no key down):
@loop
D;JEQ

// Compare with ESC:
@140
D=A
@R0
D=M-D
@halt
D;JEQ

// TODO: backspace (@129)
// TODO: newline (@128)

// R5 = address of insertion point:
// TODO: half-word
@R1
D=M
@SCREEN
D=D+A
@R5
M=D
// Write current key to the screen
@R0
D=M
@R5
A=M
M=D
// Also echo to the TTY for debug purposes
@KEYBOARD
M=D

// Move to the right:
// TODO: half-word at a time
@R1
M=M+1

@loop
0;JMP


//
// Halt loop: required by the harness, but also a place to go on ESC
//

(halt)
@halt
0;JMP
