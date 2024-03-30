;; Read and echo input line by line.
;; Note: getchar buffers the input until a whole line is entered; this script just has to read
;; and write the characters one at a time.

(define (echo)
    (let ((c (getchar)))
        (putchar c)
        (echo)))

(echo)
