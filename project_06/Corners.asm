// Draw some single pixels in each corner

  @1
  D=A
  @16384
  M=D

  @2
  D=A
  @16416
  M=D

  @4
  D=A
  @16448
  M=D

  @8
  D=A
  @16480
  M=D


  @16384
  D=A
  D=D+A  // i.e. unsigned 32768
  @16415
  M=D

  @16384
  D=A
  @16447
  M=D

  @8192
  D=A
  @16479
  M=D

  @4096
  D=A
  @16511
  M=D


  @8
  D=A
  @24448
  M=D

  @4
  D=A
  @24480
  M=D

  @2
  D=A
  @24512
  M=D

  @1
  D=A
  @24544
  M=D


  @4096
  D=A
  @24479
  M=D

  @8192
  D=A
  @24511
  M=D

  @16384
  D=A
  @24543
  M=D

  @16384
  D=A
  D=D+A  // i.e. unsigned 32768
  @24575
  M=D


(loop)
  @loop
  0;JMP