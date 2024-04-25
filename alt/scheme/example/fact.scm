;; Requires min.scm, just to write the result

(define (fact n)
    (if (< n 2)
        1
        (* n
            (fact (- n 1)))))

(write (fact 7))
