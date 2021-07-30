from nand.jack_ast import *
from nand.translate import AssemblySource


class SymbolTable:
    def __init__(self):
        self.statics = {}
        self.fields = {}

        self.args = {}
        self.locals = {}

    def start_subroutine(self):
        """Start a new subroutine scope (i.e. remove all "arg" and "local" definitions.)
        """

        self.args = {}
        self.locals = {}

    def define(self, name, type_, kind):
        """Record the definition of a new identifier, and assign it a running index.
        If `kind` is "static" or "field", record it in class scope, if "arg" or "local",
        record it in subroutine scope."""

        defs = self._map_for(kind)
        defs[name] = (type_, len(defs))

    def count(self, kind):
        """Number of identifiers of the given kind already defined in the current scope
        (class or subroutine, depending on the kind.)
        """

        return len(self._map_for(kind))

    def kind_of(self, name):
        """Look up the kind of an identifier. Return "static", "field", "arg", or "local"; if
        the identifier has not been defined in the current scope, throw."""

        _, kind = self._find_name(name)
        return kind

    def type_of(self, name):
        """Look up the type of an identifier. If the identifier has not been defined in the
        current scope, throw.
        """

        (type_, _), _ = self._find_name(name)
        return type_

    def index_of(self, name):
        """Look up the index of an identifier. Return an integer which is unique to the given
        identifier in the current scope, counting from 0; if the identifier has not been defined
        in the current scope, throw."""

        (_, index), _ = self._find_name(name)
        return index

    def _map_for(self, kind):
        if kind == "static":
            return self.statics
        elif kind == "field":
            return self.fields
        elif kind == "arg":
            return self.args
        elif kind == "local":
            return self.locals
        else:
            raise Exception(f"Unrecognized kind: {kind}")

    def _find_name(self, name):
        if name in self.locals:
            return self.locals[name], "local"
        elif name in self.args:
            return self.args[name], "arg"
        elif name in self.fields:
            return self.fields[name], "field"
        elif name in self.statics:
            return self.statics[name], "static"
        else:
            raise Exception(f"No definition for name in the current scope: {name}")


    def __str__(self):
        return "\n".join(
            [ "SymbolTable {" ]
            + [f"  {type_} {name}  // static {index}" for (name, (type_, index)) in self.statics.items()]
            + [f"  {type_} {name}  // field {index}" for (name, (type_, index)) in self.fields.items()]
            + [f"  {type_} {name}  // arg {index}" for (name, (type_, index)) in self.args.items()]
            + [f"  {type_} {name}  // local {index}" for (name, (type_, index)) in self.locals.items()]
            + [ "}" ]
        )



#### I have just realized that I have been using AssemblySource to emit VM code, which it was never
#### meant to do, and may be a completely dopey idea. Need to revisit and/or generalize it.

def compile_class(ast: Class, symbol_table: SymbolTable, asm: AssemblySource):
    for vd in ast.varDecs:
        # TODO
        pass

    for decl in ast.subroutineDecs:
        compile_subroutineDec(decl, symbol_table, asm)


def compile_subroutineDec(ast: SubroutineDec, symbol_table: SymbolTable, asm: AssemblySource):
    class_name = "Main"  # HACK

    if ast.kind == "function":
         # Scan varDecs for symbols:
        symbol_table.start_subroutine()
        for vd in ast.body.varDecs:
            for n in vd.names:
                symbol_table.define(n, vd.type, "local")

        print(symbol_table)

        num_vars = max(1, symbol_table.count("local"))  # space for return values?

        asm.instr(f"function {class_name}.{ast.name} {num_vars}")
        for stmt in ast.body.statements:
            compile_statement(stmt, symbol_table, asm)
        asm.blank()

    else:
        raise Exception("TODO")

def compile_varDec(ast, symbol_table, asm):
    print(f"varDec ast: {ast}")
    # TODO


