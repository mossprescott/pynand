;; Move a character around the screen, controlled by the arrow keys.
;;
;; Ok, so it's not much of a game. And there's a fair amount of flicker.
;; And it consumes memory just waiting for a key to be pressed, because
;; it doesn't use the optimized, but terminal-oriented getchar primitive.
;;
;; Requires ribbit/min.scm and io.scm

(define x 39)
(define y 12)

(define (game)
    (let ((c (peek 4095)))
        (cond
            ((= c 130)  ;; left arrow
                (drawchar x y 0)
                (set! x (- x 1))
                (drawchar x y 42))
            ((= c 131)  ;; up arrow
                (drawchar x y 0)
                (set! y (- y 1))
                (drawchar x y 42))
            ((= c 132)  ;; right arrow
                (drawchar x y 0)
                (set! x (+ x 1))
                (drawchar x y 42))
            ((= c 133)  ;; down arrow
                (drawchar x y 0)
                (set! y (+ y 1))
                (drawchar x y 42))
        )
        (game)))

(drawchar x y 42)
(game)
