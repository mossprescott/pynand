(define poke (rib 21 0 1))

;; With a '*2' primitive, this wouldn't be such a terrible idea...
;; 16*5x = 16*(4*x + x) = 2*(2*(2*(2*(2*(2*x)) + x)))
(define (times2 x) (+ x x))
(define (times80 x) (times2 (times2 (times2 (times2
                        (+ (times2 (times2 x))
                           x))))))

(define screen 2048)
(define (drawchar x y c) (poke (+ screen (+ x (times80 y))) c))

(drawchar  0  0 65)
(drawchar 79  0 66)
(drawchar  0 24 67)
(drawchar 79 24 68)

;; About 40k cycles and 2% of the heap to get this far



;; TODO: character map table:
;;    00 01 02 ...
;; ...
;; 30  0  1  2 ...
;; 40  @  A  B ...
;; ...