;; Count up from 1, writing each number to the screen, and wrapping around from 16383 -> -16384.
;;
;; This program will run indefinitely, continuously allocating ribs but never filling up the heap,
;; if garbage-collection is working.
;;
;; Requires min.scm (for write and newline).

(define (count x)
    (write x)
    (newline)
    (newline)
    (count (+ x 1)))

(count 0)
