# Alternative Chips and Tools

This directory contains additional chip designs, built using the same tools from the `nand` package.

Each module contains all the required pieces to simulate a chip and translate and run VM programs on it.

See each module for instructions.



| Location                         | Nands        | ROM size       | Cycles per frame | Cycles for init    | Notes  |
|----------------------------------|-------------:|---------------:|-----------------:|-------------------:|--------|
| project_0*.py                    | 1,262        |         26,382 |           32,762 |            129,500 | This is the standard design from nand2tetris, with a reasonably efficient compiler and translator. |
| [alt/lazy.py](lazy.py)           | _same_       |   24,243 (-8%) |    28,962 (-12%) |     111,300 (-14%) | A slighty cleverer translator for the standard CPU, which avoids updating the stack when that's easy to do. |
| [alt/sp.py](sp.py)               | 1,844 (+46%) |  14,517 (-45%) |    20,957 (-36%) |      76,200 (-41%) | Adds instructions for pushing/popping values to/from the stack, making programs more compact. |
| [alt/threaded.py](threaded.py)  | 1,549 (+23%) |   8,280 (-69%) |    41,103 (+26%) |     173,750 (+34%) | Adds lightweight CALL/RTN instructions, enabling a very compact "threaded interpreter" translation, which runs a little slower. |
| [alt/shift.py](shift.py)         | 1,311 (+4%)  | 26,740 (+1.4%) |    *32,762 (-0%)* |   *129,500 (-0%)* | Adds a "shiftr" instruction, and rewrites "push constant 16; call Math.divide" to use it instead; also a more efficient Math.multiply using shiftr. See note below. |
| [alt/eight.py](eight.py)         | 1,032 (-18%) | _same_         |            +100% |              +100% | Finally, a _smaller_ CPU, by using an 8-bit ALU and 2 cycles per instruction. |
| [alt/reg.py](reg.py)             | _same_       |  21,393 (-21%) |    19,647 (-40%) |      68,100 (-47%) | A much more ambititous compiler, which uses the "registers" at locations 5-12 for transient local variables and expression evaluation, reserving the stack only for subroutine calls and locals that cross them. |

**ROM Size** is the total number of instructions in ROM when Pong is translated from the same Jack
sources.

**Cycles per frame** is the number of cycles to run the first iteration of the Pong game loop.
Specifically, this includes `Bat.move` and `PongGame.moveBall`, and _not_ `Sys.wait`.

**Cycles for init** is the number of cycles from start to reaching `call Main.main 0`. That is,
the number of cycles to execute all of the common setup code in `Sys.init`.

Note: `alt/shift.py` is no longer showing any benefit after switching to use the bundled OS
implementation. There are two major factors:
- the bundled `Screen` class unrolls `Math.multiply` and `Math.divide` calls which otherwise
  take most of the time during drawing. Without that inlining, shift.py achieves a
  64% speedup on cycles per frame.
- the authors' included `Output` class spends millions of cycles initializing a separate
  "shifted" map for each character (by multiplying each of the 11 entries by 256.) The bundled
  implementation does this shifting at runtime (and unrolls it), so it's much less affected by
  multiply performance.
