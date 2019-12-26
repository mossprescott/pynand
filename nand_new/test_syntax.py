from nand_new.syntax import Nand, build, run

def test_simple():
    def mkNot(inputs, outputs):
        outputs.out = Nand(a=inputs.in_, b=inputs.in_).out
    Not = build(mkNot)
    
    chip = Not.constr()
    
    assert chip.inputs() == {"in_": 1}
    assert chip.outputs() == {"out": 1}
    
    assert len(chip.wires) == 3  # TODO: how to assert on the structure?
    
    assert run(Not, in_=False).out == True
    assert run(Not, in_=True).out == False