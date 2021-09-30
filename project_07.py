# VM I: Stack Arithmetic
#
# See https://www.nand2tetris.org/project07

from nand.translate import AssemblySource

# SOLVERS: remove this import to get started
from nand.solutions import solved_07


class Translator:
    """Translates all the arithmetic and memory access opcodes of the VM to assembly instructions.
    """

    def __init__(self):
        # AssemblySource deals with keeping track of emitted instructions, and provides a nice
        # log of execution which makes debugging a lot easier. In any case, the tests assume you use
        # it, so you might as well not fight it.
        self.asm = AssemblySource()

        # SOLVERS: remove this when all the method bodies are filled in
        self.solved = solved_07.Translator(self.asm)


    #
    # Simple Add:
    #

    def push_constant(self, value):
        # SOLVERS: write some code here to emit Hack assembly instructions to push `value` onto the stack
        #
        # self.asm.start("push constant")  # insert a comment which is shown when debugging
        # self.asm.instr(f"@{value}")
        # self.asm.instr("D=A")
        # ...

        return self.solved.push_constant(value)

    def add(self):
        # SOLVERS: implement the add opcode
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
    # (Optional) Cleanup:
    #
    def finish(self):
        """Called after all opcodes are processed, in case the translator needs to say any last words."""
        pass


    #
    # (Optional) Optimization:
    #
    def rewrite_ops(self, ops):
        # SOLVERS: ignore for now. This is a hook to allow the Translator to inspect and modify the
        # opcode sequence before it is translated, in case a "better" equivalent sequence is possible.
        return ops


    def check_references(self):
        """Check for obvious "linkage" errors: e.g. functions that are referenced but never defined.

        Raises AssertionFailure if there are any obvious problems.
        """

        # SOLVERS: this is a big help for debugging programs later on, but you can just return None
        # and nothing will break (except possibly your sanity.)
        return self.solved.check_references()


    #
    # Wiring:
    #

    def handle(self, op):
        """Dispatch to the handler for an opcode, in the form of a tuple (op_name, [args])."""

        # SOLVERS: this is just plumbing to call one of the methods definied below. Feel
        # free to leave it here and don't worry about it how it works too much.
        op_name, args = op
        self.__getattribute__(op_name)(*args)


def parse_line(line):
    # SOLVERS: parse one line of VM source. The result should be a tuple which contains the name of
    # the method of Translator which handles the opcode, and a sequence with any arguments.
    # E.g. ("push_constant", [1]), ("add", []), ("function", ["Main", "main", 2])
    return solved_07.parse_line(line)
