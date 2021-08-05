#! /usr/bin/env pytest

from nand import run
from nand.translate import AssemblySource
import project_05, project_06, project_07, project_08, project_10, project_11

import project_12


def test_compile_array_lib():
    """First, just make sure this particular class makes it through the compiler."""

    src = project_12.ARRAY_CLASS

    ast = project_10.parse_class(project_10.lex(src))

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_array_lib(chip=project_05.Computer, assembler=project_06.assemble, translator=project_08.Translator, simulator='codegen'):
    array_test = """
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
"""

    translate = translator()

    translate.preamble()

    _translate_raw_jack(translate, project_12.ARRAY_CLASS)

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


def _translate_dependencies(translator, libs=["Memory", "Math", "Screen", "Output", "Keyboard"]):
    _translate_raw_jack(translator, minimal_sys_lib(libs))
    for lib in libs:
        _translate_raw_vm(translator, f"nand2tetris/tools/OS/{lib}.vm")


def minimal_sys_lib(libs):
    """Generate a Sys implementation that only initializes the subset of libraries that
    are needed for a particular test.
    """

    return (
"""
class Sys {
    function void init() {
"""
+
"\n".join(f"        do {lib}.init();" for lib in libs)
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
        do Sys.halt();  // Note: explictly a static call, not a method on a non-existent `this`
    }
}
""")


def _translate_raw_jack(translator, src):
    ast = project_10.parse_class(project_10.lex(src))

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