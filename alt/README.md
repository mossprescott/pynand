# Alternative Chips and Tools

This directory contains additional chip and/or compiler designs, built using the same tools from the `nand` package.

Each module contains all the required pieces to simulate a chip and translate and run VM programs on it.

See each module for instructions.

## Enhanced chips

Four alternative implementations use more or less chip hardware to make programs run faster, or to fit larger programs in ROM:

[alt/sp.py](sp.py) adds instructions for pushing/popping values to/from the stack, making programs more compact.

[alt/threaded.py](threaded.py) adds lightweight CALL/RTN instructions, enabling a very compact "threaded interpreter" translation, which runs a little slower.

[alt/shift.py](shift.py) adds a "shiftr" instruction, and rewrites "push constant 16; call Math.divide" to use it instead; also a more efficient Math.multiply using shiftr.

[alt/eight.py](eight.py) is, finally, a _smaller_ CPU, by using an 8-bit ALU and 2 cycles per instruction.

## Enhanced compiler/translators

These implementations all use the standard CPU, and try to generate more efficient code for it:

[alt/lazy.py](lazy.py) has a slighty cleverer translator which avoids updating the stack when that's easy to do.

[alt/reg.py](reg.py) is a much more ambititous compiler which uses the "registers" at locations 5-12 for transient
local variables and expression evaluation, reserving the stack only for subroutine calls and locals that cross them.

[alt/reduce.py](reduce.py) adds an optimization phase after parsing and before the normal compiler runs, which
replaces certain function calls with lower-overhead "reduced" alternatives.

## Alternative architectures

[alt/risc/](risc/) implements an entirely different CPU design, which uses a much larger register
file, a simpler ALU, and different branch/jump instructions. That doesn't really pay off when
translating the standard VM, which spends most of its time pushing values on and off of the stack.
When the "reg" compiler is retargeted to it, it gets a lot more done in every cycle.

## Results

| Location                         | Nands        | ROM size       | Cycles per frame | Cycles for init    |
|----------------------------------|-------------:|---------------:|-----------------:|-------------------:|
| project_0*.py                    | 1,262        |         25,700 |           41,450 |            129,200 |
| [alt/sp.py](sp.py)               | 1,844 (+46%) |  14,150 (-45%) |    27,440 (-34%) |      76,240 (-41%) |
| [alt/threaded.py](threaded.py)   | 1,549 (+23%) |   8,100 (-68%) |    49,600 (+20%) |     173,750 (+34%) |
| [alt/shift.py](shift.py)         | 1,311 (+4%)  |   26,050 (+1%) |    19,800 (-52%) |             _same_ |
| [alt/eight.py](eight.py)         | 1,032 (-18%) |        _same_  |            +100% |              +100% |
| [alt/lazy.py](lazy.py)           | _same_       |   23,650 (-8%) |    37,300 (-10%) |     111,000 (-14%) |
| [alt/reg.py](reg.py)             | _same_       |  20,900 (-19%) |    19,150 (-54%) |      59,000 (-54%) |
| [alt/reduce.py](reduce.py)       | _same_       | 27,350 (+6.5%) |    20,300 (-51%) |             _same_ |
| [alt/risc/](risc/__init__.py) (simple) | 2,455 (+94%) |  19,011 (-26%) |    21,300 (-49%) |      64,350 (-50%) |
| [alt/risc/](risc/reg.py) (reg)   | 2,455 (+94%) |  11,700 (-54%) |    12,250 (-70%) |      29,600 (-77%) |

**ROM Size** is the total number of instructions in ROM when Pong is compiled and translated
from the Jack source.

**Cycles per frame** is the number of cycles to run the first iteration of the Pong game loop.
Specifically, this includes `Bat.move` and `PongGame.moveBall`, and _not_ `Screen.clearScreen`
or `Sys.wait`.

**Cycles for init** is the number of cycles from start to reaching `call Main.main 0`. That is,
the number of cycles to execute all of the common setup code in `Sys.init`.

The measurements in the table are all produced by [alt/compare.py](compare.py), slightly cleaned up.

## Commentary

Note: reduce.py and shift.py produce similar improvements, because they both optimize the important case of
division by a constant equal to 2^n. It's interesting that a similar improvement is achieved with either 5%
more chip area or 6% more ROM space, but that comparison isn't entirely fair for various reasons.

Furthermore, because reduce.py's optimizations run so early, they can actually be combined with any of the
other implementations for a compound effect. In particular, when reduce.py introduces additional temporary
variables and removes function calls, reg.py will handle those changes especially well and that combination
comes closest to emulating a "modern" optimizing compiler. Those results aren't shown here.
