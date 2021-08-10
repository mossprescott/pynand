from nand.jack_ast import *
from nand.translate import AssemblySource


class SymbolTable:
    def __init__(self, class_name):
        self.class_name = class_name
        self.subroutine_name = None
        self.subroutine_kind = None

        self.statics = {}
        self.fields = {}

        self.arguments = {}
        self.locals = {}

    def start_subroutine(self, name, kind):
        """Start a new subroutine scope (i.e. remove all "argument" and "local" definitions.),
        and track the name and the kind of subroutine being defined ("function", "method", or
        "constructor"), for reporting the context when something goes wrong.
        """

        self.subroutine_name = name
        self.subroutine_kind = kind

        self.arguments = {}
        self.locals = {}

    def define(self, name, type_, kind):
        """Record the definition of a new identifier, and assign it a running index.
        If `kind` is "static" or "this", record it in class scope, if "argument" or "local",
        record it in subroutine scope.
        """

        defs = self._map_for(kind)
        defs[name] = (type_, len(defs))

    def count(self, kind):
        """Number of identifiers of the given kind already defined in the current scope
        (class or subroutine, depending on the kind.)
        """

        return len(self._map_for(kind))

    def kind_of(self, name):
        """Look up the kind of an identifier. Return "static", "this", "argument", or "var"; if
        the identifier has not been defined in the current scope, return None."""

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

    def context(self):
        """Brief description of the part of the program being analyzed, e.g. "function Main.main"."""

        if self.subroutine_name is None:
            return f"class {self.class_name}"
        else:
            return f"{self.subroutine_kind} {self.class_name}.{self.subroutine_name}"

    def _map_for(self, kind):
        if kind == "static":
            return self.statics
        elif kind == "this":
            return self.fields
        elif kind == "argument":
            return self.arguments
        elif kind == "local":
            return self.locals
        else:
            raise Exception(f"Unrecognized kind: {kind}")

    def _find_name(self, name):
        if name in self.locals:
            return self.locals[name], "local"
        elif name in self.arguments:
            return self.arguments[name], "argument"
        elif name in self.fields:
            return self.fields[name], "this"
        elif name in self.statics:
            return self.statics[name], "static"
        else:
            raise Exception(f"No definition for name in the current scope: {name}")


    def __str__(self):
        return "\n".join(
            [ "SymbolTable {" ]
            + [f"  {type_} {name}  // static {index}" for (name, (type_, index)) in self.statics.items()]
            + [f"  {type_} {name}  // this {index}" for (name, (type_, index)) in self.fields.items()]
            + [""]
            + [f"  {type_} {name}  // argument {index}" for (name, (type_, index)) in self.arguments.items()]
            + [f"  {type_} {name}  // local {index}" for (name, (type_, index)) in self.locals.items()]
            + [ "}" ]
        )



#### I have just realized that I have been using AssemblySource to emit VM code, which it was never
#### meant to do, and may be a completely dopey idea. Need to revisit and/or generalize it.

def compile_class(ast: Class, asm: AssemblySource):
    symbol_table = SymbolTable(ast.name)

    for vd in ast.varDecs:
        for n in vd.names:
            kind = "static" if vd.static else "this"
            symbol_table.define(n, vd.type, kind)

    for decl in ast.subroutineDecs:
        compile_subroutineDec(decl, symbol_table, asm)
        asm.blank()


def compile_subroutineDec(ast: SubroutineDec, symbol_table: SymbolTable, asm: AssemblySource):
    if not _is_terminal_function(ast, symbol_table) and not _has_final_return(ast.body.statements):
        raise Exception(f'Missing "return" in {symbol_table.class_name}.{ast.name}')

    symbol_table.start_subroutine(ast.name, ast.kind)

    if ast.kind == "method":
        # Note: reserve space on the stack, but this is never actually looked up by name.
        symbol_table.define("<this>", symbol_table.class_name, "argument")

    for p in ast.params:
        symbol_table.define(p.name, p.type, "argument")

    for vd in ast.body.varDecs:
        for n in vd.names:
            symbol_table.define(n, vd.type, "local")

    # print(symbol_table)

    if ast.kind == "constructor":
        instance_word_count = symbol_table.count("this")
        num_vars = symbol_table.count("local")

        if ast.name != "new":
            raise Exception(f'Must be named "new": {symbol_table.context()}')
        elif ast.result != symbol_table.class_name:
            raise Exception(f'Result type does not match: {symbol_table.context()}')
        elif ast.body.statements[-1] != ReturnStatement(KeywordConstant("this")):
            raise Exception(f'Does not return "this": {symbol_table.context()}')

        asm.instr(f"function {symbol_table.class_name}.{ast.name} {num_vars}")

        asm.instr(f"push constant {instance_word_count}")
        asm.instr(f"call Memory.alloc 1")
        asm.instr("pop pointer 0")

        for stmt in ast.body.statements:
            compile_statement(stmt, symbol_table, asm)


    elif ast.kind == "function":
        num_vars = max(1, symbol_table.count("local"))  # space for return values?

        asm.instr(f"function {symbol_table.class_name}.{ast.name} {num_vars}")

        for stmt in ast.body.statements:
            compile_statement(stmt, symbol_table, asm)

    elif ast.kind == "method":
        num_vars = max(1, symbol_table.count("local"))  # space for return values?

        asm.instr(f"function {symbol_table.class_name}.{ast.name} {num_vars}")

        # Stash the (implicit) `this` argument:
        asm.instr(f"push argument 0")
        asm.instr(f"pop pointer 0")

        for stmt in ast.body.statements:
            compile_statement(stmt, symbol_table, asm)

    else:
        raise Exception(f"Unexpected subroutine kind: {ast.kind}")

    print(f"  compiled subroutine: {symbol_table.class_name}.{ast.name}")


