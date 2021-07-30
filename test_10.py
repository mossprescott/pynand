#! /usr/bin/env pytest

import pytest

from nand.jack_ast import *
from nand import parsing

import project_10

#
# Lexing:
#

# TODO: add fine-grained tests for each token type. These tests ported from nand2tetris provide good
# coverage, but they don't isolate problems well for debugging.


def test_keyword():
    tokens = project_10.lex("do")

    assert tokens == [("keyword", "do")]


def test_identifier():
    tokens = project_10.lex("done")

    assert tokens == [("identifier", "done")]


def test_symbol():
    tokens = project_10.lex("+")

    assert tokens == [("symbol", "+")]

def test_integerConstant():
    tokens = project_10.lex("012345")

    # Note: the odd formatting surivives the lexer, just because it makes the behavior more
    # consistent. In this case, it's not a problem for the parser to deal with it.
    assert tokens == [("integerConstant", "012345")]

def test_integer_overflow():
    try:
        project_10.lex("12345678")

        assert False
    except:
        pass

def test_stringConstant():
    tokens = project_10.lex('"abc def"')

    assert tokens == [("stringConstant", "abc def")]

def test_white_space():
    tokens = project_10.lex(" \n\t\n  ")

    assert tokens == []

def test_comment_simple():
    tokens = project_10.lex("// A simple comment\n")

    assert tokens == []

def test_comment_multiline():
    tokens = project_10.lex("/** A comment that  \n spans more than\n one line.\n */")

    assert tokens == []


def test_simple_statement():
    tokens = project_10.lex("let x = 10;")

    assert tokens == [
        ("keyword", "let"),
        ("identifier", "x"),
        ("symbol", "="),
        ("integerConstant", "10"),
        ("symbol", ";"),
    ]


ARRAY_TEST = """
// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/10/ArrayTest/Main.jack

// (identical to projects/09/Average/Main.jack)

/** Computes the average of a sequence of integers. */
class Main {
    function void main() {
      var Array a;
      var int length;
      var int i, sum;

	    let length = Keyboard.readInt("HOW MANY NUMBERS? ");
	    let a = Array.new(length);
	    let i = 0;

	    while (i < length) {
	        let a[i] = Keyboard.readInt("ENTER THE NEXT NUMBER: ");
	        let i = i + 1;
	    }

	    let i = 0;
	    let sum = 0;

	    while (i < length) {
	        let sum = sum + a[i];
	        let i = i + 1;
	    }

	    do Output.printString("THE AVERAGE IS: ");
	    do Output.printInt(sum / length);
	    do Output.println();

	    return;
    }
}
"""

