from nand.codegen import translate
from nand.integration import IC, Connection, root
from nand.syntax import Nand, _constr
# from project_01 import Not

    
def test_Nand():
    ic = _constr(Nand)

    klass = translate(ic)
    nand = klass()

    assert nand.out == True

    nand.a = True
    assert nand.out == True

    nand.b = True
    assert nand.out == False

    nand.a = False
    assert nand.out == True
