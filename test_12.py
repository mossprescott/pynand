#! /usr/bin/env pytest

from nand import run
from nand.translate import AssemblySource
import project_05, project_06, project_07, project_08, project_10, project_11

import project_12


def test_compile_array_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_10.parse_class(project_12.ARRAY_CLASS)

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_array_lib(chip=project_05.Computer, assembler=project_06.assemble, translator=project_08.Translator, simulator='codegen'):
    array_test = project_10.parse_class("""
// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/12/ArrayTest/Main.jack

/** Test program for the OS Array class. */
class Main {

    /** Performs several Array manipulations. */
    function void main() {
        var Array r;                  // stores test results
        var Array a, b, c;

        let r = 8000;

        let a = Array.new(3);
        let a[2] = 222;
        let r[0] = a[2];              // RAM[8000] = 222

        let b = Array.new(3);
        let b[1] = a[2] - 100;
        let r[1] = b[1];              // RAM[8001] = 122

        let c = Array.new(500);
        let c[499] = a[2] - b[1];
        let r[2] = c[499];            // RAM[8002] = 100

        do a.dispose();
        do b.dispose();

        let b = Array.new(3);
        let b[0] = c[499] - 90;
        let r[3] = b[0];              // RAM[8003] = 10

        do c.dispose();
        do b.dispose();

        return;
    }
}
""")

    translate = translator()

    translate.preamble()

    _translate_raw_jack(translate, project_10.parse_class(project_12.ARRAY_CLASS))

    _translate_dependencies(translate, ["Memory"])

    _translate_raw_jack(translate, array_test)

    translate.finish()

    check_references(translate)

    computer = run(chip, simulator=simulator)
    translate.asm.run(assembler, computer, stop_cycles=10_000, debug=True)

    assert computer.peek(8000) == 222
    assert computer.peek(8001) == 122
    assert computer.peek(8002) == 100
    assert computer.peek(8003) == 10


def test_compile_string_lib():
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    project_11.compile_class(project_12.STRING_CLASS, asm)

    assert len(asm.lines) > 0


def test_string_lib(chip=project_05.Computer, assembler=project_06.assemble, translator=project_08.Translator, simulator='codegen'):
    string_test = project_10.parse_class("""
// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/12/StringTest/Main.jack

/** Test program for the OS String class. */
class Main {

    /** Performs various string manipulations and displays their results. */
    function void main() {
        var String s;
        var String i;

        let s = String.new(0); // a zero-capacity string should be supported
        do s.dispose();

        let s = String.new(6); // capacity 6, make sure that length 5 is displayed
        let s = s.appendChar(97);
        let s = s.appendChar(98);
        let s = s.appendChar(99);
        let s = s.appendChar(100);
        let s = s.appendChar(101);
        do Output.printString("new,appendChar: ");
        do Output.printString(s);                // new, appendChar: abcde
        do Output.println();

        let i = String.new(6);
        do i.setInt(12345);
        do Output.printString("setInt: ");
        do Output.printString(i);                // setInt: 12345
        do Output.println();

        do i.setInt(-32767);
        do Output.printString("setInt: ");
        do Output.printString(i);                // setInt: -32767
        do Output.println();

        do Output.printString("length: ");
        do Output.printInt(s.length());          // length: 5
        do Output.println();

        do Output.printString("charAt[2]: ");
        do Output.printInt(s.charAt(2));         // charAt[2]: 99
        do Output.println();

        do s.setCharAt(2, 45);
        do Output.printString("setCharAt(2,'-'): ");
        do Output.printString(s);                // setCharAt(2,'-'): ab-de
        do Output.println();

        do s.eraseLastChar();
        do Output.printString("eraseLastChar: ");
        do Output.printString(s);                // eraseLastChar: ab-d
        do Output.println();

        let s = "456";
        do Output.printString("intValue: ");
        do Output.printInt(s.intValue());        // intValue: 456
        do Output.println();

        let s = "-32123";
        do Output.printString("intValue: ");
        do Output.printInt(s.intValue());        // intValue: -32123
        do Output.println();

        do Output.printString("backSpace: ");
        do Output.printInt(String.backSpace());  // backSpace: 129
        do Output.println();

        do Output.printString("doubleQuote: ");
        do Output.printInt(String.doubleQuote());// doubleQuote: 34
        do Output.println();

        do Output.printString("newLine: ");
        do Output.printInt(String.newLine());    // newLine: 128
        do Output.println();

        do i.dispose();
        do s.dispose();

        return;
    }
}
""")

    translate = translator()

    translate.preamble()

    _translate_raw_jack(translate, project_12.STRING_CLASS)

    _translate_raw_jack(translate, MINIMAL_OUTPUT_LIB)

    _translate_dependencies(translate, ["Array", "Memory", "Math"])

    _translate_raw_jack(translate, string_test)

    translate.finish()

    check_references(translate)

    computer = run(chip, simulator=simulator)

    output_stream = StringWriter()
    translate.asm.run(assembler, computer, stop_cycles=400_000, tty=output_stream)

    output_lines = "".join(output_stream.strs).split("\n")
    assert output_lines == [
        "new,appendChar: abcde",
        "setInt: 12345",
        "setInt: -32767",
        "length: 5",
        "charAt[2]: 99",
        "setCharAt(2,'-'): ab-de",
        "eraseLastChar: ab-d",
        "intValue: 456",
        "intValue: -32123",
        "backSpace: 129",
        "doubleQuote: 34",
        "newLine: 128",
    ]


