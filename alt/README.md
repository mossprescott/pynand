# Alternative Chips and Tools

This directory contains additional chip designs, built using the same tools from the `nand` package.

Each module contains all the required pieces to simulate a chip and translate and run VM programs on it.

See each module for instructions.



| Location       | Nands | ROM words for Pong | Cycles for Sys.init | Notes  |
|----------------|------:|-------------------:|--------------------:|--------|
| project_0*.py  | 1,250 |            29,500  |          4 million  | This is the standard design from nand2tetris, with a reasonably efficient VM translator. |
| alt/lazy.py    | _1,250_ |          26,000  |        3.3 million  | A slighty cleverer translator for the standard CPU, which avoids updating the stack when that's easy to do. |
| alt/sp.py      | 1,800 |            15,700  |        2.6 million  | Adds instructions for pushing/popping values to/from the stack, making programs more compact. |
| alt/threaded.py| 1,550 |             8,700  |        5.1 million  | Adds lightweight CALL/RTN instructions, enabling a very compact "threaded interpreter" translation. |
