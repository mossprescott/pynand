// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/06/max/Max.asm

// Computes R3 = max(R1, R2)  (R1,R2,R3 refer to RAM[1],RAM[2],RAM[3])
// Note: modified to avoid R0 (SP), which may get special treatment

   @R1
   D=M              // D = first number
   @R2
   D=D-M            // D = first number - second number
   @OUTPUT_FIRST
   D;JGT            // if D>0 (first is greater) goto output_first
   @R2
   D=M              // D = second number
   @OUTPUT_D
   0;JMP            // goto output_d
(OUTPUT_FIRST)
   @R1             
   D=M              // D = first number
(OUTPUT_D)
   @R3
   M=D              // M[2] = D (greatest number)
(INFINITE_LOOP)
   @INFINITE_LOOP
   0;JMP            // infinite loop
