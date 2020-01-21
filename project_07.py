# See https://www.nand2tetris.org/project07

# SOLVERS: remove this import to get started
from nand.solutions import solved_07


class Translator:
    def __init__(self):
        self.solved = solved_07.Translator()


    #
    # Simple Add:
    #

    def push_constant(self, value):
        # SOLVERS: write some code here to construct a list of strings containing Hack assembly 
        # instructions to push `value` onto the stack
        return self.solved.push_constant(value)

    def add(self):
        # SOLVERS: implement the add opcode
        # Hint: this is actually going to be the same instructions every time, so just build
        # a list and return it.
        return self.solved.add()


    #
    # Stack Ops:
    #

    def sub(self):
        # SOLVERS: implement the sub opcode
        return self.solved.sub()

    def neg(self):
        # SOLVERS: implement the sub opcode
        return self.solved.neg()

    def and_op(self):
        # SOLVERS: implement the and opcode
        return self.solved.and_op()

    def or_op(self):
        # SOLVERS: implement the or opcode
        return self.solved.or_op()

    def not_op(self):
        # SOLVERS: implement the not opcode
        return self.solved.not_op()

    def eq(self):
        # SOLVERS: implement the eq opcode
        return self.solved.eq()

    def lt(self):
        # SOLVERS: implement the lt opcode
        return self.solved.lt()

    def gt(self):
        # SOLVERS: implement the gt opcode
        return self.solved.gt()

        
    #
    # Memory Access - Basic:
    #

    def pop_local(self, index):
        # SOLVERS: implement
        return self.solved.pop_local(index)

    def pop_argument(self, index):
        # SOLVERS: implement
        return self.solved.pop_argument(index)

    def pop_this(self, index):
        # SOLVERS: implement
        return self.solved.pop_this(index)

    def pop_that(self, index):
        # SOLVERS: implement
        return self.solved.pop_that(index)

    def pop_temp(self, index):
        # SOLVERS: implement
        return self.solved.pop_temp(index)

    def push_local(self, index):
        # SOLVERS: implement
        return self.solved.push_local(index)

    def push_argument(self, index):
        # SOLVERS: implement
        return self.solved.push_argument(index)

    def push_this(self, index):
        # SOLVERS: implement
        return self.solved.push_this(index)

    def push_that(self, index):
        # SOLVERS: implement
        return self.solved.push_that(index)

    def push_temp(self, index):
        # SOLVERS: implement
        return self.solved.push_temp(index)


    #
    # Memory Access - Pointer:
    #

    def pop_pointer(self, index):
        # SOLVERS: implement
        return self.solved.pop_pointer(index)

    def push_pointer(self, index):
        # SOLVERS: implement
        return self.solved.push_pointer(index)


    #
    # Memory Access - Static:
    #

    def pop_static(self, index):
        # SOLVERS: implement
        return self.solved.pop_static(index)

    def push_static(self, index):
        # SOLVERS: implement
        return self.solved.push_static(index)


    #
    # Helpers:
    #

    def next_label(self, name):
        # SOLVERS: this might be useful
        return self.solved.next_label(name)
