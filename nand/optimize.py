"""Operations on ICs that make them more efficient to simulate, but aren't strictly required."""

import itertools

from nand.component import Nand, Const
from nand.integration import IC, Connection, root

def simplify(orig):
    """Construct a new chip which is logically identical to this one, but may be smaller
    and more efficient by the removal of certain recognized patterns. More effective after
    flatten().

    When a constant is the input of a Nand, that gate is replaced with either a constant or the
    other input: Nand(a, 0) = 1; Nand(a, 1) = Not(a)

    When a series of two Nands negate and then re-negate the same single value, the second Nand
    is always removed, and the first may be as well if it's otherwise unused.

    When more than one Nand has the same two inputs, each such set is replaced with a single
    Nand.
    """

    ic = orig.copy()

    def const_value(conn):
        if isinstance(conn.comp, Const):
            return conn.comp.value & (1 << conn.bit) != 0
        else:
            return None

    def rewrite(old_conn, new_conn):
        for t, f in list(ic.wires.items()):
            if f == old_conn:
                ic.wires[t] = new_conn

    done = False
    while not done:
        done = True
        for comp in set([c.comp for c in ic.wires.keys()] + [c.comp for c in ic.wires.values()]):
            if isinstance(comp, Nand):
                a_src = ic.wires[Connection(comp, "a", 0)]
                b_src = ic.wires[Connection(comp, "b", 0)]

                a_val = const_value(a_src)
                b_val = const_value(b_src)

                if a_val == False or b_val == False:
                    # Remove this Nand and rewrite its output as Const(1):
                    del ic.wires[Connection(comp, "a", 0)]
                    del ic.wires[Connection(comp, "b", 0)]
                    old_conn = Connection(comp, "out", 0)
                    new_conn = Connection(Const(1, 1), "out", 0)
                    rewrite(old_conn, new_conn)
                    done = False
                elif a_val == True and b_val == True:
                    # Remove this Nand and rewrite its output as Const(0):
                    del ic.wires[Connection(comp, "a", 0)]
                    del ic.wires[Connection(comp, "b", 0)]
                    old_conn = Connection(comp, "out", 0)
                    new_conn = Connection(Const(1, 0), "out", 0)
                    rewrite(old_conn, new_conn)
                    done = False
                elif a_val == True:
                    # Rewite to eliminate the Const:
                    ic.wires[Connection(comp, "a", 0)] = b_src
                    done = False
                elif b_val == True:
                    # Rewite to eliminate the Const:
                    ic.wires[Connection(comp, "b", 0)] = a_src
                    done = False
                elif a_src == b_src:
                    if isinstance(a_src.comp, Nand):
                        src_a_src = ic.wires[Connection(a_src.comp, "a", 0)]
                        src_b_src = ic.wires[Connection(a_src.comp, "b", 0)]
                        if src_a_src == src_b_src:
                            # Remove this Nand and rewrite its output as src's src:
                            del ic.wires[Connection(comp, "a", 0)]
                            del ic.wires[Connection(comp, "b", 0)]
                            old_conn = Connection(comp, "out", 0)
                            new_conn = src_a_src
                            rewrite(old_conn, new_conn)
                            # TODO: remove a_src.comp if not referenced?
                            done = False

        # Construct the sort function once, since it has to search the graph:
        by_component = ic._connections_sort_key()

        # Find and collapse sets of Nands with the same inputs:
        nands_by_input_pair = {}
        for conn in list(ic.wires):
            comp = conn.comp
            if isinstance(comp, Nand):
                t = tuple(sorted([
                    ic.wires[Connection(comp, "a", 0)],
                    ic.wires[Connection(comp, "b", 0)]
                ], key=by_component))
                nands_by_input_pair.setdefault(t, set()).add(comp)
        for _, nands_set in nands_by_input_pair.items():
            if len(nands_set) > 1:
                nands = list(nands_set)
                keep_nand = nands[0]
                for n in nands[1:]:
                    del ic.wires[Connection(n, "a", 0)]
                    del ic.wires[Connection(n, "b", 0)]
                    rewrite(Connection(n, "out", 0), Connection(keep_nand, "out", 0))
                    done = False

    return ic.flatten()  # HACK: a cheap way to remove dangling wires

def combinations(*values):
    """
    >>> combinations([[1, 2, 3], ['a', 'b']])
    [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b'), (3, 'a'), (3, 'b')]
    """
    if len(values) <= 1:
        return [tuple([x]) for x in values[0]]
    else:
        rest = combinations(*values[1:])
        return [
            tuple([x] + list(r))
            for x in values[0]
            for r in rest
        ]