def _is_terminal_function(ast: SubroutineDec, symbol_table: SymbolTable) -> bool:
    return symbol_table.class_name == "Sys" and ast.name in ("error", "halt")

def _has_final_return(stmts: Sequence[Statement]) -> bool:
    if len(stmts) == 0:
        return False

    last = stmts[-1]
    if isinstance(last, ReturnStatement):
        return True
    elif isinstance(last, DoStatement):
        if last.expr.class_name == "Sys" and last.expr.sub_name in ("error", "halt"):
            return True
    elif isinstance(last, IfStatement):
        if (_has_final_return(last.when_true) and
                (last.when_false is not None and _has_final_return(last.when_false))):
            return True

    return False


def compile_statement(ast: StatementRec, symbol_table: SymbolTable, asm: AssemblySource):
    if isinstance(ast, LetStatement):
        compile_let_statement(ast, symbol_table, asm)

    elif isinstance(ast, IfStatement):
        compile_if_statement(ast, symbol_table, asm)

    elif isinstance(ast, WhileStatement):
        compile_while_statement(ast, symbol_table, asm)

    elif isinstance(ast, DoStatement):
        compile_do_statement(ast, symbol_table, asm)

    elif isinstance(ast, ReturnStatement):
        compile_return_statement(ast, symbol_table, asm)

    else:
        raise Exception(f"Unexpected statment: {ast}")


def compile_let_statement(ast, symbol_table, asm):
    if ast.array_index is not None:
        # First compute the destination address:
        compile_expression(ast.array_index, symbol_table, asm)
        compile_expression(VarRef(ast.name), symbol_table, asm)
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


def compile_if_statement(ast, symbol_table, asm):
    true_label = asm.next_label("IF_TRUE")
    false_label = asm.next_label("IF_FALSE")

    compile_expression(ast.cond, symbol_table, asm)
    asm.instr(f"if-goto {true_label}")
    asm.instr(f"goto {false_label}")

    asm.instr(f"label {true_label}")
    for stmt in ast.when_true:
        compile_statement(stmt, symbol_table, asm)

    if ast.when_false is not None:
        end_label = asm.next_label("IF_END")

        asm.instr(f"goto {end_label}")
        asm.instr(f"label {false_label}")
        for stmt in ast.when_false:
            compile_statement(stmt, symbol_table, asm)
        asm.instr(f"label {end_label}")
    else:
        asm.instr(f"label {false_label}")


def compile_while_statement(ast, symbol_table, asm):
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


def compile_do_statement(ast, symbol_table, asm):
    compile_expression(ast.expr, symbol_table, asm)
    asm.instr("pop temp 0")


def compile_return_statement(ast, symbol_table, asm):
    if ast.expr is None:
        asm.instr("push constant 0")
    else:
        compile_expression(ast.expr, symbol_table, asm)
    asm.instr("return")


def compile_expression(ast: ExpressionRec, symbol_table: SymbolTable, asm: AssemblySource):
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
            # All bits set: ~0 == -1. The ALU can do M=-1 in one instruction, but the
            # VM doesn't let you say that.
            asm.instr("push constant 1")
            asm.instr("neg")
        elif ast.value == False:
            asm.instr("push constant 0")
        elif ast.value is None:
            asm.instr("push constant 0")
        elif ast.value == "this":
            if symbol_table.subroutine_kind not in ("constructor", "method"):
                raise Exception(f'Undefined "this" in static context: {symbol_table.context()}')
            asm.instr("push pointer 0")
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
        # Static call (e.g. Sys.error):
        if ast.class_name is not None:
            for arg in ast.args:
                compile_expression(arg, symbol_table, asm)
            asm.instr(f"call {ast.class_name}.{ast.sub_name} {len(ast.args)}")

        # Method call, on a named object (e.g. str.charAt()):
        elif ast.var_name is not None:
            target_class = symbol_table.type_of(ast.var_name)
            compile_expression(VarRef(ast.var_name), symbol_table, asm)
            for arg in ast.args:
                compile_expression(arg, symbol_table, asm)
            asm.instr(f"call {target_class}.{ast.sub_name} {len(ast.args)+1}")

        # Method call on the implicit `this` (e.g. draw()):
        else:
            if symbol_table.subroutine_kind not in ("constructor", "method"):
                raise Exception(f'Tried to use implicit "this" in static (function) context: {symbol_table.class_name}.{symbol_table.subroutine_name}')
            target_class = symbol_table.class_name
            compile_expression(KeywordConstant("this"), symbol_table, asm)
            for arg in ast.args:
                compile_expression(arg, symbol_table, asm)
            asm.instr(f"call {target_class}.{ast.sub_name} {len(ast.args)+1}")


    elif isinstance(ast, BinaryExpression):
        compile_expression(ast.left, symbol_table, asm)
        compile_expression(ast.right, symbol_table, asm)
        compile_op(ast.op, asm)

    elif isinstance(ast, UnaryExpression):
        compile_expression(ast.expr, symbol_table, asm)
        if ast.op.symbol == "-":
            asm.instr("neg")  # Note: same symbol, different vm op.
        elif ast.op.symbol == "~":
            asm.instr("not")
        else:
            raise Exception(f"Unknown unary op: {ast.op}")

    else:
        raise Exception(f"Unexpected expression: {ast}")


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
