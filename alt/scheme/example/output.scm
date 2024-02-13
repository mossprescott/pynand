(define poke (rib 21 0 1))

(define screen 2048)
(define (drawchar x y c) (poke (+ screen (+ x (* 80 y))) c))

;; First, ABCD in the corners of the screen:
(drawchar  0  0 65)
(drawchar 79  0 66)
(drawchar  0 24 67)
(drawchar 79 24 68)

;; About 40k cycles and 2% of the heap to get this far, without a primitive *
;; Down to 16K cycles and 0.8% of the heap using primitive *



;; Now, a character map table:
;;    00 01 02 ...
;; ...
;; 30  0  1  2 ...
;; 40  @  A  B ...
;; ...

(define char-zero 48)
(define char-a 65)
(define (hex c) (if (< c 10) (+ c char-zero) (+ c (- char-a 10))))

;; Effectful loop: evaluate (f value) for each x <= value < y, discarding the result.
(define (for x y f)
    (if (< x y)
        (begin
            (f x)
            (for (+ x 1) y f))
        '()))

;; Header row: 00 01 02 ...
(for 0 16 (lambda (x)
    (begin
        (drawchar (+ 5 (* 3 x)) 3 char-zero)
        (drawchar (+ 6 (* 3 x)) 3 (hex x)))))

;; About 200k cycles and 10% of the heap to this point

;; Header column: 00, 10, ... 70
(for 0 8 (lambda (y)
    (begin
        (drawchar 1 (+ y 4) (hex y))
        (drawchar 2 (+ y 4) char-zero))))

;; Fill in only the rows with printable chars: 2-7
(for 2 8 (lambda (y)
    (let ((h (* 16 y)))
        (for 0 16 (lambda (x)
            (drawchar
                (+ 6 (* 3 x))
                (+ y 4)
                (+ h x)))))))

;; 1.1M cycles and 40% of the heap to complete
