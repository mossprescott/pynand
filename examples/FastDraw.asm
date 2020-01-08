// Fill the entire screen with junk as quickly as possible. About 10k cycles.

  @SCREEN
  D=A
  @ptr
  M=D  

  // initialize the loop var:
  @256
  D=A
  @count
  M=D

(loop)
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
  // Write nonsense to an entire scanline of pixels, as fast as possible (1 instructions per 16 pixels,
  // about 8k instructions for the whole screen):
  // @ptr: the address to start copying to
  // @return: address to jump to after
  // on return, @ptr points to the next line
  
  @ptr
  A=M
  
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  AM=A+1
  
  // update @ptr
  D=A
  @ptr
  M=D
  
  @return
  A=M
  0;JMP
