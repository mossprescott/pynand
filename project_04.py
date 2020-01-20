# See https://www.nand2tetris.org/project04

# SOLVERS: remove this import to get started
from nand.solutions import solved_04


# SOLVERS: MULT_ASM and FILL_ASM should be a lists of strings, each one an assembly instruction.
# 

# Multiplies R0 and R1 and stores the result in R2.
# (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

# MULT_ASM = """
# // Here's where the magic happens:
# (top)  
#   @0
# ...
# """.split('\n')

MULT_ASM = solved_04.MULT_ASM


# Runs an infinite loop that listens to the keyboard input.
# When a key is pressed (any key), the program blackens the screen,
# i.e. writes "black" in every pixel;
# the screen should remain fully black as long as the key is pressed. 
# When no key is pressed, the program clears the screen, i.e. writes
# "white" in every pixel;
# the screen should remain fully clear as long as no key is pressed.

# FILL_ASM = """
# // Here's where the magic happens:
# (top)  
#   @0
# ...
# """.split('\n')

FILL_ASM = solved_04.FILL_ASM