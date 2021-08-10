#! /usr/bin/env pytest

from nand import run
from nand.translate import AssemblySource
from nand.solutions import solved_12
import project_05, project_06, project_07, project_08, project_10, project_11

import project_12


def test_compile_array_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.ARRAY_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_array_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    # Note: this one's not so useful interactively, but easier to view anyway
    array_test = _parse_jack_file("examples/project_12/ArrayTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.ARRAY_CLASS)

    _translate_dependencies(translator, ["Memory"])

    _translate_raw_jack(translator, array_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)
    translator.asm.run(assembler, computer, stop_cycles=10_000, debug=True)

    assert computer.peek(8000) == 222
    assert computer.peek(8001) == 122
    assert computer.peek(8002) == 100
    assert computer.peek(8003) == 10


def test_compile_string_lib():
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    project_11.compile_class(project_12.STRING_CLASS, asm)

    assert len(asm.lines) > 0


def test_string_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    string_test = _parse_jack_file("examples/project_12/StringTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.STRING_CLASS)

    _translate_raw_jack(translator, MINIMAL_OUTPUT_LIB)

    _translate_dependencies(translator, ["Array", "Memory", "Math"])

    _translate_raw_jack(translator, string_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    output_stream = StringWriter()
    # translator.asm.run(assembler, computer, stop_cycles=400_000, tty=output_stream, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=500_000, tty=output_stream)

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
        ""
    ]


def test_compile_memory_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.MEMORY_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0

def test_memory_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    # Note: this one's not so useful interactively, but easier to view anyway
    memory_test = _parse_jack_file("examples/project_12/MemoryTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.MEMORY_CLASS)

    # Dependencies; note: need Sys.init to intialize Memory, but don't want the built-in implementation.
    _translate_raw_jack(translator, solved_12._ARRAY_CLASS)
    _translate_raw_jack(translator, minimal_sys_lib("Memory"))

    _translate_raw_jack(translator, memory_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # translator.asm.run(assembler, computer, stop_cycles=10_000, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=10_000)

    # print_free_list(computer)

    assert computer.peek(8000) == 333
    assert computer.peek(8001) == 334
    assert computer.peek(8002) == 222
    assert computer.peek(8003) == 122
    assert computer.peek(8004) == 100
    assert computer.peek(8005) == 10


def test_memory_lib_reuse():
    # TODO: a series of alloc and deAlloc calls, enough to require some amount of non-trivial
    # re-use.
    pass


def test_memory_lib_stress():
    # TODO: a series of alloc and deAlloc calls for blocks of various sizes, which will
    # fragment the heap if no effrot is made to prevent it.
    pass  # TODO


def test_compile_output_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.OUTPUT_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_output_lib_debug(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    memory_test = _parse_jack_file("examples/project_12/OutputTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.OUTPUT_CLASS)

    # Dependencies; note: need Sys.init to intialize Output, but don't want the built-in implementation.
    _translate_raw_jack(translator, solved_12._ARRAY_CLASS)
    _translate_raw_jack(translator, solved_12._MEMORY_CLASS)
    _translate_raw_jack(translator, solved_12._STRING_CLASS)
    _translate_raw_vm(translator, f"nand2tetris/tools/OS/Math.vm")
    _translate_raw_jack(translator, minimal_sys_lib(["Memory", "Math", "Output"]))

    _translate_raw_jack(translator, memory_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # translator.asm.run(assembler, computer, stop_cycles=1_000_000, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=10_000_000)

    # TODO: spot check the screen RAM
    assert computer.peek_screen(0*32 + 0) == 1



#
# Helpers, odd and ends, and so forth:
#

def print_free_list(computer):
    """Print a summary of the free list, assuming it's laid out the way the included solutions do it."""
    print("free list:")
    blockPtr = computer.peek(2048)
    while blockPtr != 0:
        print(f"  @{blockPtr}; size: {computer.peek(blockPtr)}")
        blockPtr = computer.peek(blockPtr+1)


class StringWriter:
    """Dumb "file-like object" (barely) for capturing the output from simulation in a string."""
    def __init__(self):
        self.strs = []

    def write(self, chars):
        self.strs.append(chars)
        print(chars)


ALL_LIBS = ["Memory", "Math", "Screen", "Output", "Keyboard", "Array", "String"]
LIBS_WITH_INIT = ["Memory", "Math", "Screen", "Output", "Keyboard"]

def _translate_dependencies(translator, libs):
    _translate_raw_jack(translator, minimal_sys_lib(libs))
    for lib in libs:
        # TEMP: until solved_12 has real implementations
        print(f"Warning: translating original impl: {lib}")
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
        // would be nice to write the code, but don't want o depend on the Output library.
        // var Array tty;
        // let tty = 24576; // 0x6000
        // let tty[0] = ...;

        do Sys.halt();  // Note: explictly a static call, not a method on a non-existent `this`
    }
}
""")

def _parse_jack_file(path):
    with open(path) as f:
        src = "\n".join(f.readlines())
        return project_10.parse_class(src)


MINIMAL_OUTPUT_LIB = _parse_jack_file("nand/solutions/solved_12/TerminalOutput.jack")


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