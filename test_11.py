#! /usr/bin/env pytest

import pytest

from nand.translate import AssemblySource
import project_10

import project_11


def test_symbols_statics():
    st = project_11.SymbolTable("Main")

    st.define("x", "int", "static")
    st.define("y", "int", "static")

    assert st.count("static") == 2
    assert st.kind_of("x") == "static"
    assert st.type_of("y") == "int"
    assert st.index_of("x") == 0

def test_symbols_fields():
    st = project_11.SymbolTable("Main")

    st.define("width", "int", "this")
    st.define("height", "int", "this")

    assert st.count("this") == 2
    assert st.kind_of("width") == "this"
    assert st.type_of("height") == "int"
    assert st.index_of("height") == 1

def test_symbols_args():
    st = project_11.SymbolTable("Main")

    st.define("name", "string", "argument")
    st.define("isCool", "bool", "argument")

    assert st.count("argument") == 2
    assert st.kind_of("name") == "argument"
    assert st.type_of("isCool") == "bool"
    assert st.index_of("name") == 0

def test_symbols_locals():
    st = project_11.SymbolTable("Main")

    st.define("i", "int", "local")
    st.define("j", "int", "local")

    assert st.count("local") == 2
    assert st.kind_of("i") == "local"
    assert st.type_of("j") == "int"
    assert st.index_of("j") == 1


def test_symbols_shadow():
    """A local variable *shadows* a static with the same.
    """

    st = project_11.SymbolTable("Main")

    st.define("x", "int", "static")

    st.start_subroutine("main", "function")

    st.define("x", "string", "local")

    assert st.count("static") == 1
    assert st.count("local") == 1
    assert (st.kind_of("x"), st.type_of("x"), st.index_of("x")) == ("local", "string", 0)


def test_symbols_context():
    st = project_11.SymbolTable("Main")

    st.define("x", "int", "static")

    assert st.context() == "class Main"

    st.start_subroutine("main", "function")

    assert st.context() == "function Main.main"


#
# Compile: expressions
#

def test_trivial_expression():
    ast = project_10.ExpressionP.parse(project_10.lex("1 + 2"))

    symbol_table = project_11.SymbolTable("Main")
    asm = AssemblySource()
    project_11.compile_expression(ast, symbol_table, asm)

    assert asm.lines == [
        "  push constant 1",
        "  push constant 2",
        "  add",
    ]


#
# Compile: program fragments
#

@pytest.mark.skip("This isn't part of the spec; might make a great addition.")
def test_other_instance_field_access():
    ast = project_10.parse_class("""
        class BoxedInt {
            field int value;

            method boolean compare(BoxedInt other) {
                return value < other.value;
            }
        }
        """)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert asm.lines == [
        "  function BoxedInt.compare 1",
        "  push argument 0",
        "  pop pointer 0",
        "  push this 0",
        "  push argument 1",
        "  pop pointer 1",
        "  push that 0",
        "  lt",
        "  return",
        "",
    ]

def test_call_function_from_function_context():
    ast = project_10.parse_class("""
        class Foo {
            function void run() {
                do Bar.go();
                return;
            }
        }
        """)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert asm.lines == [
        "  function Foo.run 1",
        "  call Bar.go 0",
        "  pop temp 0",
        "  push constant 0",
        "  return",
        "",
    ]

def test_call_method_from_method_context():
    ast = project_10.parse_class("""
        class Foo {
            method void run() {
                do go();
                return;
            }
        }
        """)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert asm.lines == [
        "  function Foo.run 1",
        "  push argument 0",
        "  pop pointer 0",
        "  push pointer 0",  # implicit `this` for self call
        "  call Foo.go 1",
        "  pop temp 0",
        "  push constant 0",
        "  return",
        "",
    ]

def test_field_in_function_context():
    """A common error case; referring to an instance member within a function."""

    ast = project_10.parse_class("""
        class Foo {
            field int x;

            function int run() {
                return x;
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Tried to use field "x" in static context: function Foo.run',)

def test_call_method_from_function_context():
    """A common error case; referring to a function using the method-call syntax."""

    ast = project_10.parse_class("""
        class Foo {
            function void run() {
                do go();  // Probably meant `Foo.go()`
                return;
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Tried to use implicit "this" in static (function) context: Foo.run',)

def test_missing_return():
    """Another very common error."""

    ast = project_10.parse_class("""
        class Foo {
            function void noReturn() {
                // oops, forgot to `return;` here
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Missing "return" in Foo.noReturn',)

def test_return_on_both_branches():
    """Accept this common pattern."""

    ast = project_10.parse_class("""
        class Foo {
            function void toInt(boolean x) {
                if (x) {
                    return 1;
                }
                else {
                    return 0;
                }
            }
        }
        """)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    # Ok if we got here with no error

def test_constructor_wrong_name():
    """This could be confusing, so make it an error."""

    ast = project_10.parse_class("""
        class Foo {
            constructor Foo notNew() {
                return this;
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Must be named "new": constructor Foo.notNew',)

def test_constructor_bad_result_type():
    """This could be confusing, so make it an error."""

    ast = project_10.parse_class("""
        class Foo {
            constructor Bar new() {
                return this;
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Result type does not match: constructor Foo.new',)

def test_constructor_void_return():
    """Constructor must return "this", or the caller will be surprised."""

    ast = project_10.parse_class("""
        class Foo {
            constructor Foo new() {
                return;  // meaning "null"
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Does not return "this": constructor Foo.new',)



def test_no_this():
    """This could be confusing, so make it an error."""

    ast = project_10.parse_class("""
        class Foo {
            function void run() {
                return this;
            }
        }
        """)

    with pytest.raises(Exception) as exc_info:
        asm = AssemblySource()
        project_11.compile_class(ast, asm)
    assert exc_info.value.args == ('Undefined "this" in static context: function Foo.run',)


#
# Compile: full programs
#
def test_program_seven():
    with open("examples/project_11/Seven/Main.jack") as f:
        src = f.read()

    ast = project_10.parse_class(src)

    asm = AssemblySource()

    project_11.compile_class(ast, asm)

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

    assert list(asm.lines) == expected.split("\n")[1:-1]

def test_program_average():
    with open("examples/project_11/Average/Main.jack") as f:
        src = f.read()

    ast = project_10.parse_class(src)

    # TODO: just construct the symbol table and verify it's as expected:
    # a: 0, length: 1, i: 2, sum: 3

    asm = AssemblySource()

    project_11.compile_class(ast, asm)

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
