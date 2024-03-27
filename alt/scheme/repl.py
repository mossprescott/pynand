#! /usr/bin/env python

"""Scheme REPL, reading input from the keyboard and writing output to the screen.

This wrapper just runs the equivalent of

    alt/scheme/rvm.py alt/scheme/ribbit/*.scm --simulator compiled --print

Supported keywords and functions: see ribbit/repl-min.scm
"""

from alt.scheme import rvm

def main():
    def load(path):
        with open(f"alt/scheme/{path}") as f:
            return f.readlines()


    min_library_src_lines = load("ribbit/min.scm")
    io_src_lines = load("io.scm")
    repl_src_lines = load("ribbit/repl-min.scm")

    program = "".join(
        min_library_src_lines
        + io_src_lines
        + repl_src_lines)

    # Note: actually running the compiler in the Ribbit Python interpreter is pretty slow.
    # Probably want to cache the encoded result somewhere (or just go back to hard-coding it here.)
    print("Compiling...")

    rvm.run(program, interpreter="jack", simulator="compiled",
            print_asm=True,
            trace_level=rvm.TRACE_NONE)


if __name__ == "__main__":
    main()
