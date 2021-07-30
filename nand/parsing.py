"""Simple parser combinators; handy for implementing project 10.

This is intended as a self-contained demonstration of the "parser combinator" approach,
but as such it has some significant limitations:
- parsers can only inspect the single token at the current location
- no control over back-tracking; once a token is consumed on a path, there's no recovery
- it might not perform well for large inputs, depending on the parser you construct

Fortunately, the Jack language has been carefully designed so that a very simple parser can
handle it, even a parser built using this very weak foundation.

These parsers also produce fairly incomprehensible errors when they fail, which is more of
a real problem when you're trying to debug a large parser.

Naming Convention:

To avoid confusion while keeping names compact, parser class names always end in "P". When they
produce a specific type, they're often named for it, as in `MyThingP`.

Type annotations:

Unlike the rest of this repo, this module is heavily annotated to indicate expected types.
They hopefully make this fairly abstract code easier to follow, by indicating the result
produced by each combinator. However, some of the types aren't precise because a) Python
type-checkers don't handle recursive types and b) I haven't figured out how variance is
supposed to work. Even so, mypy is helpful for debugging complex Parser composition.

For the curious:

A possibly more robust implementation of a similar idea is the [parsec](https://pypi.org/project/parsec/)
package (based on Haskell's famous (simlarly-named library)[https://hackage.haskell.org/package/parsec].

Or just google "Parser Combinators".
"""

from typing import Callable, Generic, Sequence, Optional, Tuple, TypeVar, final


T = TypeVar("T", covariant=True)
"""The type of each token, e.g. `str` or `Tuple[str, str]`, but any type can be used."""

V = TypeVar("V", covariant=True)
"""The type of the value produced by a parser."""

W = TypeVar("W")
"""An alternative result type (used when transforming the value produced by a parser.)"""


class Parser(Generic[T, V]):
    """Base class for parsers."""

    # TODO: this is bogus. You should be able to define a "parser" as just a plain function
    # if you want to. But the you need this function to be defined separately. And since it's
    # final there's no real reason for it to be in this class.
    @final
    def parse(self, tokens: Sequence[T]) -> V:
        """Apply this parser to a list of tokens. If it matches the entire stream, a result is returned.
        If it doesn't match, or matches only a prefix, a ParseFailure is raised.

        This method can be used on any parser to parse a fragment of code. It never needs to be overridden.
        """

        val, loc = self.__call__(ParseLocation(tokens))
        if loc.at_eof():
            return val
        else:
            raise ParseFailure("eof", loc)

    def __call__(self, loc: "ParseLocation") -> Tuple[V, "ParseLocation"]:
        """Attempt to parse zero or more tokens starting from the given location.

        If successful, return a tuple of (value, new location). Otherwise, raise ParseFailure.

        This method is overridden in each Parser subclass.
        """

        raise NotImplementedError()

    @final
    def map(self, transform: Callable[[V], W]) -> "Parser[T, W]":
        """When the parser succeeds, transform the value that's produced."""
        return MapP(self, transform)

    @final
    def const(self, value: W) -> "Parser[T, W]":
        """When the parser succeeds, substitute a new, constant value."""
        return MapP(self, lambda _: value)  # type: ignore   # (not actually using the parameter here)

    @final
    def filter(self, predicate: Callable[[V], bool]) -> "Parser[T, V]":
        return FilterP(self, predicate)


class ParseLocation(Generic[T]):
    """Keep track of a list of tokens and the current position within it,
    with non-destructive update (by making a new instance each time the position
    advances, referring to the same underlying list.)
    """

    def __init__(self, tokens: Sequence[T], pos=0):
        self.tokens = tokens
        self.pos = pos

    def current_token(self) -> T:
        if self.at_eof():
            raise ParseFailure("a token", self)
        return self.tokens[self.pos]

    def at_eof(self) -> bool:
        return self.pos == len(self.tokens)

    def advance(self) -> "ParseLocation":
        return ParseLocation(self.tokens, self.pos+1)

    def __str__(self):
        return f"ParseLocation(pos: {self.pos}; next token: {repr(self.current_token())})"


class ParseFailure(Exception, Generic[T]):
    def __init__(self, expected, loc: ParseLocation[T]):
        self.expected = expected
        self.loc = loc

    def __str__(self):
        return f"ParseFailure: expected {self.expected} at {self.loc}"


#
# Combinators:
#

class AnyP(Parser[T, T]):
    """Match literally *any* single token, and just produce the token itself as a value.

    Mostly useful when you want to to apply filtering/mapping afterward.
    """

    def __call__(self, loc) -> Tuple[T, ParseLocation[T]]:
        return loc.current_token(), loc.advance()


class TokenP(Parser[T, V]):
    """Match a specific token, returning a constant value.

    Note: this is equivalent to `AnyP().filter(lambda t: t == token).const(value)`, but it produces
    a more informative error message when it fails.

    Note: common result values are either the token itself or `None`; you know what value you're
    looking for, so there's often no need to produce any value when you recognize it.

    >>> one_a = TokenP("a", "Success!")

    >>> one_a.parse("a")
    'Success!'

    >>> one_a.parse("q")
    Traceback (most recent call last):
    ...
    nand.parsing.ParseFailure: ParseFailure: expected 'a' at ParseLocation(pos: 0; next token: 'q')

    >>> one_a.parse("abc")
    Traceback (most recent call last):
    ...
    nand.parsing.ParseFailure: ParseFailure: expected eof at ParseLocation(pos: 1; next token: 'b')
    """

    def __init__(self, token: T, value: V):
        self.token = token
        self.value = value

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        if loc.current_token() == self.token:
            return self.value, loc.advance()
        else:
            raise ParseFailure(repr(self.token), loc)


