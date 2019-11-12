from random import shuffle

from nand.component import sorted_nodes


class Node:
    """Trivial node type providing refs() and inst, as required by sorted_nodes."""
    
    def __init__(self, name, *rs):
        self.name = name
        self.rs = set(rs)
        self.inst = self
    
    def refs(self):
        lst = list(self.rs)
        shuffle(lst)
        return lst
        
    def __repr__(self):
        return self.name
        
def test_simple():
    a = Node('a')
    b = Node('b', a)
    c = Node('c', b)
    
    assert sorted_nodes(c) == [a, b, c]
    
    
def test_converging():
    a = Node('a', )
    b = Node('b', a)
    c = Node('c', a, b)
    
    assert sorted_nodes(c) == [a, b, c], "a should precede b, even if c also depends directly on a"

    
def test_circular():
    a = Node('a')
    b = Node('b', a)
    c = Node('c', b)
    a.rs.add(c)
    
    assert sorted_nodes(c) == [a, b, c], "a is first because we started at c"


# This isn't quite right, because:
# 1) The dependencies on Mux_0 and Mux_8 are missing 
# 2) Would need to account for forward (back) refs in the assertion also
# def test_complex():
#     # based on the failing (flaky) test for Bit:
#     # inst: Not_1; {'in_': Ref(root.load)}
#     # inst: Not_9; {'in_': Ref(root.clock)}
#     # inst: Mux_0; {'a': Ref(Forward(DFF_6).out), 'b': Ref(root.in_), 'sel': Ref(root.load)}
#     # inst: Mux_8; {'a': Ref(Forward(Mux_8).out), 'b': Ref(Mux_0.out), 'sel': Ref(root.clock)}
#     # inst: Not_18; {'in_': Ref(Not_14.out)}
#     # inst: Not_14; {'in_': Ref(root.clock)}
#     # inst: Latch_7; {'in_': Ref(Mux_0.out), 'enable': Ref(root.clock)}
#     # inst: Mux_17; {'a': Ref(Forward(Mux_17).out), 'b': Ref(Latch_7.out), 'sel': Ref(Not_14.out)}
#     # inst: Latch_16; {'in_': Ref(Latch_7.out), 'enable': Ref(Not_14.out)}
#     # inst: DFF_6; {'in_': Ref(Mux_0.out), 'clock': Ref(root.clock)}
#     a = Node('Not_1')
#     b = Node('Mux_0')
#     c = Node('Not_9')
#     d = Node('Mux_8', b); d.rs.add(d)
#     e = Node('Latch_7', b)
#     f = Node('Not_14')
#     g = Node('Not_18', f)
#     h = Node('Mux_17', e); h.rs.add(h)
#     i = Node('Latch_16', e, f)
#     j = Node('DFF_6', b)
#
#     # delayed:
#     b.rs.add(j)
#
#     s = sorted_nodes(b)
#     for n in (a, b, c, d, e, f, g, h, i, j):
#         for r in n.refs():
#             assert s.index(r) <= s.index(n)
