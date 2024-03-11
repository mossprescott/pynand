#! /usr/bin/env python

"""Scheme REPL, reading input from the keyboard and writing output to the screen.

Supported keywords and functions:
TBD
"""

from alt.scheme import rvm

def main():
    def load(path):
        with open(f"alt/scheme/{path}") as f:
            return f.readlines()


    min_library_src_lines = load("ribbit/min.scm")
    io_src_lines = load("io.scm")

    program = "".join(min_library_src_lines + io_src_lines) + """

;; TEMP: this should be good enough to convert single-digit numbers to strings for display
(define (quotient x y) 0)


(repl)

;; Exported symbols.

(export

*
+
-
<
=
cons
)
"""

    # Note: actually running the compiler in the Ribbit Python interpreter is pretty slow.
    # Probably want to cache the encoded result somewhere (or just go back to hard-coding it here.)
    print("Compiling...")

    rvm.run(program, interpreter="jack", simulator="compiled",
            print_asm=True,
            trace_level=rvm.TRACE_NONE)
            # trace_level=rvm.TRACE_COARSE)


if __name__ == "__main__":
    main()