def test_lex_array_test():
    tokens = project_10.lex(ARRAY_TEST)

    assert tokens == [
        # 0
        ("keyword", "class"),
        ("identifier", "Main"),
        ("symbol", "{"),
        ("keyword", "function"),
        ("keyword", "void"),
        ("identifier", "main"),
        ("symbol", "("),
        ("symbol", ")"),
        ("symbol", "{"),
        ("keyword", "var"),
        # 10
        ("identifier", "Array"),
        ("identifier", "a"),
        ("symbol", ";"),
        ("keyword", "var"),
        ("keyword", "int"),
        ("identifier", "length"),
        ("symbol", ";"),
        ("keyword", "var"),
        ("keyword", "int"),
        ("identifier", "i"),
        # 20
        ("symbol", ","),
        ("identifier", "sum"),
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "length"),
        ("symbol", "="),
        ("identifier", "Keyboard"),
        ("symbol", "."),
        ("identifier", "readInt"),
        ("symbol", "("),
        # 30
        ("stringConstant", "HOW MANY NUMBERS? "),
        ("symbol", ")"),
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "a"),
        ("symbol", "="),
        ("identifier", "Array"),
        ("symbol", "."),
        ("identifier", "new"),
        ("symbol", "("),
        # 40
        ("identifier", "length"),
        ("symbol", ")"),
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "i"),
        ("symbol", "="),
        ("integerConstant", "0"),
        ("symbol", ";"),
        ("keyword", "while"),
        ("symbol", "("),
        # 50
        ("identifier", "i"),
        ("symbol", "<"),
        ("identifier", "length"),
        ("symbol", ")"),
        ("symbol", "{"),
        ("keyword", "let"),
        ("identifier", "a"),
        ("symbol", "["),
        ("identifier", "i"),
        ("symbol", "]"),
        # 60
        ("symbol", "="),
        ("identifier", "Keyboard"),
        ("symbol", "."),
        ("identifier", "readInt"),
        ("symbol", "("),
        ("stringConstant", "ENTER THE NEXT NUMBER: "),
        ("symbol", ")"),
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "i"),
        # 70
        ("symbol", "="),
        ("identifier", "i"),
        ("symbol", "+"),
        ("integerConstant", "1"),
        ("symbol", ";"),
        ("symbol", "}"),
        ("keyword", "let"),
        ("identifier", "i"),
        ("symbol", "="),
        ("integerConstant", "0"),
        # 80
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "sum"),
        ("symbol", "="),
        ("integerConstant", "0"),
        ("symbol", ";"),
        ("keyword", "while"),
        ("symbol", "("),
        ("identifier", "i"),
        ("symbol", "<"),
        # 90
        ("identifier", "length"),
        ("symbol", ")"),
        ("symbol", "{"),
        ("keyword", "let"),
        ("identifier", "sum"),
        ("symbol", "="),
        ("identifier", "sum"),
        ("symbol", "+"),
        ("identifier", "a"),
        ("symbol", "["),
        # 100
        ("identifier", "i"),
        ("symbol", "]"),
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "i"),
        ("symbol", "="),
        ("identifier", "i"),
        ("symbol", "+"),
        ("integerConstant", "1"),
        ("symbol", ";"),
        # 110
        ("symbol", "}"),
        ("keyword", "do"),
        ("identifier", "Output"),
        ("symbol", "."),
        ("identifier", "printString"),
        ("symbol", "("),
        ("stringConstant", "THE AVERAGE IS: "),
        ("symbol", ")"),
        ("symbol", ";"),
        ("keyword", "do"),
        # 120
        ("identifier", "Output"),
        ("symbol", "."),
        ("identifier", "printInt"),
        ("symbol", "("),
        ("identifier", "sum"),
        ("symbol", "/"),
        ("identifier", "length"),
        ("symbol", ")"),
        ("symbol", ";"),
        ("keyword", "do"),
        # 130
        ("identifier", "Output"),
        ("symbol", "."),
        ("identifier", "println"),
        ("symbol", "("),
        ("symbol", ")"),
        ("symbol", ";"),
        ("keyword", "return"),
        ("symbol", ";"),
        ("symbol", "}"),
        ("symbol", "}"),
    ]


#
# Parsing:
#

def test_parse_keyword_constant():
    assert project_10.KeywordConstantP.parse([('keyword', 'true')]) == KeywordConstant(True)
    assert project_10.KeywordConstantP.parse([('keyword', 'false')]) == KeywordConstant(False)
    assert project_10.KeywordConstantP.parse([('keyword', 'null')]) == KeywordConstant(None)
    assert project_10.KeywordConstantP.parse([('keyword', 'this')]) == KeywordConstant("this")

    with pytest.raises(parsing.ParseFailure):
        project_10.KeywordConstantP.parse([('keyword', 'while')])

def test_parse_unary_op():
    assert project_10.UnaryOpP.parse([('symbol', '-')]) == Op("-")
    assert project_10.UnaryOpP.parse([('symbol', '~')]) == Op("~")

    with pytest.raises(parsing.ParseFailure):
        project_10.UnaryOpP.parse([('symbol', '+')])

def test_parse_binary_op():
    assert project_10.BinaryOpP.parse([('symbol', '+')]) == Op("+")
    assert project_10.BinaryOpP.parse([('symbol', '-')]) == Op("-")
    assert project_10.BinaryOpP.parse([('symbol', '*')]) == Op("*")
    assert project_10.BinaryOpP.parse([('symbol', '/')]) == Op("/")
    assert project_10.BinaryOpP.parse([('symbol', '&')]) == Op("&")
    assert project_10.BinaryOpP.parse([('symbol', '|')]) == Op("|")
    assert project_10.BinaryOpP.parse([('symbol', '<')]) == Op("<")
    assert project_10.BinaryOpP.parse([('symbol', '>')]) == Op(">")
    assert project_10.BinaryOpP.parse([('symbol', '=')]) == Op("=")

    with pytest.raises(parsing.ParseFailure):
        project_10.BinaryOpP.parse([('symbol', '~')])

    with pytest.raises(parsing.ParseFailure):
        project_10.BinaryOpP.parse([('symbol', '//')])

