"""Implementation(s) of the [RiSC-16](https://user.eng.umd.edu/~blj/RiSC/) ISA.

A simple implementation of this CPU is roughly comparable in conceptual complexity to the "Hack"
CPU, but with very different architectural choices, inspired by the early "pure" RISC designs:

- 7 "general-purpose" registers, plus an always-zero pseudo-register
- every instruction can read/write any register
- a *very* simple ALU, offering only `ADD` and `NAND`
- a 3-bit opcode field, decoded to arbitrary control signals
- seriously, only *8* instructions
- PC-relative branch targets

This design leads to very different challenges for the compiler writer, and also leaves a lot
more leeway for clever implementation strategies.

On the other hand, it ends up being more than twice as large in terms of gates, at least as they
are currently counted. This is mainly due to the large register file and the naive way it's
implemented.

## Instructions

All the instruction formats and behavior are as described in the RiSC-16 design docs, and only
briefly summarized here. See
[The RiSC-16 Instruction-Set Architecture](https://user.eng.umd.edu/~blj/RiSC/RiSC-isa.pdf).

Instructions contain one, two, or three "register" fields, which identify one of the seven registers
r1 (bits: 001) to r7 (111). r0 is not actually stored; it always contains the value 0 when read.
When r0 is used as the destination, the result is discarded.

### Three-register-operand instructions

`add` and `nand` instructions read two source registers and write to a register:

 15   14   13   12   11   10    9    8    7    6    5    4    3    2    1    0
|   opcode    |  regA (dst)  |  regB (src0) |   0 (reserved)    | regC (src1)  |

`add rA rB rC` (opcode: 000); add the contents of regB with regC, store results in regA.
`nand rA rB rC` (opcode: 010); nand the contents of regB with regC, store results in regA.

### Two-register-operand instructions

 15   14   13   12   11   10    9    8    7    6    5    4    3    2    1    0
|   opcode    |     regA     |     regB     |    signed immediate (-64 to 63)  |

`addi rA rB imm` (opcode: 001); add the contents of regB with imm, store results in regA.
`lw rA rB imm` (opcode: 100); load value from memory into regA. Location is imm + the contents of regB.
`sw rA rB imm` (opcode: 101); store value from regA into memory. Location is imm + the contents of regB.
`beq rA rB imm` (opcode: 110); compare contents of regA and regB. If they are the same, branch to PC + 1 + imm.
`jalr rA rB` (opcode: 111); jump to the address in regB. Store PC + 1 into regA.

The imm field of jalr is unused and should always be 0.

Note that regA is *written* by `addi`, `lw`, and `jalr`, but *read* by `sw` and `beq`.

### One-register-operand instructions

 15   14   13   12   11   10    9    8    7    6    5    4    3    2    1    0
|   opcode    |     regA     |         immediate (0 to 0x3FF)                  |

`lui rA imm` (opcode: 011); place the immediate value in the upper 10 bits of regA. Set the bottom 6 bits of regA to 0.

### Labels

A label appears on its own line, surrounded by parens, e.g. `(start)`.

The address of the instruction following the label can be referred to in any immediate field,
with the meaning dependent on the instruction format:

`beq r1 r0 @start`: the immediate value is the *offset* from the following instruction to the
instruction labeled `(start)`. For example:

    (loop)
      addi r2 r2 1
      beq r1 r2 @end   // (@end -> +1); skip next instruction if r1 == r2
      beq r0 r0 @loop  // (@loop -> -3); jump back three instructions
    (end)
      beq r0 r0 @end   // (@end -> -1); jump to same address — infinite loop

If the resolved address offset doesn't fit in 6 bits (-64 to 63), the assembler will reject the code.
TODO: so, yeah, that seems like it could turn out be awfully inconvenient for real code. Consider
changing beq to compare with 0, using a 10-bit offset? -512 to 511 is *probably* enough for local
branches, most of the time.


`lui r1 @start`: the immediate value is the upper 10 bits of the *absolute* address of the labeled
instruction.




### Pseudo-instructions

`lli rA @label` translates to `addi rA rA (address & 03f)`, with the address resolved at
load-time as described above. This can be used with `lui rA @label` to load an arbitrary 16-bit
address into a register in two cycles. Note: if the address is <= 63, then a single-cycle
`addi rA r0 @label` *would* work, if you could say that, but you can't, because we said these
small immediate values are *offsets*. Anyway, 63 may be too small to be super useful (remember,
"statics" are allocated starting at address 16.)

None of the other pseudo-instructions described in the docs are implemented. It's expected that code
generators will use comments in the assembly stream to clarify intent when necessary.

The `.fill` and `.space` directives are not implemented. They seem to be intended to allocate
space in RAM within the instruction stream, which doesn't make sense given that programs reside
in ROM in this implementation.




## Caveats

In the real world, this design would probably *require* a pipelined implementation (or a lot
of stalls), just because the addresses for load/store are computed by the ALU. In the Hack design,
the physical memory address is always available in A when the instruction is decoded, so a very
simple no-stall design is a little more realistic.

That level of timing detail isn't really captured in this implementation at the moment.


## Low-hanging fruit

Several aspects of this ISA make it simple to implement the chip, but are significantly limiting
for compiling Jack programs:

Limiting computation to `add` and `nand` will mean a lot of repetitive sequences of simple ops.
Those two opcodes occupy fully 25% of the opcode space, but don't use 4 bits. One alternative
would be to use just two bits to select "<alu_op> rA rB rC", and use the 5 bits to configure the
ALU, somewhat like the Hack CPU does (with 6 bits, but in this case we wouldn't need the "zero"
bits, for one thing.) It's pretty typical for RISCs to have *lots* of fiddly instructions,
precisely because of these available bits.

In particular, add shift left/right instructions, which are cheap in terms of gates. Probably not
enough bits available for a proper shift by +/- 15 bits, but even single-bit shifting is a big help
(see shift.py.)

Expand the immediate offset for beq to 10 bits. 7 bits is probably hardly ever enough.

Modify lui so you can load a jump target in one cycle more of the time? Shift by 5? That would still
require 32-word alignment. And alignment sucks.
"""