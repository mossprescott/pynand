;; Note: io.scm should be loaded first

(define (echo)
    (let ((c (getchar)))
        ;;(putchar c)
        (echo)))

(echo)