def characterize(ic):
    """Construct a map containing every possible combination of inputs, with the resulting outputs.
    """

    import nand.vector
    nv = nand.vector.run(ic)

    input_pairs = combinations(*[[(n, v) for v in [False, True] ] for n in sorted(nv._vector.inputs)])

    def to_outputs(inputs):
        for n, v in inputs:
            nv._vector.set(n, v)
        return tuple([(n, nv._vector.get(n)) for n in sorted(nv._vector.outputs)])

    return {i: to_outputs(i) for i in input_pairs}


def generate_dags(inputs, outputs, max_size):
    """Generate _all_ possible ICs consisting of up to max_size Nands, with the given inputs
    (possibly not all connected) and outputs (definitely all connected).

    TODO: generate each unique IC only once, or at least closer to once.
    """

    iconns = [Connection(root, n, b) for (n, bits) in inputs.items() for b in range(bits)]
    oconns = [Connection(root, n, b) for (n, bits) in outputs.items() for b in range(bits)]

    def loop(size):
        if size == 0:
            yield [], []
        else:
            # TODO: yield all the smaller ones first? Would have to have them all in memory
            # (or else generate them twice)
            for nands, wires in loop(size-1):
                # yield nands, wires  # no need if loop below
                srcs = iconns + [Connection(n, "out", 0) for n in nands]
                nand = Nand()
                for a_src, b_src in combinations(srcs, srcs):
                    yield nands + [nand], wires + [(a_src, Connection(nand, "a", 0)), (b_src, Connection(nand, "b", 0))]


    for size in range(len(oconns), max_size+1):
        for nands, wires in loop(size):
            # DONE: probably ok to insist that every output has a unique source
            # possibly also insist that every input is used?
            # DONE: also rule out inputs wired directly to outputs?
            # maybe detect ICs that violate those properties up front?

            # srcs = iconns + [Connection(n, "out", 0) for n in nands]
            srcs = [Connection(n, "out", 0) for n in nands]  # no input wired directly to output
            for cs in combinations(*[srcs]*len(oconns)):
                if len(set(cs)) == len(cs):  # every output is mapped to a unique src
                    ic = IC("Gen", inputs, outputs)
                    ic.wires = { t: f for (f, t) in wires }
                    for f, t in zip(cs, oconns):
                        ic.wire(f, t)
                    flat = ic.flatten()  # remove unreachable Nands
                    # drop ICs where not all Nands were reachable; they would have been generated earlier
                    if len(flat.sorted_components()) == len(ic.sorted_components()):
                        yield flat


def super_optimize(ic):
    """Try to construct the _smallest_ equivalent chip, by enumerating every possible arrangment
    of Nands up to the same size, until one is found that returns the same result for all inputs.

    Works only on chips that can be expressed as DAGs of only Nands, with no references to `clock`.

    The number of potential circuits grows pretty appallingly:
    X = # of input bits
    Y = # of gates
    Z = # of output bits
    unique configurations = X^2 * (X + 1)^2 * ... * (X + Y - 1)^2  *  Y * (Y-1) * ... (Y - (Z-1))
                          = ((X + Y - 1)! / (X - 1)!)^2 * Y!/(Y-Z)!

    For example, HalfAdder has 2 inputs, 5 gates, and 2 outputs:
    (6!/1!)^2 * 5!/3! = ~10.4 million

    DMux4Way: 2, 13, 4 => (14!/1!)^2 * 13!/11! = 8e21. That's not good! ~260,000 years if we could check one per second.
    """

    print(f"original: {ic}")

    # first simplify, to establish a tight upper bound:
    simple = simplify(ic)

    upper_bound = len(simple.sorted_components())

    print(f"simple: {upper_bound} gates\n{simple}")

    expected_output = characterize(simple)

    print(f"expected: {expected_output}")

    import nand.vector
    def matches_expected(gen_ic):
        # This seems like it would be a _lot_ faster than `characterize(gen_ic) == expected_output`,
        # but it's not noticeable. I guess the time is elsewhere.
        # Profiling indicates it's mostly in synthesize.
        nv = nand.vector.run(gen_ic, optimize=False)
        for ins, outs in expected_output.items():
            for n, v in ins:
                nv._vector.set(n, v)
            for n, v in outs:
                if nv._vector.get(n) != v:
                    return False
        return True

    no_match_count = 0
    for gen_ic in generate_dags(ic.inputs(), ic.outputs(), upper_bound):
        if matches_expected(gen_ic):
            print(f"Matched after {no_match_count:,d} tries:\n{gen_ic}")
            return gen_ic
        else:
            no_match_count += 1
            if no_match_count % 10000 == 0:
                print(f"Failed #{no_match_count:,d}:\n{gen_ic}")
    raise Exception("No matches generated")
