;; I/O "primitives" for the REPL and any other terminal-style programs.
;;
;; In this implementation, getchar and putchar aren't provided directly by the VM, because there's
;; no OS-level support for getting characters from the keyboard and onto the screen. Instead, the
;; VM provides a lower-level "getchar" (which is a blocking read of the location in memory where
;; the keyboard is mapped), generic "peek" and "poke" primitives which can read and write the
;; screen buffer, and (for peformance) a "screenAddr" primitive which calculates addresses in the
;; screen buffer memory faster than interpreted schems could and without allocation.


(define poke (rib 21 0 1))

;; (define screen 2048)
;; (define (drawchar x y c) (poke (+ screen (+ x (* 80 y))) c))

(define screenAddr (rib 23 0 1))
(define (drawchar x y c) (poke (screenAddr x y) c))

;; (define cursorx 0)
;; (define cursory 0)
;; (define (putchar c)
;;     (if (eqv? c 10)
;;         (begin
;;             (set! cursorx 0)
;;             (set! cursory (+ 1 cursory)))
;;         (begin
;;             (drawchar cursorx cursory c)
;;             (set! cursorx (+ 1 cursorx)))))

;; The getchar primitive just blocks and then returns a non-zero char. The repl seems to
;; expect getchar to handle echo, etc.
;; TODO: use a (let ...) here to hide this definition
;; (define getchar-primitive (rib 18 0 1))
;; (define (getchar)
;;     (let ((c (getchar-primitive)))
;;         (if (eqv? c 128)  ;; newline, according to the strange key mapping
;;             (begin
;;                 (set! cursorx 0)
;;                 (set! cursory (+ 1 cursory))
;;                 10)  ;; regular ASCII newline
;;             (begin
;;                 (putchar c)
;;                 c))))

