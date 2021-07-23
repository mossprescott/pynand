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

    # SOLVERS: replace this with code to break the input string into a sequence of tokens
    tokens = solved_10.lex(string)

    return tokens


def parse_class(token_list):
    """Analyze a stream of tokens and assemble them into an Abstract Syntax Tree representing the program.

    Each node is a tuple consisting of a token-type label and zero or more arguments. Within nodes,
    tokens are represented by the tuples form the input. That is,

    See the tests for the expected
    """

    # SOLVERS: replace this with code to analyze the token stream
    ast = solved_10.parse_class(token_list)

    return ast
