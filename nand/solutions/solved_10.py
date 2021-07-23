import re

# integerConstant: a decimal number in the range 0 ... 32767
# stringConstant: '"', a sequence of Unicode characters, not including double quote or newline, '"'
# identifier: a sequence of letters, digits, and underscore ( '_' ) not starting with a digit.

def lex(string):
    # This is simple and requires no additional packages, but there are more elegant ways to get
    # this job done.

    keywords = set([
        "class", "constructor", "function",
        "method", "field", "static", "var", "int",
        "char", "boolean", "void", "true", "false",
        "null", "this", "let", "do", "if", "else",
        "while", "return",
    ])
    symbols = set("'{}()[].,;+-*/&|<>=~")

    tokens = []

    while string != "":
        m = re.match(r"^([0-9]+)", string)
        if m is not None:
            token_str = m.group(1)
            int_val = int(token_str)
            if not (0 <= int_val <= 32767):
                raise Exception(f"Integer constant out of range: {int_val}")
            tokens.append(("integerConstant", int_val))
            string = string[len(token_str):]
            continue

        m = re.match(r'^"([^"\n]*)"', string)
        if m is not None:
            token_str = m.group(1)
            tokens.append(("stringConstant", token_str))
            string = string[len(token_str)+2:]
            continue

        m = re.match(r"^([a-zA-Z_][a-zA-Z_0-9]*)", string)
        if m is not None:
            token_str = m.group(1)
            if token_str in keywords:
                tokens.append(("keyword", token_str))
            else:
                tokens.append(("identifier", token_str))
            string = string[len(token_str):]
            continue

        m = re.match(r"^(//[^\n]*)", string)
        if m is not None:
            string = string[len(m.group(1)):]
            continue

        m = re.match(r"^(/\*.*\*/)", string, re.DOTALL)
        if m is not None:
            string = string[len(m.group(1)):]
            continue

        if string[0] in symbols:
            tokens.append(("symbol", string[0]))
            string = string[1:]
            continue

        if string[0] in " \t\n":
            string = string[1:]
            continue

        raise Exception("Unexpected input: {string}")

    return tokens

#
# Simple parser combinators:
#

class ParseLocation:
    """Keep track of a list of tokens and the current position within it,
    with non-destructive update (by making a new instance each time the position
    advances, referring to the same underlying list.)
    """

    def __init__(self, tokens, pos=0):
        self.tokens = tokens
        self.pos = pos

    def current_token(self):
        if not self.at_eof():
            return self.tokens[self.pos]

    def at_eof(self):
        return self.pos == len(self.tokens)

    def advance(self):
        return ParseLocation(self.tokens, self.pos+1)

    def __str__(self):
        return f"ParseLocation: pos = {self.pos}; next token = {self.current_token()}"


class ParseFailure(Exception):
    def __init__(self, expected, loc):
        self.expected = expected
        self.loc = loc

    def __str__(self):
        return f"ParseFailure: expected {self.expected} at {self.loc}"


def parse(parser, token_list):
    """Apply a parser to a list of tokens, producing a single result if the parser
    succeeds and consumes the entire stream.

    The actual values in the stream can be anything.

    :param parser: A function which inspects the token stream. If it matches, return
        a tuple containing a result value and a new position in the stream. Otherwise,
        raise ParseFailure.
    """

    val, loc = parser(ParseLocation(token_list))
    # if not loc.at_eof():
    #     raise Exception("Parsing incomplete")
    # else:
    #     return val
    return val  # TEMP

def or_p(*parsers):
    """Apply each parser in turn to the same location, until one of them succeeds.
    Fail if they all fail.
    """
    def f(loc):
        for p in parsers:
            try:
                # print(f"try {p} at {loc}")
                return p(loc)
            except ParseFailure as x:
                # print(f"failed: {x}")
                pass
        raise ParseFailure(f"one of {parsers}", loc)

    return f