def test_parse_other_constants():
    assert project_10.IntegerConstantP.parse([('integerConstant', "12345")]) == IntegerConstant(12345)
    assert (project_10.StringConstantP.parse([('stringConstant', "Hello, \"world\"!")])
            == StringConstant("Hello, \"world\"!"))

def test_parse_var_ref():
    assert project_10.VarNameP.parse([('identifier', 'x')]) == VarRef("x")
    assert (project_10.VarNameP.parse([('identifier', '_a_very_long_name_is_fine_too_123')])
            == VarRef("_a_very_long_name_is_fine_too_123"))

def test_parse_array_ref():
    assert (project_10.VarNameAndArrayIndexP.parse([('identifier', 'x'), ('symbol', '['), ('integerConstant', '0'), ('symbol', ']')])
            == ArrayRef("x", IntegerConstant(0)))

def test_parse_terms():
    assert (project_10.ExpressionP.parse(project_10.lex("x + 1"))
            == BinaryExpression(VarRef("x"), Op("+"), IntegerConstant(1)))

    # Note: all operators associate to the right, which is almost definitely *not* what you want
    assert (project_10.ExpressionP.parse(project_10.lex("x + y + z"))
            == BinaryExpression(
                VarRef("x"),
                Op("+"),
                (BinaryExpression(VarRef("y"), Op("+"), VarRef("z")))))

    # Parens required here.
    assert (project_10.ExpressionP.parse(project_10.lex("(x - y) + z"))
            == BinaryExpression(
                (BinaryExpression(VarRef("x"), Op("-"), VarRef("y"))),
                Op("+"),
                VarRef("z")))


def test_parse_do_statements():
    assert (project_10.DoStatementP.parse(project_10.lex("do Output.printInt(42);"))
            == DoStatement(SubroutineCall(class_name="Output", var_name=None, sub_name="printInt", args=[IntegerConstant(42)])))

def test_parse_return_statements():
    assert (project_10.ReturnStatementP.parse(project_10.lex("return;"))
            == ReturnStatement(None))

    assert (project_10.ReturnStatementP.parse(project_10.lex("return 137;"))
            == ReturnStatement(IntegerConstant(137)))

def test_parse_let_statements():
    assert (project_10.LetStatementP.parse(project_10.lex("let x = 1;"))
            == LetStatement("x", None, IntegerConstant(1)))

    assert (project_10.LetStatementP.parse(project_10.lex("let a[0] = x + 1;"))
            == LetStatement("a", IntegerConstant(0), BinaryExpression(VarRef("x"), Op("+"), IntegerConstant(1))))

def test_parse_if_statements():
    assert (project_10.IfStatementP.parse(project_10.lex("if (debugEnabled) { do Output.printString(\"got here\"); }"))
            == IfStatement(
                VarRef("debugEnabled"),
                [DoStatement(SubroutineCall(class_name="Output", var_name=None, sub_name="printString", args=[StringConstant("got here")]))],
                None))

    assert (project_10.IfStatementP.parse(project_10.lex("if (true) { } else { do firstThing(); do secondThing(); }"))
            == IfStatement(
                KeywordConstant(True),
                [],
                [
                    DoStatement(SubroutineCall(class_name=None, var_name=None, sub_name="firstThing", args=[])),
                    DoStatement(SubroutineCall(class_name=None, var_name=None, sub_name="secondThing", args=[])),
                ]))

def test_parse_while_statements():
    assert (project_10.WhileStatementP.parse(project_10.lex("while (x > 1) { let x = x - 1; }"))
            == WhileStatement(
                BinaryExpression(VarRef("x"), Op(">"), IntegerConstant(1)),
                [ LetStatement("x", None, BinaryExpression(VarRef("x"), Op("-"), IntegerConstant(1)))]))


def test_parse_types():
    assert project_10.TypeP.parse(project_10.lex("int")) == Type("int")
    assert project_10.TypeP.parse(project_10.lex("char")) == Type("char")
    assert project_10.TypeP.parse(project_10.lex("boolean")) == Type("boolean")
    assert project_10.TypeP.parse(project_10.lex("MyClass")) == Type("MyClass")

    with pytest.raises(parsing.ParseFailure):
        project_10.TypeP.parse(project_10.lex("text"))

