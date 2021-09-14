# Alternative Chips and Tools

This directory contains additional chip designs, built using the same tools from the `nand` package.

Each module contains all the required pieces to simulate a chip and translate and run VM programs on it.

See each module for instructions.



| Location                         | Nands        | ROM size       | Cycles per frame | Cycles for init    | Notes  |
|----------------------------------|-------------:|---------------:|-----------------:|-------------------:|--------|
| project_0*.py                    | 1,262        |         25,700 |           41,450 |            129,200 | This is the standard design from nand2tetris, with a reasonably efficient compiler and translator. |
| [alt/lazy.py](lazy.py)           | _same_       |   23,650 (-8%) |    37,300 (-10%) |     111,000 (-14%) | A slighty cleverer translator for the standard CPU, which avoids updating the stack when that's easy to do. |
| [alt/sp.py](sp.py)               | 1,844 (+46%) |  14,150 (-45%) |    27,440 (-34%) |      76,240 (-41%) | Adds instructions for pushing/popping values to/from the stack, making programs more compact. |
| [alt/threaded.py](threaded.py)  | 1,549 (+23%) |    8,100 (-68%) |    49,600 (+20%) |     173,750 (+34%) | Adds lightweight CALL/RTN instructions, enabling a very compact "threaded interpreter" translation, which runs a little slower. |
| [alt/shift.py](shift.py)         | 1,311 (+4%)  |   26,050 (+1%) |    19,800 (-52%) |        129,200 (–) | Adds a "shiftr" instruction, and rewrites "push constant 16; call Math.divide" to use it instead; also a more efficient Math.multiply using shiftr. |
| [alt/eight.py](eight.py)         | 1,032 (-18%) | _same_         |            +100% |              +100% | Finally, a _smaller_ CPU, by using an 8-bit ALU and 2 cycles per instruction. |
| [alt/reg.py](reg.py)             | _same_       |  20,900 (-19%) |    19,150 (-54%) |      59,000 (-54%) | A much more ambititous compiler, which uses the "registers" at locations 5-12 for transient local variables and expression evaluation, reserving the stack only for subroutine calls and locals that cross them. |
| [alt/reduce.py](reduce.py)       | _same_       | 27,350 (+6.5%) |    20,300 (-51%) |        129,200 (–) | Adds an optimizaation phase after parsing and before the normal compiler runs, which replaces certain function calls with lower-overhead "reduced" alternatives. |

**ROM Size** is the total number of instructions in ROM when Pong is compiled and translated
from the same Jack sources.

**Cycles per frame** is the number of cycles to run the first iteration of the Pong game loop.
Specifically, this includes `Bat.move` and `PongGame.moveBall`, and _not_ `Screen.clearScreen`
or `Sys.wait`.

**Cycles for init** is the number of cycles from start to reaching `call Main.main 0`. That is,
the number of cycles to execute all of the common setup code in `Sys.init`.
