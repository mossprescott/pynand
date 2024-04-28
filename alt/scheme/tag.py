"""Encoding for integer, slot, and rib pointer values."""

from alt import big
from nand.vector import extend_sign, unsigned


# FIXME: use the rvm's actual/current value
MAX_SLOT = big.ROM_BASE/3


def is_int(obj):
    return not is_rib(obj)

def is_rib(obj):
    # TODO: test addr is in range?
    return extend_sign(obj) < 0

# No need now that ribs are always < 0
# def is_slot(obj):
#     return 0 <= obj <= MAX_SLOT

def tag_int(x):
    return x & 0x7FFF

def tag_rib(addr):
    addr = unsigned(addr)
    assert addr % 3 == 0
    obj = extend_sign(-(addr//3))
    assert (-32768 <= obj < 0) or (MAX_SLOT < obj <= 32767)
    return obj


def untag_int(obj):
    """See vector.extend_sign."""

    assert is_int(obj)
    x = obj & 0x7fff
    if x & 0x4000 != 0:
        return (-1 & ~0x7fff) | x
    else:
        return x

def untag_rib(obj):
    assert is_rib(obj)
    return extend_sign(-3*extend_sign(obj))
