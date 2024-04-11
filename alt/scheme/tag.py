"""Encoding for integer, slot, and rib pointer values."""

from alt import big

# FIXME: use the rvm's actual/current value
MAX_SLOT = big.ROM_BASE/3


def is_int(obj):
    return obj & 0x8000 != 0

def is_slot(obj):
    return 0 <= obj <= MAX_SLOT

def is_rib(obj):
    return not is_int(obj) and not is_slot(obj)


def tag_int(x):
    return x | 0x8000

def tag_rib(addr):
    assert addr % 3 == 0
    return addr//3


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
    return 3*obj
