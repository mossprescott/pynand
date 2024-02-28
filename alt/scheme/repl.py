#! /usr/bin/env python

"""Scheme REPL, reading input from the keyboard and writing output to the screen.

Supported keywords and functions:
TBD
"""

from alt.scheme import rvm

def main():
    with open("alt/scheme/ribbit/min.scm") as f:
        min_library_src_lines = f.readlines()

    program = "".join(min_library_src_lines) + """

(define poke (rib 21 0 1))

;; (define screen 2048)
;; (define (drawchar x y c) (poke (+ screen (+ x (* 80 y))) c))
;; TODO: pre-compute start address of each row? Is that actually faster than multiply, which is

(define screenAddr (rib 23 0 1))
(define (drawchar x y c) (poke (screenAddr x y) c))

(define cursorx 0)
(define cursory 0)
(define (putchar c)
    (if (eqv? c 10)
        (begin
            (set! cursorx 0)
            (set! cursory (+ 1 cursory)))
        (begin
            (drawchar cursorx cursory c)
            (set! cursorx (+ 1 cursorx)))))

;; The getchar primitive just blocks and then returns a non-zero char. The repl seems to
;; expect getchar to handle echo, etc.
;; TODO: use a (let ...) here to hide this definition
(define getchar-primitive (rib 18 0 1))
(define (getchar)
    (let ((c (getchar-primitive)))
        (if (eqv? c 128)  ;; newline, according to the strange key mapping
            (begin
                (set! cursorx 0)
                (set! cursory (+ 1 cursory))
                10)  ;; regular ASCII newline
            (begin
                (putchar c)
                c))))

;; TEMP: this should be good enough to convert single-digit numbers to strings for display
(define (quotient x y) 0)

;; TEMP: until I get exports to work
(define + (rib 14 0 1))

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

    rvm.run(program, interpreter="assembly", simulator="compiled", print_asm=False, trace_level=rvm.TRACE_COARSE)


if __name__ == "__main__":
    main()
