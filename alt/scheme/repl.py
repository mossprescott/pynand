#! /usr/bin/env python

"""Scheme REPL, reading input from the keyboard and writing output to the screen.

Supported keywords and functions:
TBD
"""

from alt.scheme import rvm

def main():
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
