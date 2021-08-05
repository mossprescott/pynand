
ARRAY_NEW = """
    /** Constructs a new Array of the given size. */
    function Array new(int size) {
        if (size < 0) {
            do Sys.error(2);
        }
        return Memory.alloc(size);
    }
"""


ARRAY_DISPOSE = """
    /** Disposes this array. */
    method void dispose() {
        do Memory.deAlloc(this);
        return;
    }
"""


ARRAY_CLASS = f"""
class Array {{
{ARRAY_NEW}
{ARRAY_DISPOSE}
}}
"""