def test_parse_var_decs():
    assert project_10.VarDecP.parse(project_10.lex("var int x;")) == VarDec(Type("int"), ["x"])
    assert project_10.VarDecP.parse(project_10.lex("var boolean isBlue, isOvine;")) == VarDec(Type("boolean"), ["isBlue", "isOvine"])

def test_parse_subroutine_decs():
    assert (project_10.SubroutineDecP.parse(project_10.lex(
                "function void foo() { }"))
            == SubroutineDec("function", None, "foo", [], SubroutineBody([], [])))

    assert (project_10.SubroutineDecP.parse(project_10.lex(
                "constructor Thing new(int width, int height) { let area = width*height; return this; }"))
            == SubroutineDec("constructor", Type("Thing"), "new",
                [Parameter(Type("int"), "width"), Parameter(Type("int"), "height")],
                SubroutineBody(
                    [],
                    [
                      LetStatement("area", None, BinaryExpression(VarRef("width"), Op("*"), VarRef("height"))),
                      ReturnStatement(KeywordConstant("this")),
                  ])))

def test_parse_class_var_decs():
    assert (project_10.ClassVarDecP.parse(project_10.lex("static Game instance;"))
            == ClassVarDec(static=True, type=Type("Game"), names=["instance"]))

    assert (project_10.ClassVarDecP.parse(project_10.lex("field int count, limit;"))
            == ClassVarDec(static=False, type=Type("int"), names=["count", "limit"]))

def test_parse_classes():
  assert (project_10.ClassP.parse(project_10.lex("class Foo {}"))
            == Class("Foo", [], []))

  assert (project_10.ClassP.parse(project_10.lex(
              "class Counter { field int value; method void reset() { let value = 0; } }"))
            == Class("Counter",
                [ClassVarDec(False, Type("int"), ["value"])],
                [SubroutineDec("method", None, "reset", [],
                    SubroutineBody([], [LetStatement("value", None, IntegerConstant(0))]))]))


def test_parse_array_test():
    ast = project_10.parse_class(project_10.lex(ARRAY_TEST))

    print(ast)

    expected = Class("Main",
        [],
        [
          SubroutineDec("function", None, "main", [],
            SubroutineBody(
              [
                VarDec(Type("Array"), ["a"]),
                VarDec(Type("int"), ["length"]),
                VarDec(Type("int"), ["i", "sum"]),
              ],
              [
                LetStatement("length", None,
                  SubroutineCall(class_name="Keyboard", var_name=None, sub_name="readInt", args=[
                    StringConstant("HOW MANY NUMBERS? ")
                  ])),
                LetStatement("a", None,
                  SubroutineCall(class_name="Array", var_name=None, sub_name="new", args=[
                    VarRef("length")
                  ])),
                LetStatement("i", None, IntegerConstant(0)),
                WhileStatement(
                  BinaryExpression(VarRef("i"), Op("<"), VarRef("length")),
                  [
                    LetStatement("a", VarRef("i"),
                      SubroutineCall(class_name="Keyboard", var_name=None, sub_name="readInt", args=[
                        StringConstant("ENTER THE NEXT NUMBER: ")
                      ])),
                    LetStatement("i", None, BinaryExpression(VarRef("i"), Op("+"), IntegerConstant(1))),
                  ]),
                LetStatement("i", None, IntegerConstant(0)),
                LetStatement("sum", None, IntegerConstant(0)),
                WhileStatement(
                  BinaryExpression(VarRef("i"), Op("<"), VarRef("length")),
                  [
                    LetStatement("sum", None, BinaryExpression(VarRef("sum"), Op("+"), ArrayRef("a", VarRef("i")))),
                    LetStatement("i", None, BinaryExpression(VarRef("i"), Op("+"), IntegerConstant(1))),
                ]),
                DoStatement(
                  SubroutineCall(class_name="Output", var_name=None, sub_name="printString", args=[
                    StringConstant("THE AVERAGE IS: ")
                  ])),
                DoStatement(
                  SubroutineCall(class_name="Output", var_name=None, sub_name="printInt", args=[
                    BinaryExpression(VarRef("sum"), Op("/"), VarRef("length"))
                  ])),
                DoStatement(expr=
                  SubroutineCall(class_name="Output", var_name=None, sub_name="println", args=[])),
                ReturnStatement(expr=None),
              ]
            ),
          ),
        ])

    assert ast == expected