def seq_p(*parsers):
    """Apply each parser in turn to successive positions, returning a (flattened) list of results.
    Fail if any parser fails.
    """

    def f(loc):
        vals = []
        for p in parsers:
            val, loc = p(loc)
            if isinstance(val, list):
                vals.extend(val)
            else:
                vals.append(val)
        return (vals, loc)

    return f

def many_p(parser):
    """Apply a parser repeatedly as long as it succeeds, returning a list of results.
    Never fail."""

    def f(loc):
        vals = []
        while True:
            try:
                val, loc = parser(loc)
                vals.append(val)
            except ParseFailure:
                return vals, loc
    return f

def sep_by_p(parser, sep_parser):
    """Apply a parser repeatedly, also consuming separators in between values.
    Fail if a separator is not followed by a parsable entity.
    """

    def f(loc):
        vals = []

        try:
            val, loc = parser(loc)
            vals.append(val)
        except ParseFailure:
            # Early exit: no values is ok
            return vals, loc

        while True:
            try:
                val, loc = sep_parser(loc)
                vals.append(val)
            except ParseFailure:
                # No separator: we're done
                return vals, loc

            # Element required after a separator has been consumed:
            val, loc = parser(loc)
            vals.append(val)

    return f

def sep_by_1_p(parser, sep_parser):
    """Apply a parser repeatedly, also consuming separators in between values.
    Fail if a separator is not followed by a parsable entity.
    """

    def f(loc):
        vals = []

        val, loc = parser(loc)
        vals.append(val)

        while True:
            try:
                val, loc = sep_parser(loc)
                vals.append(val)
            except ParseFailure:
                # No separator: we're done
                return vals, loc

            # Element required after a separator has been consumed:
            val, loc = parser(loc)
            vals.append(val)

    return f

#
# Now, parsers for Jack:
#

# Wrap the top-level parser so the caller doesn't need to know about parser combinators
def parse_class(token_list):
    return parse(class_p(), token_list)

def class_p():
    return nest_p("class",
        seq_p(
            keyword_p("class"),
            className_p(),
            symbol_p("{"),
            subroutineDec_p(),
            symbol_p("}"),
        ))

def subroutineDec_p():
    return nest_p("subroutineDec",
        seq_p(
            keyword_p("function"),  # method/constructor
            keyword_p("void"),  # or any type
            subroutineName_p(),
            symbol_p("("),
            parameterList_p(),
            symbol_p(")"),
            subroutineBody_p(),
        ))

def parameterList_p():
    return nest_p("parameterList",
        sep_by_p(
            seq_p(
                type_p(),
                varName_p(),
            ),
            symbol_p(",")))

def subroutineBody_p():
    return nest_p("subroutineBody",
        seq_p(
            symbol_p("{"),
            many_p(varDec_p()),
            statements_p(),
            symbol_p("}"),
        ))

def varDec_p():
    return nest_p("varDec",
        seq_p(
            keyword_p("var"),
            type_p(),
            sep_by_1_p(varName_p(), symbol_p(",")),
            symbol_p(";"),
        ))

def statements_p():
    return nest_p("statements",
        many_p(statement_p()))

def statement_p():
    return or_p(
        letStatement_p(),
        # ifStatement_p(),
        whileStatement_p(),
        doStatement_p(),
        returnStatement_p(),
    )

def letStatement_p():
    return nest_p("letStatement",
        or_p(
            seq_p(
                keyword_p("let"),
                varName_p(),
                symbol_p("["),
                expression_p(),
                symbol_p("]"),
                symbol_p("="),
                expression_p(),
                symbol_p(";")
            ),
            seq_p(
                keyword_p("let"),
                varName_p(),
                symbol_p("="),
                expression_p(),
                symbol_p(";")
            ),
        ))