class StringWriter:
    """Dumb "file-like object" (barely) for capturing the output from simulation in a string."""
    def __init__(self):
        self.strs = []

    def write(self, chars):
        self.strs.append(chars)


ALL_LIBS = ["Memory", "Math", "Screen", "Output", "Keyboard", "Array", "String"]
LIBS_WITH_INIT = ["Memory", "Math", "Screen", "Output", "Keyboard"]

def _translate_dependencies(translator, libs):
    _translate_raw_jack(translator, minimal_sys_lib(libs))
    for lib in libs:
        # TEMP: until solved_12 has real implementations
        _translate_raw_vm(translator, f"nand2tetris/tools/OS/{lib}.vm")


def minimal_sys_lib(libs):
    """Generate a Sys implementation that only initializes the subset of libraries that
    are needed for a particular test.
    """

    return project_10.parse_class(
"""
class Sys {
    function void init() {
"""
+
"\n".join(f"        do {lib}.init();" for lib in LIBS_WITH_INIT if lib in libs)
+
"""
        do Main.main();
        do Sys.halt();  // Note: explictly a static call, not a method on a non-existent `this`
        return;  // as if
    }

    function void halt() {
        while (true) {}
    }

    function void error(int errorCode) {
        // var Array tty;
        // let tty = 24576; // 0x6000
        // let tty[0] = ...;

        do Sys.halt();  // Note: explictly a static call, not a method on a non-existent `this`
    }
}
""")

# For test purposes, this implementation of the Output class just writes characters to the "TTY"
# port, and doesn't update the screen at all. That saves a lot of time, and it means we can test
# String operations without trying to inspect the screen buffer (or even having drawing to the
# screen working at all.)
MINIMAL_OUTPUT_LIB = project_10.parse_class("""
class Output {
    field String temp;

    function void init() {
        let temp = String.new(6);  // enough space for any int
        return;
    }

    // Ignored.
    function void moveCursor(int i, int j) {
        return;
    }

    function void printChar(char c) {
        var Array tty;

        let tty = 24576;  // 0x6000
        let tty[0] = c;

        return;
    }

    function void printString(String s) {
        // Note: writing directly here (as opposed to calling printChar) saves some cycles.
        // However, we don't this to be *too* efficient, because whoever's polling the TTY
        // port needs to check it often enough to see each character as it goes by.
        // That is, you can't just write one value after another to memory as fast as you
        // please, and there's no way from inside the CPU to see if the last value you wrote
        // has been consumed yet.
        // That's probably not going to be a problem, since String.charAt() should involve
        // plenty of overhead.

        var Array tty;
        var int length, ptr;

        let tty = 24576;  // 0x6000

        let length = s.length();
        let ptr = 0;
        while (ptr < length) {
            let tty[0] = s.charAt(ptr);
            let ptr = ptr + 1;
        }
        return;
    }

    function void printInt(int i) {
        do temp.setInt(i);
        do Output.printString(temp);
        return;
    }

    function void println() {
        var Array tty;

        let tty = 24576;   // 0x6000
        let tty[0] = 128;  // same as String.newLine()

        return;
    }

    // Ignored, for now. What should it do? Write a backspace character?
    function void backSpace() {
        return;
    }
}
""")

def _translate_raw_jack(translator, ast):
    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    # HACK: re-use the impl in nand.translate somehow?
    for op, args in [project_07.parse_line(l) for l in asm.lines if project_07.parse_line(l) is not None]:
        translator.__getattribute__(op)(*args)


### TEMP: until solved_12 is a full implementation
def _translate_raw_vm(translator, src_path):
    with open(src_path) as f:
        for op, args in [project_07.parse_line(l) for l in f.readlines() if project_07.parse_line(l) is not None]:
            translator.__getattribute__(op)(*args)


def check_references(translator):
    """Check for obvious "linkage" errors: functions that are referenced but never defined.

    WARNING: this is currently making completely unfounded assumptions about the translator.
    TODO: somehow inspect the VM ops, maybe, and avoid that assumption.
    """

    defined = set(translator.solved.defined_functions)
    referenced = set(translator.solved.referenced_functions)

    assert len(translator.solved.defined_functions) == len(defined), "Each function is defined only once"

    unresolved = referenced - defined
    assert unresolved == set(), "Unresolved references"