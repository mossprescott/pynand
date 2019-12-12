from project_05 import *

def test_memory_system():
    mem = run(MemorySystem)
    
    # set RAM[0] = -1
    mem.in_ = -1
    mem.load = 1
    mem.address = 0
    mem.tick(); mem.tock()

    # RAM[0] holds value
    mem.in_ = 9999
    mem.load = 0
    mem.tick(); mem.tock()
    assert mem.out == -1
    
    # Did not also write to upper RAM or Screen
    mem.address = 0x2000
    assert mem.out == 0
    mem.address = 0x4000
    assert mem.out == 0

    # Set RAM[2000] = 2222
    mem.in_ = 2222
    mem.load = 1
    mem.address = 0x2000
    mem.tick(); mem.tock()
    assert mem.out == 2222
    
    # RAM[2000] holds value
    mem.in_ = 9999
    mem.load = 0
    mem.tick(); mem.tock()
    assert mem.out == 2222
    
    # Did not also write to lower RAM or Screen
    mem.address = 0
    assert mem.out == -1
    mem.address = 0x4000
    assert mem.out == 0

    # Low order address bits connected
    # (note: not actually testing anything in this system?)
    mem.address = 0x0001; assert mem.out == 0
    mem.address = 0x0002; assert mem.out == 0
    mem.address = 0x0004; assert mem.out == 0
    mem.address = 0x0008; assert mem.out == 0
    mem.address = 0x0010; assert mem.out == 0
    mem.address = 0x0020; assert mem.out == 0
    mem.address = 0x0040; assert mem.out == 0
    mem.address = 0x0080; assert mem.out == 0
    mem.address = 0x0100; assert mem.out == 0
    mem.address = 0x0200; assert mem.out == 0
    mem.address = 0x0400; assert mem.out == 0
    mem.address = 0x0800; assert mem.out == 0
    mem.address = 0x1000; assert mem.out == 0
    mem.address = 0x2000; assert mem.out == 2222

    # RAM[0x1234] = 1234
    mem.address = 0x1234
    mem.in_ = 1234
    mem.load = 1
    mem.tick(); mem.tock()
    assert mem.out == 1234

    # Did not also write to lower RAM or Screen
    mem.address = 0x2234
    assert mem.out == 0
    mem.address = 0x6234
    assert mem.out == 0

    # RAM[0x2345] = 2345
    mem.address = 0x2345
    mem.in_ = 2345
    mem.load = 1
    mem.tick(); mem.tock()
    assert mem.out == 2345

    # Did not also write to lower RAM or Screen
    mem.address = 0x0345
    assert mem.out == 0
    mem.address = 0x4345
    assert mem.out == 0


    ### Keyboard test
    
    mem.address = 0x6000
    # TODO: simulate 'k' key pressed
    # assert mem.out == 75
    assert mem.out == 0


    ### Screen test
    
    mem.load = 1
    mem.in_ = -1
    mem.address = 0x4fcf
    mem.tick(); mem.tock()
    assert mem.out == -1

    mem.address = 0x504f
    mem.tick(); mem.tock()
    assert mem.out == -1
