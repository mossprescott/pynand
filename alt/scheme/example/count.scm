;; Count up from 1, writing each number to the screen, and wrapping around from 16383 -> -16384.
;;
;; This program will run indefinitely, continuously allocating ribs but never filling up the heap,
;; if garbage-collection is working.
;;
;; Requires min.scm (for write, newline, etc.)

(define (sep) (write-chars (string->list ", ")))

(define (count x)
    (write x)
    (sep)
    (write (+ x 1))
    (sep)
    (write (+ x 2))
    (sep)
    (write (+ x 3))
    (sep)
    (write (+ x 4))
    (sep)
    (write (+ x 5))
    (sep)
    (write (+ x 6))
    (sep)
    (write (+ x 7))
    (sep)
    (write (+ x 8))
    (sep)
    (write (+ x 9))
    (newline)
    (count (+ x 10)))

(count 0)
