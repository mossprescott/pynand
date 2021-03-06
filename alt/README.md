# Alternative Chips and Tools

This directory contains additional chip designs, built using the same tools from the `nand` package.

Each module contains all the required pieces to simulate a chip and translate and run VM programs on it.

See each module for instructions.



| Location       | Nands        | ROM size       | Cycles per frame | Cycles for init    | Notes  |
|----------------|-------------:|---------------:|-----------------:|-------------------:|--------|
| project_0*.py  | 1,262        |         28,300 |           34,415 |         4 million  | This is the standard design from nand2tetris, with a reasonably efficient VM translator. |
| alt/lazy.py    | _same_       |   25,700 (-9%) |    29,245 (-15%) | 3.2 million (-18%) | A slighty cleverer translator for the standard CPU, which avoids updating the stack when that's easy to do. |
| alt/sp.py      | 1,844 (+46%) |  15,800 (-44%) |    21,877 (-36%) | 2.5 million (-36%) | Adds instructions for pushing/popping values to/from the stack, making programs more compact. |
| alt/threaded.py| 1,549 (+23%) |   8,700 (-69%) |    43,336 (+26%) | 5.1 million (+29%) | Adds lightweight CALL/RTN instructions, enabling a very compact "threaded interpreter" translation. |
| alt/shift.py   | 1,311 (+4%)  | 28,300 (-0.1%) |    16,735 (-51%) | 3.5 million (-11%) | Adds a "shiftr" instruction, and rewrites "push constant 16; call Math.divide" to use it instead; also a more efficient Math.multiply using shiftr. |
| alt/eight.py   | 1,032 (-18%) | _same_         |           +100%  |              +100% | Finally, a _smaller_ CPU, by using an 8-bit ALU and 2 cycles per instruction. |

*ROM Size* is the total number of instructions in ROM when Pong is translated from the same VM 
sources.

*Cycles per frame* is the number of cycles to run the first iteration of the Pong game loop. 
Specifically, this includes `Bat.move` and `PongGame.moveBall`, and _not_ `Sys.wait`.

*Cycles for init* is the number of cycles from start to reaching `call Main.main 0`. That is,
the number of cycles to execute all of the common setup code in `Sys.init`.
