"""A namedtuple to encapsulate an implementation of everything needed to simulate a computer
and run Jack programs on it.

`chip` contains the gate-level design of the entire CPU (along with the other components
to make a Computer.) See projects 1 through 5.

`assemble` translates human-readable assembly code into machine instruction words, one
instruction at a time. See project 6.

`parse_line` and `Translator`, respectively, read VM instructions and translating them into
assembly code. See projects 7 and 8.

`parser` and `compiler`, respectively, handle Jack syntax and code generation. See projects
10 and 11.

`library` contains implementations of each of the "OS" classes. For now, they always take
the form of jack_ast.Class nodes.
TODO: allow VM source as an alternative, for comparison with the author's implementation.

Each of these components may differ from the "standard" design, as described in the original
course materials, as long as they operate on roughly the same types of data. The components
that are put together in any Platform instance should work together to run programs, but the
programs they run might be slightly different from the standard ones. For example, an alternate
platform might add new machine instructions, VM opcodes, or Jack syntax, or it might *remove*
some instructions; as long as the components work together to do something useful.
"""

import collections

from nand.solutions import solved_05, solved_06, solved_07, solved_10, solved_11, solved_12
import project_05, project_06, project_07, project_08, project_10, project_11, project_12


Platform = collections.namedtuple("Platform", [
    "chip", "assemble", "parse_line", "translator", "parser", "compiler", "library"
])
"""Package of a chip and the assembler, translator, compiler, and library needed to run Jack programs on it."""




# def standard_compile(ast)

USER_PLATFORM = Platform(
    chip=project_05.Computer,
    assemble=project_06.assemble,
    parse_line=project_07.parse_line,
    translator=project_08.Translator,
    parser=project_10.parse_class,
    compiler=project_11.compile_class,
    # library=project_12.OS_CLASSES)
    library=solved_12._OS_CLASSES)  # HACK: because Output._drawChar is unresolved if the user's (partial) solution is used.
"""The default chip and associated tools, defined in the project_0x.py modules."""


BUNDLED_PLATFORM = Platform(
    chip=solved_05.Computer,
    assemble=solved_06.assemble,
    parse_line=solved_07.parse_line,
    translator=solved_07.Translator,
    parser=solved_10.parse_class,
    compiler=solved_11.compile_class,
    library=solved_12._OS_CLASSES)
"""The included chip and tools; for comparison with the user's solution."""
