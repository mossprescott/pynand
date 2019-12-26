from nand_new.syntax import Nand, build

def test_simple():
    def mkNot(inputs, outputs):
        outputs.out = Nand(a=inputs.in_, b=inputs.in_).out
    Not = build(mkNot)
    
    n = Not.run()
    
    assert n.out == True
    
    n.in_ = True
    assert n.out == False
