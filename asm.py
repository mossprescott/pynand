"""Read assembly from stdin, write instructions to stdout, 16-binary digits per line."""

import sys
from project_06 import assemble

for instr in assemble(sys.stdin):
    for i in range(15, -1, -1):
        print(int(instr & (1 << i) != 0), end='')
    print()
