#! /usr/bin/env pytest

from nand.translate import AssemblySource
import project_10

import project_11


def test_symbols_statics():
    st = project_11.SymbolTable()

    st.define("x", "int", "static")
    st.define("y", "int", "static")

    assert st.count("static") == 2
    assert st.kind_of("x") == "static"
    assert st.type_of("y") == "int"
    assert st.index_of("x") == 0

def test_symbols_fields():
    st = project_11.SymbolTable()

    st.define("width", "int", "field")
    st.define("height", "int", "field")

    assert st.count("field") == 2
    assert st.kind_of("width") == "field"
    assert st.type_of("height") == "int"
    assert st.index_of("height") == 1

def test_symbols_args():
    st = project_11.SymbolTable()

    st.define("name", "string", "arg")
    st.define("isCool", "bool", "arg")

    assert st.count("arg") == 2
    assert st.kind_of("name") == "arg"
    assert st.type_of("isCool") == "bool"
    assert st.index_of("name") == 0

def test_symbols_locals():
    st = project_11.SymbolTable()

    st.define("i", "int", "local")
    st.define("j", "int", "local")

    assert st.count("local") == 2
    assert st.kind_of("i") == "local"
    assert st.type_of("j") == "int"
    assert st.index_of("j") == 1


def test_symbols_shadow():
    """A local variable *shadows* a static with the same.
    """

    st = project_11.SymbolTable()

    st.define("x", "int", "static")

    st.define("x", "string", "local")

    assert st.count("static") == 1
    assert st.count("local") == 1
    assert (st.kind_of("x"), st.type_of("x"), st.index_of("x")) == ("local", "string", 0)


def test_trivial_expression():
    ast = project_10.ExpressionP.parse(project_10.lex("1 + 2"))

    symbol_table = project_11.SymbolTable()

    asm = AssemblySource()

    project_11.compile_expression(ast, symbol_table, asm)

    assert asm.lines == [
        "  push constant 1",
        "  push constant 2",
        "  add",
    ]

def test_program_seven():
    with open("project_11/Seven/Main.jack") as f:
        src = f.read()

    ast = project_10.parse_class(project_10.lex(src))

    symbol_table = project_11.SymbolTable()

    asm = AssemblySource()

    project_11.compile_class(ast, symbol_table, asm)

    expected = """
  function Main.main 1
  push constant 1
  push constant 2
  push constant 3
  call Math.multiply 2
  add
  call Output.printInt 1
  pop temp 0
  push constant 0
  return

"""

    # assert "\n".join(asm.lines) == expected[1:-1]
    assert list(asm.lines) == expected.split("\n")[1:-1]

def test_program_average():
    with open("project_11/Average/Main.jack") as f:
        src = f.read()

    ast = project_10.parse_class(project_10.lex(src))

    symbol_table = project_11.SymbolTable()

    # TODO: just construct the symbol table and verify it's as expected:
    # a: 0, length: 1, i: 2, sum: 3

    asm = AssemblySource()

    project_11.compile_class(ast, symbol_table, asm)

    # Note: this is the exact output of the Java compiler, modulo label numbering
    expected = """
  function Main.main 4
  push constant 18
  call String.new 1
  push constant 72
  call String.appendChar 2
  push constant 111
  call String.appendChar 2
  push constant 119
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  push constant 109
  call String.appendChar 2
  push constant 97
  call String.appendChar 2
  push constant 110
  call String.appendChar 2
  push constant 121
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  push constant 110
  call String.appendChar 2
  push constant 117
  call String.appendChar 2
  push constant 109
  call String.appendChar 2
  push constant 98
  call String.appendChar 2
  push constant 101
  call String.appendChar 2
  push constant 114
  call String.appendChar 2
  push constant 115
  call String.appendChar 2
  push constant 63
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  call Keyboard.readInt 1
  pop local 1
  push local 1
  call Array.new 1
  pop local 0
  push constant 0
  pop local 2
  label WHILE_EXP_0
  push local 2
  push local 1
  lt
  not
  if-goto WHILE_END_1
  push local 2
  push local 0
  add
  push constant 16
  call String.new 1
  push constant 69
  call String.appendChar 2
  push constant 110
  call String.appendChar 2
  push constant 116
  call String.appendChar 2
  push constant 101
  call String.appendChar 2
  push constant 114
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  push constant 97
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  push constant 110
  call String.appendChar 2
  push constant 117
  call String.appendChar 2
  push constant 109
  call String.appendChar 2
  push constant 98
  call String.appendChar 2
  push constant 101
  call String.appendChar 2
  push constant 114
  call String.appendChar 2
  push constant 58
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  call Keyboard.readInt 1
  pop temp 0
  pop pointer 1
  push temp 0
  pop that 0
  push local 3
  push local 2
  push local 0
  add
  pop pointer 1
  push that 0
  add
  pop local 3
  push local 2
  push constant 1
  add
  pop local 2
  goto WHILE_EXP_0
  label WHILE_END_1
  push constant 15
  call String.new 1
  push constant 84
  call String.appendChar 2
  push constant 104
  call String.appendChar 2
  push constant 101
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  push constant 97
  call String.appendChar 2
  push constant 118
  call String.appendChar 2
  push constant 101
  call String.appendChar 2
  push constant 114
  call String.appendChar 2
  push constant 97
  call String.appendChar 2
  push constant 103
  call String.appendChar 2
  push constant 101
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  push constant 105
  call String.appendChar 2
  push constant 115
  call String.appendChar 2
  push constant 32
  call String.appendChar 2
  call Output.printString 1
  pop temp 0
  push local 3
  push local 1
  call Math.divide 2
  call Output.printInt 1
  pop temp 0
  push constant 0
  return

"""

    assert asm.lines == expected.split("\n")[1:-1]
