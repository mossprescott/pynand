from Nand import *


def mkNot(inputs, outputs):
    in_ = inputs.in_
    n = Nand(a=in_, b=in_)
    outputs.out = n.out

    # Or you can run it all together:
    outputs.out = Nand(a=inputs.in_, b=inputs.in_).out

Not = Component(mkNot)

# possible alt:
# class Not(Component3):
#     def construct(self):
#         n = Nand(a=self.in_, b=self.in_)
#         self.out = n.out


def mkOr(inputs, outputs):
    a = inputs.a
    b = inputs.b
    outputs.out = ___

Or = Component(mkOr)


def mkAnd(inputs, outputs):
    a = inputs.a
    b = inputs.b
    outputs.out = ___

And = Component(mkAnd)


def mkXor(inputs, outputs):
    # When there's only one output from a component, you can extract it immediately:
    a = inputs.a
    b = inputs.b
    outputs.out = ___

Xor = Component(mkXor)


def mkMux(inputs, outputs):
    a = inputs.a
    b = inputs.b
    sel = inputs.sel
    outputs.out = ___

Mux = Component(mkMux)


def mkDMux(inputs, outputs):
    in_ = inputs.in_
    sel = inputs.sel

    outputs.a = ___
    outputs.b = ___

DMux = Component(mkDMux)


# TODO: these require multi-bit inputs/outputs:
# DMux4Way
# DMux8Way
# Not16
# And16
# Mux16
# Mux4Way16
# Mux8Way16