def whileStatement_p():
    return nest_p("whileStatement",
        seq_p(
            keyword_p("while"),
            symbol_p("("),
            expression_p(),
            symbol_p(")"),
            symbol_p("{"),
            lazy(statements_p),
            symbol_p("}"),
        ))

def doStatement_p():
    return nest_p("doStatement",
        seq_p(
            keyword_p("do"),
            subroutineCall_p(),
            symbol_p(";"),
        ))

def returnStatement_p():
    return nest_p("returnStatement",
        or_p(
            # TODO: optional_p
            seq_p(
                keyword_p("return"),
                symbol_p(";"),
            ),
            seq_p(
                keyword_p("return"),
                expression_p(),
                symbol_p(";"),
            ),
        ))

def expression_p():
    return nest_p("expression",
        sep_by_1_p(term_p(), op_p()))

def lazy(parser_f):
    """Defer constructing a parser to avoid recursion when composing parsers."""
    def f(loc):
        return parser_f()(loc)
    return f

def term_p():
    return nest_p("term",
        or_p(
            seq_p(integerConstant_p()),  # Tricky: seq_p just to embed in a list
            seq_p(stringConstant_p()),
            seq_p(keywordConstant_p()),
            subroutineCall_p(),  # disambiguate by trying this earlier
            # varName_p(),
            seq_p(
                varName_p(),
                symbol_p("["),
                lazy(expression_p),
                symbol_p("]"),
            ),
            seq_p(varName_p()),  # disambiguate by trying this later
            # subroutineCall_p(),
            seq_p(
                symbol_p("("),
                lazy(expression_p),
                symbol_p(")"),
            ),
            seq_p(
                unaryOp_p(),
                lazy(expression_p),
            ),
        ))

def subroutineCall_p():
    return or_p(
        # seq_p(
        #     subroutineName_p(),
        #     symbol_p("("),
        #     expressionList_p(),
        #     symbol_p(")"),
        # ),
        seq_p(
            or_p(
                className_p(),
                varName_p(),
            ),
            symbol_p("."),
            subroutineName_p(),
            symbol_p("("),
            expressionList_p(),
            symbol_p(")"),
        ),
    )

def expressionList_p():
    return nest_p("expressionList",
        sep_by_p(lazy(expression_p), symbol_p(",")))

def op_p():
    return or_p(*[symbol_p(op)
        for op in "+-*/&|<>="])

def unaryOp_p():
    return or_p(*[symbol_p(op)
        for op in "-~"])

def nest_p(name, parser):
    """Apply a parser, then wrap the result in a new tuple with the given name/type."""
    def f(loc):
        val, loc = parser(loc)
        return ((name, val), loc)
    return f


def type_p():
    return or_p(
        keyword_p("int"),
        keyword_p("char"),
        keyword_p("boolean"),
        className_p(),
    )

def className_p():
    return identifier_p()

def subroutineName_p():
    return identifier_p()

def varName_p():
    return identifier_p()

def keyword_p(kw):
    def f(loc):
        typ, val = loc.current_token()
        if typ == "keyword" and val == kw:
            return ((typ, val), loc.advance())
        else:
            raise ParseFailure(f"keyword: {kw}", loc)
    return f

def identifier_p():
    return any_p("identifier")

def symbol_p(sym):
    def f(loc):
        typ, val = loc.current_token()
        if typ == "symbol" and val == sym:
            return ((typ, val), loc.advance())
        else:
            raise ParseFailure(f"symbol: {repr(sym)}", loc)
    return f

def integerConstant_p():
    return any_p("integerConstant")

def stringConstant_p():
    return any_p("stringConstant")

def keywordConstant_p():
    return or_p(
        keyword_p("true"),
        keyword_p("false"),
        keyword_p("null"),
        keyword_p("this"),
    )

def any_p(token_type):
    def f(loc):
        typ, val = loc.current_token()
        if typ == token_type:
            return ((typ, val), loc.advance())
        else:
            raise ParseFailure(token_type, loc)
    return f
