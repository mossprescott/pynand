# See https://www.nand2tetris.org/project08

import project_07


class Translator(project_07.Translator):
    """Translates all VM opcodes to assembly instructions, extending the Translator from project 07.
    """

    def __init__(self):
        project_07.Translator.__init__(self)


    #
    # Program Flow — Basic Loop:
    #

    def label(self, name):
        # SOLVERS: implement
        return self.solved.label(name)

    def if_goto(self, name):
        # SOLVERS: implement
        return self.solved.if_goto(name)


    #
    # Program Flow — Fibonacci Series:
    #
    
    def goto(self, name):
        # SOLVERS: implement
        return self.solved.goto(name)


    #
    # Function Calls — Simple Function:
    #

    def function(self, class_name, function_name, num_locals):
        # SOLVERS: implement
        return self.solved.function(class_name, function_name, num_locals)

    def return_op(self):
        # SOLVERS: implement
        return self.solved.return_op()


    #
    # Function Calls — Nested Call:
    #

    def call(self, class_name, function_name, num_args):
        # SOLVERS: implement
        return self.solved.call(class_name, function_name, num_args)


    #
    # Function Calls - Fibonacci Element:
    #
    
    def preamble(self):
        # SOLVERS: emit instructions to be 
        return self.solved.preamble()
