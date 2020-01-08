// Fill the entire screen with a 50% gray pattern, as quickly as possible, or nearly. About 20k cycles.

  @SCREEN
  D=A
  @ptr
  M=D  

  @0x5555
  D=A
  @pixels
  M=D

  // initialize the loop var:
  @256
  D=A
  @count
  M=D

(loop)
  // Flip pixels from previous line:
  @pixels
  M=!M
  
  @_1
  D=A
  @return
  M=D
  
  @copy
  0;JMP
  
(_1)
  @count
  DM=M-1
  @loop
  D;JGT

(halt)
  @halt
  0;JMP
  


(copy)
  // Copy one word to one entire scanline of pixels, as fast as possible (2 instructions per 16 pixels,
  // about 16k instructions for the whole screen):
  // @pixels: 16 pixels
  // @ptr: the address to start copying to
  // @return: address to jump to after
  // on return, @ptr points to the next line
  
  @pixels
  D=M
  
  @ptr
  A=M
  
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  M=D
  A=A+1
  
  // update @ptr
  D=A
  @ptr
  M=D
  
  @return
  A=M
  0;JMP
