"""Operations on ICs that make them more efficient to simulate, but aren't strictly required."""

from nand.component import Nand, Const
from nand.integration import IC, Connection

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
        by_component = ic._connections_sort_key(ic.wires)

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
