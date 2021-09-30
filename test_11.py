#! /usr/bin/env pytest

import pytest

from nand import run
from nand.platform import BUNDLED_PLATFORM
from nand.translate import AssemblySource, translate_library
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
def test_program_seven_opcodes():
    """This program is so simple that there's probably only one reasonable way to compile it,
    so just compare the VM opcodes."""

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


def test_program_average_compile():
    # Isolate the compiler by using the included solution for everything else:
    platform = BUNDLED_PLATFORM
    simulator = "codegen"

    with open("examples/project_11/Average/Main.jack") as f:
        src = f.read()

    ast = platform.parser(src)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    # If it fails, you probably want to see the opcodes it wrote:
    for l in asm.lines:
        print(l)

    ops = [platform.parse_line(l) for l in asm.lines if platform.parse_line(l) is not None]

    translator = platform.translator()
    translator.preamble()

    for op in ops:
        translator.handle(op)

    translate_library(translator, platform)

    translator.finish()
    translator.check_references()

    # TODO: would need to provide input via the keyboard port (see test_12.test_keyboard_lib)

    # computer = run(platform.chip, simulator=simulator)

    # output_stream = StringWriter()
    # translator.asm.run(platform.assemble, computer, stop_cycles=200_000, debug=True, tty=output_stream)

    # output_lines = "".join(output_stream.strs).split("\n")
    # assert output_lines == [
    #     # TODO
    # ]


def test_program_convert_to_bin():
    # Isolate the compiler by using the included solution for everything else:
    platform = BUNDLED_PLATFORM
    simulator = "codegen"

    with open("examples/project_11/ConvertToBin/Main.jack") as f:
        src = f.read()

    ast = platform.parser(src)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    # If it fails, you probably want to see the opcodes it wrote:
    for l in asm.lines:
        print(l)

    ops = [platform.parse_line(l) for l in asm.lines if platform.parse_line(l) is not None]

    translator = platform.translator()
    translator.preamble()

    for op in ops:
        translator.handle(op)

    # Note: using the full OS implementation is simpler then the fancy tricks done in test_12
    # to isolate individual OS classes, but it also means that this test might need 100s
    # of thousands of cycles to run (mainly initializing the OS unnecessarily.)
    translate_library(translator, platform)

    translator.finish()
    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    computer.poke(8000, 0xBEEF)

    translator.asm.run(platform.assemble, computer, stop_cycles=200_000, debug=True)

    for b in range(16):
        assert computer.peek(8001+b) == bool(0xBEEF & (1 << b))


def test_program_complex_arrays():
    # Isolate the compiler by using the included solution for everything else:
    platform = BUNDLED_PLATFORM
    simulator = "codegen"

    with open("examples/project_11/ComplexArrays/Main.jack") as f:
        src = f.read()

    ast = platform.parser(src)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    # If it fails, you probably want to see the opcodes it wrote:
    for l in asm.lines:
        print(l)

    ops = [platform.parse_line(l) for l in asm.lines if platform.parse_line(l) is not None]

    translator = platform.translator()
    translator.preamble()

    for op in ops:
        translator.handle(op)

    # Note: using the full OS implementation is simpler then the fancy tricks done in test_12
    # to isolate individual OS classes, but it also means that this test might need millions of
    # cycles to run, including writing all the results to the screen buffer.
    translate_library(translator, platform)

    translator.finish()
    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    output_stream = StringWriter()
    translator.asm.run(platform.assemble, computer, stop_cycles=5_000_000, debug=True, tty=output_stream)

    output_lines = "".join(output_stream.strs).split("\n")
    assert output_lines == [
        "Test 1: expected result: 5; actual result: 5",
        "Test 2: expected result: 40; actual result: 40",
        "Test 3: expected result: 0; actual result: 0",
        "Test 4: expected result: 77; actual result: 77",
        "Test 5: expected result: 110; actual result: 110",
        "",
    ]


class StringWriter:
    """Dumb "file-like object" (barely) for capturing the output from simulation in a string."""
    def __init__(self):
        self.strs = []

    def write(self, chars):
        self.strs.append(chars)
        print(chars)
