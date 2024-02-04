# Scheme

Scheme interpreter, based on [Ribbit](https://github.com/udem-dlteam/ribbit/).

Goals:
- run on the vanilla Hack architecture (well, the CPU anyway)
- provide a REPL that can compile and run simple functions like `fib` or `fact` written at the
  keyboard
- run something graphical (even if in character-mode)
- implement as little as possible in assembly; just the bare interpreter and Ribbit primitives,
  plus a few additions for accessing the hardware.


## Virtual Machine

A source program is compiled by the Ribbit AOT compiler to an instruction graph as specified in
[A Small Scheme VM, Compiler, and REPL in 4K](http://www.iro.umontreal.ca/~feeley/papers/YvonFeeleyVMIL21.pdf),
with a few modifications.

Unimplemented primitives:
- `*`, `quotient`: the Hack CPU does not provide these; they can be implemented as ordinary
  functions (*TBD* probably need at least `*` as a primitive for speed).
- `getchar` and `putchar`: there is no OS to provide these, they will be implemented as ordinary
    functions when needed (i.e. for the REPL)

Additional primitives:
- `peek`; code: `20`; `x ← pop(); r ← RAM[x]`
- `poke`; code: `21`; `y ← pop(); x ← pop(); RAM[x] ← y; r <- y`
- `halt`; code: `22`; stop the machine, probably by going into a tight loop

`peek` and `poke` can be used to read and write to any address, but most usefully the screen buffer
(which is at 0x0400–0x0x07E7) and the location mapped to the keyboard (0x07FF).

`halt` can be used to signal normal completion of a program.

## Memory Layout

| Address | Contents | Description |
| 0       | SP       | Address of the cons list that represents the stack: i.e. a "pair" rib which contains the value at the top of the stack and points to the next entry. |
| 1       | PC       | Address of the rib currently being interpreted. |
| 2       | NEXT_RIB | Address where the next allocation will occur. |
| ...     |          | TBD: values used by the garbage collector to keep track of free space. |


## Rib Representation

For simplicity, ribs are stored as described in the paper, three words each.

The high bit of each word is used as a tag to identify whether the word points to a rib.
- A word with the high bit set is a 15-bit signed integer value. To recover an ordinary 16-bit value when
    needed, bit 14 is copied to bit 15. For many operations, it's sufficient to treat values as unsigned
    and just make sure to set the high bit if it might have been cleared (e.g. due to overflow.)
- A word with the high bit unset is the address of a rib in memory, treated as unsigned and
    divided by three, so that every possible rib address fits in the range of 15-bit unsigned values.

Note: Ribbit's C implementation uses the *low* bit to tag integers, but that's not practical on this
CPU, which does not provide a right-shift instruction. Masking off the high bit can be done efficiently.
On the other hand, rib addresses only ever need to be generated incrementally so we only need the
`extract` operation: multiply by 3 (with two "+" instructions.)

Future:
- really squeeze the bits and get each rib into 2 words. If possible, this saves 33% of the space,
    and adds a *lot* of cycles to decode the bits in the interpreter. And it might mean reducing
    the maximum number of ribs that can be addressed, which defeats the purpose.


## Initialization

To make efficient use of available memory, the symbol table and instruction graph produced by
Ribbit's compiler (`rsc.py`) are decoded into ribs and included as "data" words in the ROM, using
[big.py](../big.py)'s extra `#<int>` opcode.

The actual `symbol` ribs that make up the symbol table have to be mutable, so they're constructed
in RAM during initialization. Their addresses are known ahead of time, so the code in ROM refers to
them directly.

Note: the REPL consumes about 2K ribs in memory, and takes about 2KB of encoded data in the Ribbit
implementations. That means to initialize we need something like 6K of heap plus 2K words, plus
some for stack.

Actual size in the implementation:
- Instruction ribs in the ROM for the REPL: 1643 (4.8K words)
- Initial ribs in RAM for the symbol table: 212 (0.6K words)
- Note: this does not account for additional Scheme code that will eventually be needed to make it
    work (e.g. getchar/putchar).

[A comment in the Ribbit source]((https://github.com/udem-dlteam/ribbit/blob/dev/src/host/c/rvm.c#L207))
suggests that space for 48,000 ribs is needed to bootstrap. Presumably that refers to running the
*compiler*, which is out of scope.

## GC

The program runs until memory is exhausted.

TODO: collect garbage.
