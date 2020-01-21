# See https://www.nand2tetris.org/project08

import project_07


class Translator(project_07.Translator):
    """Translates all VM opcodes to assembly instructions, extending the Translator from project 07.
    """

    def __init__(self):
        project_07.Translator.__init__(self)


    #
    # Basic Loop:
    #

    def label(self, name):
        # SOLVERS: implement
        return self.solved.label(name)

    def if_goto(self, name):
        # SOLVERS: implement
        return self.solved.if_goto(name)
