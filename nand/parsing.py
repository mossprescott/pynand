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
package (based on Haskell's famous [similarly-named library](https://hackage.haskell.org/package/parsec)).

Or just google "Parser Combinators".


A few examples to get started:

>>> aP = TokenP("a", 1)
>>> bP = TokenP("b", 2)
>>> aP.parse("a")
1
>>> bP.parse("b")
2


These parsers only match these *exact* strings. If you apply them to anything else, a ParseFailure
is raised:

>>> aP.parse("table")
Traceback (most recent call last):
...
nand.parsing.ParseFailure: Expected token 'a' at location 0; next token: 't'


You can match one of a set of alternatives by combining parsers with the '|' operator:

>>> a_or_bP = aP | bP
>>> a_or_bP.parse("a")
1
>>> a_or_bP.parse("b")
2
>>> ManyP(a_or_bP).parse("abba")
[1, 2, 2, 1]


Similarly, you can match a sequence of tokens using '&'. The results get wrapped in a tuple:

>>> (aP & bP).parse("ab")
(1, 2)


This gets unwieldy when you string together a longer sequence (a common need), so you can use
`.mapConstr()` to unpack them and apply whatever function you like:

>>> def three_things(x, y, z):
...     return [x, y, z]
>>> (aP & bP & bP).mapConstr(three_things).parse("abb")
[1, 2, 2]


You can also use functions to modify the values you get back, or to control what can match in
arbitrary ways:

>>> a_or_bP.map(str).parse("b")
'2'
>>> AnyP().filter(str.isupper).parse("A")
'A'


And there's more:

>>> (OptionalP(aP) & bP).parse("b")
(None, 2)

>>> BracketP(
...     TokenP("[", "ignored"),
...     aP,
...     TokenP("]", "who cares?")
... ).parse("[a]")
1

>>> SepByP(a_or_bP, TokenP(",", None)).parse("a,b,b,a")
[1, 2, 2, 1]


If you can't define your parser because it needs to refer to itself, DeferP can save the day.
Here's a tricky parser that also shows how you can use transformation of the parsed values
to do arbitrary computation:

>>> depthP = DeferP("depth")
>>> depthP.set(
...     BracketP(TokenP("[", None), depthP, TokenP("]", None))
...         .map(lambda x: x+1)
...     | a_or_bP
...         .const(0))
>>> depthP.parse("[[a]]")
2
"""

from typing import Callable, Generic, Sequence, Optional, Tuple, Type, TypeVar, final


T = TypeVar("T", covariant=True)
"""The type of each token, e.g. `str` or `Tuple[str, str]`, but any type can be used."""

V = TypeVar("V", covariant=True)
"""The type of the value produced by a parser."""

W = TypeVar("W")
"""An alternative result type (used when transforming the value produced by a parser.)"""


class Parser(Generic[T, V]):
    """Base class for parsers."""

    # TODO: this is bogus. You should be able to define a "parser" as just a plain function
    # if you want to. But then you need this function to be defined separately. And since it's
    # final there's no real reason for it to be in this class.
    @final
    def parse(self, tokens: Sequence[T]) -> V:
        """Apply this parser to a list of tokens. If it matches the entire stream, a result is returned.
        If it doesn't match, or matches only a prefix, a ParseFailure is raised.

        This method can be used on any parser to parse a fragment of code. It never needs to be overridden.
        """

        val, loc = self.__call__(ParseLocation(tokens, pos=0))
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
    def describe(self, label: str) -> "Parser[T, V]":
        """Supply a human-readable description of what the parser is trying to match, to be
        included in error messages.

        >>> a_or_b = TokenP("a", None) | TokenP("b", None)

        >>> a_or_b.parse("c")
        Traceback (most recent call last):
        ...
        nand.parsing.ParseFailure: Expected one of token 'a', token 'b' at location 0; next token: 'c'

        >>> a_or_b.describe("one of the first two letters of the alphabet").parse("c")
        Traceback (most recent call last):
        ...
        nand.parsing.ParseFailure: Expected one of the first two letters of the alphabet at location 0; next token: 'c'
        """

        class LabeledP(Parser[T, V]):
            def __init__(self, parser, label):
                self.parser = parser
                self.label = label
            def __call__(self, loc: "ParseLocation") -> Tuple[V, "ParseLocation"]:
                try:
                    return self.parser(loc)
                except ParseFailure:
                    raise ParseFailure(label, loc)
            def __str__(self):
                return self.label
        return LabeledP(self, label)

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


    @final
    def mapConstr(self, constr: Callable[..., W], indexes: Optional[Sequence[int]] = None) -> "Parser[T, W]":
        """Apply a constructor (actually, any function) to the result, after flattening the tuple
        constructed by successive `&` or Seq2P compositions.
        If `indexes` is present, it gives the locations of parameters to be extracted from the result;
        otherwise, all results are used.
        The arity of the constructor must match the number of results available (or the number of indexes.)

        Note: if one of the values being collected here can ever be an ordinary tuple, chaos ensues.
        """

        def flatten(t):
            # Note: *not* using isinstance(t, tuple), because NamedTuples are tuple!
            if type(t) == tuple:
                return [d for c in t for d in flatten(c)]
            else:
                return [t]

        def munge(lft):
            vals = flatten(lft)
            # print(constr)
            # for v in vals: print(v)
            if indexes is not None:
                args = [vals[i] for i in indexes]
            else:
                args = vals
            return constr(*args)

        return MapP(self, munge)


    #
    # And now, for some outrageous syntax sugar:
    #

    # Note: the inferred type here is worse than OrP's in some cases (because it's based only on the left parser?)
    @final
    def __or__(self, rhs: "Parser[T, V]") -> "Parser[T, V]":
        """Match one or the other; see OrP."""

        # Collapse chained OrP's for better parse failure messages:
        if isinstance(self, OrP):
            return OrP(*(list(self.parsers) + [rhs]))
        else:
            return OrP(self, rhs)

    @final
    def __and__(self, rhs: "Parser[T, W]") -> "Parser[T, Tuple[V, W]]":
        """Match one, then the other; see Seq2P."""
        return Seq2P(self, rhs)

    @final
    def __lshift__(self, rhs: "Parser[T, W]") -> "Parser[T, W]":
        """Apply two parsers and ignore the result on the left.

        Best used sparingly.

        >>> p = TokenP("a", 1) << TokenP("b", 2)
        >>> p.parse("ab")
        2
        """
        return Seq2P(self, rhs).map(lambda t: t[1])

    @final
    def __rshift__(self, rhs: "Parser[T, W]") -> "Parser[T, V]":
        """Apply two parsers and ignore the result on the right.

        Best used sparingly.

        >>> p = TokenP("a", 1) >> TokenP("b", 2)
        >>> p.parse("ab")
        1
        """
        return Seq2P(self, rhs).map(lambda t: t[0])


class ParseLocation(Generic[T]):
    """Keep track of a list of tokens and the current position within it,
    with non-destructive update (by making a new instance each time the position
    advances, referring to the same underlying list.)
    """

    def __init__(self, tokens: Sequence[T], pos):
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
        return f"ParseLocation(pos: {self.pos}; next token: {'<eof>' if self.at_eof() else repr(self.current_token())})"


class ParseFailure(Exception, Generic[T]):
    def __init__(self, expected, loc: ParseLocation[T]):
        self.expected = expected
        self.loc = loc

    def __str__(self):
        return f"Expected {self.expected} at location {self.loc.pos}; next token: {'<eof>' if self.loc.at_eof() else repr(self.loc.current_token())}"


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
    nand.parsing.ParseFailure: Expected token 'a' at location 0; next token: 'q'

    >>> one_a.parse("abc")
    Traceback (most recent call last):
    ...
    nand.parsing.ParseFailure: Expected eof at location 1; next token: 'b'
    """

    def __init__(self, token: T, value: V):
        self.token = token
        self.value = value

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        if loc.current_token() == self.token:
            return self.value, loc.advance()
        else:
            raise ParseFailure(str(self), loc)

    def __str__(self):
        return f"token {repr(self.token)}"


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
            except ParseFailure as x:
                # If the parser consumed any input and *then* failed, report that failure.
                # If not, then we're at the end of the list and just return it.
                if x.loc == loc:
                    return vals, loc
                else:
                    raise x


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


class OrP(Parser[T, V]):
    """Try a series of parsers until one matches, and return its result.

    >>> a_or_b = OrP(TokenP("a", "Nice!"), TokenP("b", "Great!"))

    >>> a_or_b.parse("a")
    'Nice!'


    Note: the '|' operator is another way to construct the same parser:

    >>> a_or_b = TokenP("a", "Nice!") | TokenP("b", "Great!")
    >>> a_or_b.parse("b")
    'Great!'


    If one of the alternatives makes some progress before failing, it's failure will
    be the one you see:

    >>> a_and_b = TokenP("a", None) & TokenP("b", None)
    >>> c_and_d = TokenP("c", None) & TokenP("d", None)
    >>> (a_and_b | c_and_d).parse("af")
    Traceback (most recent call last):
    ...
    nand.parsing.ParseFailure: Expected token 'b' at location 1; next token: 'f'
    """

    def __init__(self, *parsers: Parser[T, V]):
        self.parsers = parsers

    def __call__(self, loc) -> Tuple[V, ParseLocation[T]]:
        failures = []
        for p in self.parsers:
            try:
                return p(loc)
            except ParseFailure as x:
                failures.append(x)
        # Tricky: choose the "most interesting" failure to report — the one that
        # got the farthest and therefore has the most specific problem to report,
        # most of the time.
        furthest = sorted(failures, key=lambda pf: -pf.loc.pos)[0]
        if furthest.loc.pos > loc.pos:
            raise furthest
        else:
            # No parser made any progress, so summarize them all
            raise ParseFailure(f"one of {', '.join(str(p) for p in self.parsers)}", loc)


V1 = TypeVar("V1", covariant=True)
V2 = TypeVar("V2", covariant=True)

class Seq2P(Parser[T, Tuple[V1, V2]]):
    """Apply two parsers and assemble their results into a tuple.

    >>> a_and_b = Seq2P(TokenP("a", "Nice!"), TokenP("b", "Great!"))

    >>> a_and_b.parse("ab")
    ('Nice!', 'Great!')

    Note: the '&' operator is another way to construct the same parser:

    >>> a_and_b = TokenP("a", "Nice!") & TokenP("b", "Great!")
    >>> a_and_b.parse("ab")
    ('Nice!', 'Great!')
    """

    def __init__(self, first: Parser[T, V1], second: Parser[T, V2]):
        self.first = first
        self.second = second

    def __call__(self, loc) -> Tuple[Tuple[V1, V2], ParseLocation[T]]:
        # TODO: if the first partially succeeds (that is, parses some stuff, then tries to parse
        # more but doesn't match), and then the second also fails, we want to make an informed
        # choice which failure to report.
        v1, loc = self.first(loc)
        v2, loc = self.second(loc)
        return (v1, v2), loc


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

    # Note: you end up having to annotate the type whenever you construct one of these, but fancy
    # tricks don't seem to work anyway because the types involved are recursive and hurt mypy's
    # brain so I gave up.
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
