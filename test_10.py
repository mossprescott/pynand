#! /usr/bin/env pytest

import project_10


# TODO: add fine-grained tests for each token type. These tests ported from nand2tetris provide good
# coverage, but they don't isolate problems well for debugging.


def test_keyword():
    tokens = project_10.lex("do")

    assert tokens == [("keyword", "do")]


def test_identifier():
    tokens = project_10.lex("done")

    assert tokens == [("identifier", "done")]


def test_identifier():
    tokens = project_10.lex("+")

    assert tokens == [("symbol", "+")]

def test_integerConstant():
    tokens = project_10.lex("012345")

    assert tokens == [("integerConstant", 12345)]

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
    print(tokens)

    assert tokens == [
        ("keyword", "let"),
        ("identifier", "x"),
        ("symbol", "="),
        ("integerConstant", 10),
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
        ("integerConstant", 0),
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
        ("integerConstant", 1),
        ("symbol", ";"),
        ("symbol", "}"),
        ("keyword", "let"),
        ("identifier", "i"),
        ("symbol", "="),
        ("integerConstant", 0),
        # 80
        ("symbol", ";"),
        ("keyword", "let"),
        ("identifier", "sum"),
        ("symbol", "="),
        ("integerConstant", 0),
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
        ("integerConstant", 1),
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


def test_parse_arraytest():
    ast = project_10.parse_class(project_10.lex(ARRAY_TEST))
    print(ast)
    assert ast == ("class", [
          ("keyword", "class"),
          ("identifier", "Main"),
          ("symbol", "{"),
          ("subroutineDec", [
            ("keyword", "function"),
            ("keyword", "void"),
            ("identifier", "main"),
            ("symbol", "("),
            ("parameterList", [
            ]),
            ("symbol", ")"),
            ("subroutineBody", [
              ("symbol", "{"),
              ("varDec", [
                ("keyword", "var"),
                ("identifier", "Array"),
                ("identifier", "a"),
                ("symbol", ";"),
              ]),
              ("varDec", [
                ("keyword", "var"),
                ("keyword", "int"),
                ("identifier", "length"),
                ("symbol", ";"),
              ]),
              ("varDec", [
                ("keyword", "var"),
                ("keyword", "int"),
                ("identifier", "i"),
                ("symbol", ","),
                ("identifier", "sum"),
                ("symbol", ";"),
              ]),
              ("statements", [
                ("letStatement", [
                  ("keyword", "let"),
                  ("identifier", "length"),
                  ("symbol", "="),
                  ("expression", [
                    ("term", [
                      ("identifier", "Keyboard"),
                      ("symbol", "."),
                      ("identifier", "readInt"),
                      ("symbol", "("),
                      ("expressionList", [
                        ("expression", [
                          ("term", [
                            ("stringConstant", "HOW MANY NUMBERS? "),
                          ]),
                        ]),
                      ]),
                      ("symbol", ")"),
                    ]),
                  ]),
                  ("symbol", ";"),
                ]),
                ("letStatement", [
                  ("keyword", "let"),
                  ("identifier", "a"),
                  ("symbol", "="),
                  ("expression", [
                    ("term", [
                      ("identifier", "Array"),
                      ("symbol", "."),
                      ("identifier", "new"),
                      ("symbol", "("),
                      ("expressionList", [
                        ("expression", [
                          ("term", [
                            ("identifier", "length"),
                          ]),
                        ]),
                      ]),
                      ("symbol", ")"),
                    ]),
                  ]),
                  ("symbol", ";"),
                ]),
                ("letStatement", [
                  ("keyword", "let"),
                  ("identifier", "i"),
                  ("symbol", "="),
                  ("expression", [
                    ("term", [
                      ("integerConstant", 0),
                    ]),
                  ]),
                  ("symbol", ";"),
                ]),
                ("whileStatement", [
                  ("keyword", "while"),
                  ("symbol", "("),
                  ("expression", [
                    ("term", [
                      ("identifier", "i"),
                    ]),
                    ("symbol", "<"),
                    ("term", [
                      ("identifier", "length"),
                    ]),
                  ]),
                  ("symbol", ")"),
                  ("symbol", "{"),
                  ("statements", [
                    ("letStatement", [
                      ("keyword", "let"),
                      ("identifier", "a"),
                      ("symbol", "["),
                      ("expression", [
                        ("term", [
                          ("identifier", "i"),
                        ]),
                      ]),
                      ("symbol", "]"),
                      ("symbol", "="),
                      ("expression", [
                        ("term", [
                          ("identifier", "Keyboard"),
                          ("symbol", "."),
                          ("identifier", "readInt"),
                          ("symbol", "("),
                          ("expressionList", [
                            ("expression", [
                              ("term", [
                                ("stringConstant", "ENTER THE NEXT NUMBER: "),
                              ]),
                            ]),
                          ]),
                          ("symbol", ")"),
                        ]),
                      ]),
                      ("symbol", ";"),
                    ]),
                    ("letStatement", [
                      ("keyword", "let"),
                      ("identifier", "i"),
                      ("symbol", "="),
                      ("expression", [
                        ("term", [
                          ("identifier", "i"),
                        ]),
                        ("symbol", "+"),
                        ("term", [
                          ("integerConstant", 1),
                        ]),
                      ]),
                      ("symbol", ";"),
                    ]),
                  ]),
                  ("symbol", "}"),
                ]),
                ("letStatement", [
                  ("keyword", "let"),
                  ("identifier", "i"),
                  ("symbol", "="),
                  ("expression", [
                    ("term", [
                      ("integerConstant", 0),
                    ]),
                  ]),
                  ("symbol", ";"),
                ]),
                ("letStatement", [
                  ("keyword", "let"),
                  ("identifier", "sum"),
                  ("symbol", "="),
                  ("expression", [
                    ("term", [
                      ("integerConstant", 0),
                    ]),
                  ]),
                  ("symbol", ";"),
                ]),
                ("whileStatement", [
                  ("keyword", "while"),
                  ("symbol", "("),
                  ("expression", [
                    ("term", [
                      ("identifier", "i"),
                    ]),
                    ("symbol", "<"),
                    ("term", [
                      ("identifier", "length"),
                    ]),
                  ]),
                  ("symbol", ")"),
                  ("symbol", "{"),
                  ("statements", [
                    ("letStatement", [
                      ("keyword", "let"),
                      ("identifier", "sum"),
                      ("symbol", "="),
                      ("expression", [
                        ("term", [
                          ("identifier", "sum"),
                        ]),
                        ("symbol", "+"),
                        ("term", [
                          ("identifier", "a"),
                          ("symbol", "["),
                          ("expression", [
                            ("term", [
                              ("identifier", "i"),
                            ]),
                          ]),
                          ("symbol", "]"),
                        ]),
                      ]),
                      ("symbol", ";"),
                    ]),
                    ("letStatement", [
                      ("keyword", "let"),
                      ("identifier", "i"),
                      ("symbol", "="),
                      ("expression", [
                        ("term", [
                          ("identifier", "i"),
                        ]),
                        ("symbol", "+"),
                        ("term", [
                          ("integerConstant", 1),
                        ]),
                      ]),
                      ("symbol", ";"),
                    ]),
                  ]),
                  ("symbol", "}"),
                ]),
                ("doStatement", [
                  ("keyword", "do"),
                  ("identifier", "Output"),
                  ("symbol", "."),
                  ("identifier", "printString"),
                  ("symbol", "("),
                  ("expressionList", [
                    ("expression", [
                      ("term", [
                        ("stringConstant", "THE AVERAGE IS: "),
                      ]),
                    ]),
                  ]),
                  ("symbol", ")"),
                  ("symbol", ";"),
                ]),
                ("doStatement", [
                  ("keyword", "do"),
                  ("identifier", "Output"),
                  ("symbol", "."),
                  ("identifier", "printInt"),
                  ("symbol", "("),
                  ("expressionList", [
                    ("expression", [
                      ("term", [
                        ("identifier", "sum"),
                      ]),
                      ("symbol", "/"),
                      ("term", [
                        ("identifier", "length"),
                      ]),
                    ]),
                  ]),
                  ("symbol", ")"),
                  ("symbol", ";"),
                ]),
                ("doStatement", [
                  ("keyword", "do"),
                  ("identifier", "Output"),
                  ("symbol", "."),
                  ("identifier", "println"),
                  ("symbol", "("),
                  ("expressionList", [
                  ]),
                  ("symbol", ")"),
                  ("symbol", ";"),
                ]),
                ("returnStatement", [
                  ("keyword", "return"),
                  ("symbol", ";"),
                ]),
              ]),
              ("symbol", "}"),
            ]),
          ]),
          ("symbol", "}"),
        ])
