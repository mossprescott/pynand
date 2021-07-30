# Compiler II: Code Generation
#
# See https://www.nand2tetris.org/project11


from nand.jack_ast import *

# SOLVERS: remove this import to get started
from nand.solutions import solved_11


class SymbolTable:
    def __init__(self):
        # SOLVERS: delete this line and add your implementation here
        self.solved = solved_11.SymbolTable()

    def start_subroutine(self):
        """Start a new subroutine scope (i.e. remove all "arg" and "var" definitions.)
        """

        # SOLVERS: delete this line and add your implementation here
        self.solved.start_subroutine()

    def define(self, name, type_, kind):
        """Record the definition of a new identifier, and assign it a running index.
        If `kind` is "static" or "field", record it in class scope, if "arg" or "var",
        record it in subroutine scope."""

        # SOLVERS: delete this line and add your implementation here
        self.solved.define(name, type_, kind)

    def count(self, kind):
        """Number of identifiers of the given kind already defined in the current scope
        (class or subroutine, depending on the kind.)
        """

        # SOLVERS: delete this line and add your implementation here
        return self.solved.count(kind)

    def kind_of(self, name):
        """Look up the kind of an identifier. Return "static", "field", "arg", or "var"; if
        the identifier has not been defined in the current scope, return None."""

        # SOLVERS: delete this line and add your implementation here
        return self.solved.kind_of(name)

    def type_of(self, name):
        """Look up the type of an identifier. If the identifier has not been defined in the
        current scope, throw.
        """

        # SOLVERS: delete this line and add your implementation here
        return self.solved.type_of(name)

    def index_of(self, name):
        """Look up the index of an identifier. Return an integer which is unique to the given
        identifier in the current scope, counting from 0; if the identifier has not been defined
        in the current scope, return None."""

        # SOLVERS: delete this line and add your implementation here
        return self.solved.index_of(name)


    def __str__(self):
        """A human-readable summary of all definitions in scope.
        Note: this is useful for debugging, but not actually required for the tests or for actually
        using the compiler.
        """

        # SOLVERS: delete this line and add your implementation here
        return str(self.solved)


def find_symbols(node):
    """Identify all references needing to be mapped to locations in memory, and build the mapping
    in the form of a symbol table.

    TODO: how do symbol tables for different scopes get composed?
    """

    symbol_table = solved_11.find_symbols(node)

    return symbol_table


def compile_expression(ast, symbol_table, asm):
    """Given a node representing a Jack expression (e.g. "x + 1"), and a symbol table mapping
    identifiers to locations, generate VM instructions to compute the result and leave it on the
    stack.

    >>> from nand.translate import AssemblySource
    >>> asm = AssemblySource()
    >>> compile_expression(IntegerConstant(1), SymbolTable(), asm)
    >>> asm.lines
    ['  push constant 1']
    """

    # SOLVERS: replace this with your own implementation
    solved_11.compile_expression(ast, symbol_table, asm)


def compile_class(ast, symbol_table, asm):
    # SOLVERS: replace this with your own implementation
    solved_11.compile_class(ast, symbol_table, asm)
