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


def test_compile_keyboard_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.KEYBOARD_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0

def test_keyboard_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    # Note: this one's not so useful interactively, but easier to view anyway
    keyboard_test = _parse_jack_file("examples/project_12/KeyboardTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.KEYBOARD_CLASS)

    _translate_raw_jack(translator, MINIMAL_OUTPUT_LIB)
    _translate_dependencies(translator, ["Array", "Memory", "Math", "String"])

    _translate_raw_jack(translator, keyboard_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # TODO: put this stop-start running into a utility somewhere (translate.py?)
    # Also, make it smarter about how long to wait. Maybe: wait_for_output(), which
    # will run a lot of cycles if needed, but stops not long after the output shows
    # up.

    asm = assembler(translator.asm)
    computer.init_rom(asm)

    output = ""

    def crank(cycles=100_000):
        """Run for a while, checking the tty for output every few cycles."""
        nonlocal output
        for _ in range(cycles//100):
            computer.ticktock(cycles=100)
            computer.ticktock()
            c = computer.get_tty()
            if c != 0:
                if c == 128:
                    output += "\n"
                else:
                    output += chr(c)

    def type_key(code):
        computer.set_keydown(code)
        crank()
        computer.set_keydown(0)
        crank()

    crank(1_000_000)

    assert output.endswith("Please press the 'Page Down' key")

    type_key(137)  # page down

    assert output.endswith("Please press the number '3': ")

    type_key(ord("3"))

    assert "Please press the number '3': 3\nok\n" in output

    type_key(ord("J"))
    type_key(ord("A"))
    type_key(ord("C"))
    type_key(ord("C"))
    type_key(129)  # backspace
    type_key(ord("K"))
    type_key(128)  # newline

    # Note: the backspace is ignored by the TTY-only Output impl.
    assert "Please type 'JACK' and press enter: JACCK\nok\n" in output

    for c in "-32123":
        type_key(ord(c))
    type_key(128)  # newline

    assert output.endswith("Test completed successfully")


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
    # TODO: need the "private" helper from solved_12._OUTPUT_CLASS,
    # if the default impl is used. Get rid of it.

    # Dependencies; note: need Sys.init to intialize Output, but don't want the built-in implementation.
    _translate_raw_jack(translator, solved_12._ARRAY_CLASS)
    _translate_raw_jack(translator, solved_12._MEMORY_CLASS)
    _translate_raw_jack(translator, solved_12._STRING_CLASS)
    _translate_raw_jack(translator, solved_12._MATH_CLASS)
    _translate_raw_jack(translator, minimal_sys_lib(["Memory", "Math", "Output"]))

    _translate_raw_jack(translator, memory_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # translator.asm.run(assembler, computer, stop_cycles=1_000_000, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=1_000_000)


    # Spot check the screen RAM:

    # A few lines from the A in the upper left:
    assert computer.peek_screen(0*32 + 0) == 30
    assert computer.peek_screen(1*32 + 0) == 51
    assert computer.peek_screen(4*32 + 0) == 63

    # The top line of the adjacent characters "6" and "7":
    assert computer.peek_screen((2*11)*32 + 3) == (63 << 8) | 28

# TODO: Output.println wraps back to the top of the screen after 23 lines


def test_compile_math_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.MATH_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_math_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    math_test = _parse_jack_file("examples/project_12/MathTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.MATH_CLASS)

    _translate_raw_jack(translator, minimal_sys_lib(["Math"]))

    _translate_raw_jack(translator, math_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # translator.asm.run(assembler, computer, stop_cycles=10_000, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=1_000_000)

    assert computer.peek(8000) == 6,      "multiply(2, 3)"
    assert computer.peek(8001) == -180,   "multiply(6, -30)"
    assert computer.peek(8002) == -18000, "multiply(-180, 100)"
    assert computer.peek(8003) == -18000, "multiply(1, -18000)"
    assert computer.peek(8004) == 0,      "multiply(-18000, 0)"

    assert computer.peek(8005) == 3,      "divide(9, 3)"
    assert computer.peek(8006) == -3000,  "divide(-18000, 6)"
    assert computer.peek(8007) == 0,      "divide(32766, -32767)"

    assert computer.peek(8008) == 3,      "sqrt(9)"
    assert computer.peek(8009) == 181,    "sqrt(32767)"

    assert computer.peek(8010) == 123,    "min(3445, 123)"
    assert computer.peek(8011) == 123,    "max(123, -345)"
    assert computer.peek(8012) == 27,     "abs(27)"
    assert computer.peek(8013) == 32767,  "abs(-32767)"

    # Additional cases:
    assert computer.peek(8014) == 3000,   "30000/10"
    assert computer.peek(8015) == -3276,  "-32767/10"
    assert computer.peek(8016) == -32768, "abs(-32768)"


def test_compile_screen_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.SCREEN_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_screen_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    screen_test = _parse_jack_file("examples/project_12/ScreenTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.SCREEN_CLASS)

    _translate_raw_jack(translator, minimal_sys_lib([]))

    _translate_raw_jack(translator, screen_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # translator.asm.run(assembler, computer, stop_cycles=3_000_000, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=3_000_000)

    # TODO: spot check some pixels
    assert False


def test_compile_sys_lib():
    """First, just make sure this particular class makes it through the compiler."""

    ast = project_12.SYS_CLASS

    asm = AssemblySource()
    project_11.compile_class(ast, asm)

    assert len(asm.lines) > 0


def test_sys_lib(chip=project_05.Computer, assembler=project_06.assemble, translator_class=project_08.Translator, simulator='codegen'):
    sys_test = _parse_jack_file("examples/project_12/SysTest.jack")

    translator = translator_class()

    translator.preamble()

    _translate_raw_jack(translator, project_12.SYS_CLASS)

    _translate_raw_jack(translator, solved_12._MEMORY_CLASS)
    _translate_raw_jack(translator, solved_12._MATH_CLASS)
    _translate_raw_jack(translator, solved_12._SCREEN_CLASS)
    _translate_raw_jack(translator, solved_12._OUTPUT_CLASS)
    _translate_raw_jack(translator, solved_12._KEYBOARD_CLASS)
    _translate_raw_jack(translator, solved_12._ARRAY_CLASS)
    _translate_raw_jack(translator, solved_12._STRING_CLASS)

    _translate_raw_jack(translator, sys_test)

    translator.finish()

    check_references(translator)

    computer = run(chip, simulator=simulator)

    # translator.asm.run(assembler, computer, stop_cycles=10_000, debug=True)
    translator.asm.trace(assembler, computer, stop_cycles=1_000_000)

    # TODO: assert what?
    assert False


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
        # # TEMP: until solved_12 has real implementations
        # print(f"Warning: translating original impl: {lib}")
        # _translate_raw_vm(translator, f"nand2tetris/tools/OS/{lib}.vm")
        if lib == "Memory":
            _translate_raw_jack(translator, solved_12._MEMORY_CLASS)
        elif lib == "Math":
            _translate_raw_jack(translator, solved_12._MATH_CLASS)
        elif lib == "Screen":
            _translate_raw_jack(translator, solved_12._SCREEN_CLASS)
        elif lib == "Output":
            _translate_raw_jack(translator, solved_12._OUTPUT_CLASS)
        elif lib == "Keyboard":
            _translate_raw_jack(translator, solved_12._KEYBOARD_CLASS)
        elif lib == "Array":
            _translate_raw_jack(translator, solved_12._ARRAY_CLASS)
        elif lib == "String":
            _translate_raw_jack(translator, solved_12._STRING_CLASS)
        else:
            raise Exception(f"Unknown class: {lib}")



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
        // TODO: it would be nice to write the code, but don't want to depend on the OutputString library.
        // Maybe a simpler version here writing to the port directly?
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