def compile_statement(ast: Statement, symbol_table: SymbolTable, asm: AssemblySource):
    if isinstance(ast, LetStatement):
        if ast.array_index is not None:
            # First compute the destination address:
            compile_expression(ast.array_index, symbol_table, asm)
            asm.instr(f"push {symbol_table.kind_of(ast.name)} {symbol_table.index_of(ast.name)}")
            asm.instr("add")

            # Now the right hand side:
            compile_expression(ast.expr, symbol_table, asm)
            asm.instr("pop temp 0")     # stash the value

            asm.instr("pop pointer 1")  # set the THAT pointer
            asm.instr("push temp 0")    # recover the value
            asm.instr("pop that 0")     # and finally store it
        else:
            compile_expression(ast.expr, symbol_table, asm)
            asm.instr(f"pop {symbol_table.kind_of(ast.name)} {symbol_table.index_of(ast.name)}")

    # elif isinstance(ast, IfStatement):

    elif isinstance(ast, WhileStatement):
        # Note: this is the exact strategy (and labels) used by the canonical compiler.
        # Don't look at me, in other words.
        top_label = asm.next_label("WHILE_EXP")
        exit_label = asm.next_label("WHILE_END")

        asm.instr(f"label {top_label}")  # HACK
        compile_expression(ast.cond, symbol_table, asm)
        asm.instr("not")
        asm.instr(f"if-goto {exit_label}")
        for stmt in ast.body:
            compile_statement(stmt, symbol_table, asm)
        asm.instr(f"goto {top_label}")
        asm.instr(f"label {exit_label}")  # HACK


    elif isinstance(ast, DoStatement):
        # expr = body[1]
        compile_subroutineCall(ast.expr, symbol_table, asm)
        asm.instr("pop temp 0")

    elif isinstance(ast, ReturnStatement):
        if ast.expr is None:
            asm.instr("push constant 0")
        else:
            compile_expression(ast.expr, symbol_table, asm)
        asm.instr("return")

    else:
        raise Exception(f"TODO: {ast}")


def compile_expression(ast: Expression, symbol_table: SymbolTable, asm: AssemblySource):
    if isinstance(ast, IntegerConstant):
        asm.instr(f"push constant {ast.value}")

    elif isinstance(ast, StringConstant):
        # Yikes: this is 2 instructions per character, and it leaks the string.
        # What could the CPU do to make this less painful?
        # Should the compiler hoist these constants to the top of the function
        # and/or delete them for you?
        asm.instr(f"push constant {len(ast.value)}")
        asm.instr("call String.new 1")
        for c in ast.value:
            asm.instr(f"push constant {ord(c)}")
            asm.instr("call String.appendChar 2")

    elif isinstance(ast, KeywordConstant):
        if ast.value == True:
            asm.instr(f"push constant 1")
        elif ast.value == False:
            asm.instr(f"push constant 0")
        elif ast.value is None:
            asm.instr(f"push constant 0")
        elif ast.value == "this":
            asm.instr("push argument 0")
        else:
            raise Exception(f"Unrecognized constant: {ast}")

    elif isinstance(ast, VarRef):
        asm.instr(f"push {symbol_table.kind_of(ast.name)} {symbol_table.index_of(ast.name)}")

    elif isinstance(ast, ArrayRef):
        # TODO: validate this makes any sense at all
        compile_expression(ast.array_index, symbol_table, asm)
        asm.instr(f"push {symbol_table.kind_of(ast.name)} {symbol_table.index_of(ast.name)}")
        asm.instr("add")
        asm.instr("pop pointer 1")
        asm.instr("push that 0")

    elif isinstance(ast, SubroutineCall):
        for arg in ast.args:
            compile_expression(arg, symbol_table, asm)
        # TODO: non-static
        asm.instr(f"call {ast.class_name}.{ast.sub_name} {len(ast.args)}")

    elif isinstance(ast, BinaryExpression):
        compile_expression(ast.left, symbol_table, asm)
        compile_expression(ast.right, symbol_table, asm)
        compile_op(ast.op, asm)

    # UnaryExpression
    else:
        raise Exception(f"TODO: {ast}")


def compile_op(ast: Op, asm: AssemblySource):
    if ast.symbol == "+":
        asm.instr("add")
    elif ast.symbol == "-":
        asm.instr("sub")
    elif ast.symbol == "*":
        asm.instr("call Math.multiply 2")
    elif ast.symbol == "/":
        asm.instr("call Math.divide 2")
    elif ast.symbol == "&":
        asm.instr("and")
    elif ast.symbol == "|":
        asm.instr("or")
    elif ast.symbol == "<":
        asm.instr("lt")
    elif ast.symbol == ">":
        asm.instr("gt")
    elif ast.symbol == "=":
        asm.instr("eq")
    else:
        raise Exception(f"Unknown op: {ast.symbol}")


def compile_subroutineCall(ast: SubroutineCall, symbol_table: SymbolTable, asm: AssemblySource):
    for arg in ast.args:
        compile_expression(arg, symbol_table, asm)

    asm.instr(f"call {ast.class_name}.{ast.sub_name} {len(ast.args)}")
