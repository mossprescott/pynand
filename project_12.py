# Operating System
#
# See https://www.nand2tetris.org/project12

# SOLVERS: remove this import to get started
from nand.solutions import solved_12


ARRAY_NEW = solved_12.ARRAY_NEW
# """
#     /** Constructs a new Array of the given size. */
#     function Array new(int size) {
#
#     }
# """

ARRAY_DISPOSE = """
    /** Disposes this array. */
    method void dispose() {
      do Memory.deAlloc(this);
      return;
    }
"""


ARRAY_CLASS = f"""
class Array {{
{ARRAY_NEW}
{ARRAY_DISPOSE}
}}
"""