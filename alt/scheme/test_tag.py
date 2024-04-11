#! /usr/bin/env pytest

import pytest
from hypothesis import given, strategies as st

from alt import big
from alt.scheme.tag import *


@given(st.integers(-16384, 16383))
def test_int(x):
    """Every 15-bit integer can be encoded and decoded."""
    tagged = tag_int(x)

    assert is_int(tagged)

    assert untag_int(tagged) == x


@given(st.integers(big.ROM_BASE, big.HEAP_TOP).filter(lambda x: x % 3 == 0))
def test_rib(addr):
    """Every valid rib address can be encoded and decoded."""
    tagged = tag_rib(addr)

    assert is_rib(tagged)

    assert untag_rib(tagged) == addr


@given(st.integers(-32768, 32767))
def test_distinct(x):
    """Every 16-bit value has exactly one possible interpretation."""
    assert is_int(x) + is_slot(x) + is_rib(x) == 1