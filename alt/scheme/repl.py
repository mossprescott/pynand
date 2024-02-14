#! /usr/bin/env python

"""Scheme REPL, reading input from the keyboard and writing output to the screen.

Supported keywords and functions:
TBD
"""

from alt.scheme import rvm

def main():
    with open("alt/scheme/ribbit/min.scm") as f:
        min_library_src_lines = f.readlines()

    # TODO: need to reference the library functions we want to be able available
    program = "".join(min_library_src_lines) + """

    (define poke (rib 21 0 1))

    (define screen 2048)
    (define (drawchar x y c) (poke (+ screen (+ x (* 80 y))) c))

    (define cursorx 0)
    (define cursory 0)
    (define (putchar c)
        (begin
            (drawchar cursorx cursory c)
            (set! cursorx (+ 1 cursorx))))

    (repl)
    """

    # Note: actually running the compiler in the Ribbit Python interpreter is pretty slow.
    # Probably want to cache the encoded result somewhere (or just go back to hard-coding it here.)
    print("Compiling...")

    rvm.run(program, simulator="codegen", print_asm=False, trace_level=rvm.TRACE_COARSE)


def temp():
    """Simpler examples for now."""

#     pgm = """
# ;; In lieu of pre-defining additional primitives and re-building rsc,
# ;; with the same result:
# (define poke (##rib 21 0 1))

# (poke 16384 21845)
# """

#     pgm = """
# (+ 1 2)
# """

    pgm = "42"

    rvm.run(program=pgm)


if __name__ == "__main__":
    main()
    # temp()