class OptionalP(Parser[T, Optional[V]]):
    """Try a parser; if it fails, consume no tokens and return None.
    """

    def __init__(self, parser: Parser[T, V]):
        self.parser = parser

    def __call__(self, loc) -> Tuple[Optional[V], ParseLocation[T]]:
        try:
            return self.parser(loc)
        except ParseFailure:
            return None, loc


class ManyP(Parser[T, Sequence[V]]):
    """Apply a parser repeatedly until it fails, producing a list of values."""

    def __init__(self, parser: Parser[T, V]):
        self.parser = parser

    def __call__(self, loc) -> Tuple[Sequence[V], ParseLocation[T]]:
        vals = []
        while True:
            try:
                val, loc = self.parser(loc)
                vals.append(val)
            except ParseFailure:
                return vals, loc


class SepByP(Parser[T, Sequence[V]]):
    """Apply a parser repeatedly until it fails, matching (and discarding) a separator between each, and
    producing a list of values.
    """

    def __init__(self, parser: Parser[T, V], separator: Parser[T, W], one_or_more=False):
        self.parser = parser
        self.separator = separator
        self.one_or_more = one_or_more

    def __call__(self, loc) -> Tuple[Sequence[V], ParseLocation[T]]:
        vals = []

        try:
            val, loc = self.parser(loc)
            vals.append(val)
        except ParseFailure as x:
            if self.one_or_more:
                raise x
            else:
                return [], loc

        while True:
            try:
                _, loc = self.separator(loc)
            except:
                # No separator means we're done
                return vals, loc

            # Already parsed a separator, so now need a value:
            val, loc = self.parser(loc)
            vals.append(val)


# TODO: figure out how to make the sub-parsers properly (co)variant.
class OrP(Parser[T, V]):
    """Try a series of parsers until one matches, and return its result.

    >>> one_a = OrP(TokenP("a", "Nice!"), TokenP("b", "Great!"))

    >>> one_a.parse("a")
    'Nice!'

    >>> one_a.parse("b")
    'Great!'
    """

    def __init__(self, *parsers: Parser[T, V]):
        self.parsers = parsers

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        for p in self.parsers:
            try:
                return p(loc)
            except ParseFailure:
                pass
        raise ParseFailure(f"one of {self.parsers}", loc)


# TODO: a specific type is never going to work here if you want to use this in a general way;
# each parser is going to produce a different type of value and that's just not a Sequence.
# Probably need to just have Seq2P (and so on) and properly type the result as a Tuple.
class SeqP(Parser[T, Sequence[V]]):
    """Apply a series of parsers and return a list with the result from each one.

    >>> one_a = SeqP(TokenP("a", "Nice!"), TokenP("b", "Great!"))

    >>> one_a.parse("ab")
    ['Nice!', 'Great!']
    """

    def __init__(self, *parsers: Parser[T, V]):
        self.parsers = parsers

    def __call__(self, loc) -> Tuple[Sequence[V], ParseLocation[T]]:
        vals = []
        for p in self.parsers:
            val, loc = p(loc)
            vals.append(val)
        return vals, loc


class BracketP(Parser[T, V]):
    """Apply a parser, ignoring matching tokens to the left and right.

    >>> SurroundedP = BracketP(TokenP("(", 42), TokenP("a", "Got it!"), TokenP(")", True))

    >>> SurroundedP.parse("(a)")
    'Got it!'
    """

    # TODO: fix these types; no need to constrain left and right at all, but "None" is
    # sometimes used, because it forces you to be explicit about not using those values.
    def __init__(self, left: Parser[T, object], parser: Parser[T, V], right: Parser[T, object]):
        self.left = left
        self.parser = parser
        self.right = right

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        _, loc = self.left(loc)
        val, loc = self.parser(loc)
        _, loc = self.right(loc)
        return val, loc


class MapP(Parser[T, V]):
    """Apply a parser, then transform the value it produced.

    Note: the transform function always applies to a single value (possible a list) produced
    by the original parser. That's not always convenient, but it's easy to understand.
    """

    def __init__(self, parser: Parser[T, W], transform: Callable[[W], V]):
        self.parser = parser
        self.transform = transform

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        val, loc = self.parser(loc)
        return self.transform(val), loc


class FilterP(Parser[T, V]):
    """Apply a parser, then check the value it produced against a predicate and fail if it's not accepted.

    Note: the predicate function always applies to a single value (possible a list) produced
    by the original parser. That's not always convenient, but it's easy to understand.
    """

    def __init__(self, parser: Parser[T, V], predicate: Callable[[V], bool]):
        self.parser = parser
        self.predicate = predicate

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        val, loc1 = self.parser(loc)
        if self.predicate(val):
            return val, loc1
        else:
            # Note: the failure needs to refer to the original location, not the new location
            # after consuming some tokens
            raise ParseFailure("predicate not satisfied", loc)


class DeferP(Parser[T, V]):
    """A placeholder for a parser which will be constructed later, to resolve circular dependencies
    when recursive grammars are defined.

    If the actual parser hasn't been defined yet when this parser is applied, it fails with a distinct
    error.
    """

    def __init__(self, name: str):
        self.name = name
        self.parser = None  # type: Optional[Parser[T, V]]

    def set(self, parser: Parser[T, V]):
        self.parser = parser

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        if self.parser is not None:
            return self.parser(loc)
        else:
            raise UnresolvedCircularityError(self.name)

class UnresolvedCircularityError(Exception):
    def __init__(self, name):
        Exception.__init__(self, f"Parser {repr(name)} was never defined")
