// Test of writing to the screen, hand-written in assembly for maximum simplicity.

(black)
  // R8 = SCREEN + 32*15
  @16864
  D=A
  @R8
  M=D

(black_loop)
  // write 16 black pixels at R8
  @R8
  A=M
  M=-1
  
  // compare R8 with SCREEN
  D=A
  @SCREEN
  D=D-A
  @black_done
  D;JEQ
  
  // move R8 up one line (32 words)
  @32
  D=A
  @R8
  M=M-D
  @black_loop
  0;JMP
  
(black_done)
  // spin loop using R9 for visibility
  @1000
  D=A
  @R9
  M=D
(black_done_loop)
  @R9
  DM=M-1
  // D=M-1
  // M=D
  @black_done_loop
  D;JGT
  // fall through to (white)

(white)
  // R8 = SCREEN + 32*15
  @16864
  D=A
  @R8
  M=D

(white_loop)
  // write 16 white pixels at R8
  @R8
  A=M
  M=0
  
  // compare R8 with SCREEN
  D=A
  @SCREEN
  D=D-A
  @white_done
  D;JEQ
  
  // move R8 up one line (32 words)
  @32
  D=A
  @R8
  M=M-D
  @white_loop
  0;JMP
  
(white_done)
  // spin loop using R9 for visibility
  @1000
  D=A
  @R9
  M=D
(white_done_loop)
  @R9
  DM=M-1
  @white_done_loop
  D;JGT
  
  @black
  0;JMP

