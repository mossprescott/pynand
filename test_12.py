#! /usr/bin/env pytest

import pytest

from nand import run
from nand.platform import BUNDLED_PLATFORM
from nand.translate import AssemblySource, translate_jack
import project_05, project_06, project_07, project_08, project_10

import project_12

# Note: each test uses the bundled solutions for each dependency, so that the test
# is isolated from the user's own implementation of all but the class being tested.
# That means you have to follow the suggested implementation fairly closely so your
# classes don't depend on implementation details that don't match the expected
# behavior (even if they work fine when run together.) To change that, just switch
# the default value for the `platform` parameter to `USER_PLATFORM` on any or all tests.

def test_compile_array_lib(array_class=project_12.ARRAY_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(array_class, asm)

    assert len(asm.lines) > 0

def test_array_lib(array_class=project_12.ARRAY_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    # Note: this one's not so useful interactively, but easier to view anyway
    array_test = _parse_jack_file("examples/project_12/ArrayTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, array_class)

    _translate_dependencies(translator, platform, ["Memory"])

    translate_jack(translator, platform, array_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)
    translator.asm.run(platform.assemble, computer, stop_cycles=10_000, debug=True)

    assert computer.peek(8000) == 222
    assert computer.peek(8001) == 122
    assert computer.peek(8002) == 100
    assert computer.peek(8003) == 10


def test_compile_string_lib(string_class=project_12.STRING_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(string_class, asm)

    assert len(asm.lines) > 0

def test_string_lib(string_class=project_12.STRING_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    string_test = _parse_jack_file("examples/project_12/StringTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, string_class)

    translate_jack(translator, platform, minimal_output_lib(platform))

    _translate_dependencies(translator, platform, ["Array", "Memory", "Math"])

    translate_jack(translator, platform, string_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    output_stream = StringWriter()
    translator.asm.run(platform.assemble, computer, stop_cycles=500_000, tty=output_stream, debug=True)
    # translator.asm.trace(platform.assemble, computer, stop_cycles=500_000, tty=output_stream)

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


def test_compile_memory_lib(memory_class=project_12.MEMORY_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(memory_class, asm)

    assert len(asm.lines) > 0

def test_memory_lib(memory_class=project_12.MEMORY_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    # Note: this one's not so useful interactively, but easier to view anyway
    memory_test = _parse_jack_file("examples/project_12/MemoryTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, memory_class)

    # Dependencies; note: need Sys.init to intialize Memory, but don't want the built-in implementation.
    translate_library(translator, platform, "Array")
    translate_jack(translator, platform, minimal_sys_lib("Memory", platform))

    translate_jack(translator, platform, memory_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    # translator.asm.run(platform.assemble, computer, stop_cycles=10_000, debug=True)
    translator.asm.trace(platform.assemble, computer, stop_cycles=10_000)

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
    # fragment the heap if no effort is made to prevent it.
    pass  # TODO


def test_compile_keyboard_lib(keyboard_class=project_12.OUTPUT_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(keyboard_class, asm)

    assert len(asm.lines) > 0

def test_keyboard_lib(keyboard_class=project_12.KEYBOARD_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    keyboard_test = _parse_jack_file("examples/project_12/KeyboardTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, keyboard_class)

    translate_jack(translator, platform, minimal_output_lib(platform))
    _translate_dependencies(translator, platform, ["Array", "Memory", "Math", "String"])

    translate_jack(translator, platform, keyboard_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    # TODO: put this stop-start running into a utility somewhere (translate.py?)
    # Also, make it smarter about how long to wait. Maybe: wait_for_output(), which
    # will run a lot of cycles if needed, but stops not long after the output shows
    # up.

    asm, _, _ = platform.assemble(translator.asm)
    computer.init_rom(asm)

    output = ""

    def crank(cycles=100_000):
        """Run for a while, checking the tty for output every few cycles."""
        nonlocal output
        for _ in range(cycles//50):
            computer.ticktock(cycles=50)
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


def test_compile_output_lib(output_class=project_12.OUTPUT_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(output_class, asm)

    assert len(asm.lines) > 0

def test_output_lib(output_class=project_12.OUTPUT_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    output_test = _parse_jack_file("examples/project_12/OutputTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, output_class)

    # Dependencies; note: need Sys.init to intialize Output, but don't want the built-in implementation.
    translate_library(translator, platform, "Array")
    translate_library(translator, platform, "Memory")
    translate_library(translator, platform, "String")
    translate_library(translator, platform, "Math")
    translate_jack(translator, platform, minimal_sys_lib(["Memory", "Math", "Output"], platform))

    translate_jack(translator, platform, output_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    # translator.asm.run(platform.assemble, computer, stop_cycles=1_000_000, debug=True)
    translator.asm.trace(platform.assemble, computer, stop_cycles=1_000_000)


    # Spot check the screen RAM:

    # A few lines from the A in the upper left:
    assert computer.peek_screen(0*32 + 0) == 30
    assert computer.peek_screen(1*32 + 0) == 51
    assert computer.peek_screen(4*32 + 0) == 63

    # The top line of the adjacent characters "6" and "7":
    assert computer.peek_screen((2*11)*32 + 3) == (63 << 8) | 28

# TODO: Output.println wraps back to the top of the screen after 23 lines


def test_compile_math_lib(math_class=project_12.MATH_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(math_class, asm)

    assert len(asm.lines) > 0

def test_math_lib(math_class=project_12.MATH_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    math_test = _parse_jack_file("examples/project_12/MathTest.jack", platform)

    translator = platform.translator()
    translator.preamble()

    translate_jack(translator, platform, math_class)

    translate_jack(translator, platform, minimal_sys_lib(["Math"], platform))

    translate_jack(translator, platform, math_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    translator.asm.run(platform.assemble, computer, stop_cycles=300_000, debug=True)
    # translator.asm.trace(platform.assemble, computer, stop_cycles=300_000)

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
    assert computer.peek(8017) == 771,    "12345/16"
    assert computer.peek(8018) == -771,   "-12345/16"


def test_compile_screen_lib(screen_class=project_12.SCREEN_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(screen_class, asm)

    assert len(asm.lines) > 0


def test_screen_lib(screen_class=project_12.SCREEN_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    screen_test = _parse_jack_file("examples/project_12/ScreenTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, screen_class)

    # Dependencies; note: need Sys.init to intialize Screen, but don't want the built-in implementation.
    translate_library(translator, platform, "Array")
    translate_library(translator, platform, "Memory")
    translate_library(translator, platform, "Math")
    translate_jack(translator, platform, minimal_sys_lib(["Memory", "Math", "Screen"], platform))

    translate_jack(translator, platform, screen_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    translator.asm.run(platform.assemble, computer, stop_cycles=10_000_000, debug=True)
    # translator.asm.trace(platform.assemble, computer, stop_cycles=10_000_000)

    dump_screen(computer)  # For debugging

    # If you have failures here, try running
    # `./computer.py examples/project_12/ScreenTest.jack` and see if looks like a house.
    # If later assertions fail, maybe your impl is too slow and it's just not finished after
    # 10 million cycles. See the trace logging.

    # Spot check some groups of pixels:
    assert [computer.peek_screen(220*32 + w) for w in range(32)] == [-1]*32, "ground all filled"

    assert computer.peek_screen(100*32 + 20) == -1, "house filled"
    assert computer.peek_screen(160*32 + 22) == 0, "door cleared"

    assert computer.peek_screen(64*32 + 19) != 0, "along left roof line (at least one pixel)"
    assert computer.peek_screen(50*32 + 22) != 0, "along right roof line (at least one pixel)"

    assert computer.peek_screen(6*32 + 8) == 1 << 12, "12 o-clock ray tip"
    assert computer.peek_screen(114*32 + 8) == 1 << 12, "6 o-clock ray tip"
    assert computer.peek_screen(60*32 + 5) == -64, "9 o-clock ray tip"
    assert computer.peek_screen(60*32 + 12) == 7, "3 o-clock ray tip"

    assert computer.peek_screen(20*32 + 6) == 1 << 6, "upper-left ray tip (102, 20)"
    assert computer.peek_screen(21*32 + 6) == 1 << 7, "upper-left ray next (103, 21)"


def dump_screen(computer):
    """Write the entire contents of the screen buffer to stdout."""

    print("   ", " ".join(f"{w:6d}" for w in range(32)))
    for y in range(256):
        print(f"{y:3d}", ",".join(f"{computer.peek_screen(y*32 + w):6d}" for w in range(32)))


def test_compile_sys_lib(sys_class=project_12.SYS_CLASS, platform=BUNDLED_PLATFORM):
    """First, just make sure this particular class makes it through the compiler."""

    asm = AssemblySource()
    platform.compiler(sys_class, asm)

    assert len(asm.lines) > 0

@pytest.mark.skip(reason="It's not clear what to assert here that proves anything.")
def test_sys_lib(sys_class=project_12.SYS_CLASS, platform=BUNDLED_PLATFORM, simulator='codegen'):
    sys_test = _parse_jack_file("examples/project_12/SysTest.jack", platform)

    translator = platform.translator()

    translator.preamble()

    translate_jack(translator, platform, sys_class)

    # Dependencies:
    translate_library(translator, platform, "Memory")
    translate_library(translator, platform, "Math")
    translate_library(translator, platform, "Screen")
    translate_library(translator, platform, "Output")
    translate_library(translator, platform, "Keyboard")
    translate_library(translator, platform, "Array")
    translate_library(translator, platform, "String")

    translate_jack(translator, platform, sys_test)

    translator.finish()

    translator.check_references()

    computer = run(platform.chip, simulator=simulator)

    # translator.asm.run(platform.assemble, computer, stop_cycles=10_000, debug=True)
    translator.asm.trace(platform.assemble, computer, stop_cycles=1_000_000)

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

def _translate_dependencies(translator, platform, libs):
    translate_jack(translator, platform, minimal_sys_lib(libs, platform))
    for lib in libs:
        translate_library(translator, platform, lib)


def minimal_sys_lib(libs, platform):
    """Generate a Sys implementation that only initializes the subset of libraries that
    are needed for a particular test.
    """

    return platform.parser(
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
        // TODO: it would be nice to write the code, but don't want to depend on the String library.
        // Maybe a simpler version here writing to the port directly?
        // var Array tty;
        // let tty = 24576; // 0x6000
        // let tty[0] = ...;

        do Sys.halt();  // Note: explictly a static call, not a method on a non-existent `this`
    }
}
""")

def _parse_jack_file(path, platform):
    with open(path) as f:
        src = "\n".join(f.readlines())
        return platform.parser(src)


def minimal_output_lib(platform):
    return _parse_jack_file("nand/solutions/solved_12/TerminalOutput.jack", platform)


def translate_library(translator, platform, class_name):
    """Locate a class by name from the "OS" library provided with the Platform, and load it
    for use as a dependency.
    """

    matching = [cl for cl in platform.library if cl.name == class_name]
    if len(matching) == 1:
        translate_jack(translator, platform, matching[0])
    else:
        raise Exception(f"Could not find a class {class_name!r} in the platform's library ({[cl.name for cl in platform.library]})")
