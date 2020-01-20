"""Solutions for project 04.

SPOILER ALERT: this files contains complete solutions for all the exercises.
If you want to solve them on your own, stop reading now!
"""

# Disclaimer: these solutions aren't especially elegant.


MULT_ASM = """
  // Initialize R2 to 0
  @R2
  M=0
  
  // Test for R1 == 0 and exit early
  @R1
  D=M
  @halt
  D;JLE
  
(loop)
  @R0
  D=M
  @halt
  D;JLE

  // Add R1 to R2:
  @1
  D=M
  @R2
  M=D+M
  
  // Subtract 1 from R0 (in place)
  @R0
  M=M-1
  
  @loop
  0;JMP

(halt)
    
""".split('\n')


FILL_ASM = """
(top)
  @KEYBOARD
  D=M
  @black
  D;JNE

(white)
  @R0
  M=0
  @start
  0;JMP

(black)
  @R0
  M=-1

(start)
  // Initialize R1 to point to the first word of screen RAM
  @SCREEN
  D=A
  @R1
  M=D

(loop)
  // Test if R1 is at the end (i.e. points to @KEYBOARD); if so, back to the beginning
  @R1
  D=M
  @KEYBOARD
  D=D-A
  @top
  D;JGE
  
  // Fill the current word with the appropriate pixels:
  @R0
  D=M
  @R1
  A=M
  M=D
  
  // Increment R1
  @R1
  M=M+1

  @loop
  0;JMP
""".split('\n')