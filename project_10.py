# See https://www.nand2tetris.org/project10

# SOLVERS: remove this import to get started
from nand.solutions import solved_10

# a label for each token type:
KEYWORD = 'keyword'
SYMBOL = 'symbol'
INT = 'integerConstant'
STR = 'stringConstant'
ID = 'identifier'


def lex(string):
    """Break the text of Jack source code into a list of tokens.

    White space and comments are ignored. Each token is converted to a tuple of (token-type, chars).
    
    """

    # SOLVERS: replace this with code to parse a single assembly instruction string, producing
    # a machine instruction as a 16-bit int
    tokens = solved_10.lex(string)

    return tokens
