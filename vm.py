UINT_MASK = 0xFFFFFFFF

class SharedMemory:
    def __init__(self):
        '''
        mem[0:50] shared memory

        '''
        self.shared = [0 for _ in range(50)]


    def __getitem__(self, addr):
        addr = int(addr)
        addr = self.check_addr_bound(addr)

        return self.shared[addr] & 0xFFFFFFFF
        

    def __setitem__(self, addr, value):
        addr = int(addr)
        value = value & 0xFFFFFFFF

        addr = self.check_addr_bound(addr)
        self.shared[addr] = value


    def check_addr_bound(self, addr):
        if not 0 <= addr < 50:
            raise IndexError("Shared Memory access out of bounds")
        
        return addr

class IsolationMemory:
    def __init__(self):
        '''
        mem[50:58]
        50 51 52
        53 *  54
        55 56 57
        '''
        self.isolation = [0 for _ in range(50)]


    def __getitem__(self, addr: int):
        addr = int(addr)
        addr = self.check_addr_bound(addr)

        return self.isolation[addr] & 0xFFFFFFFF
        

    def __setitem__(self, addr: int, value: int):
        addr = int(addr)
        value = value & 0xFFFFFFFF

        addr = self.check_addr_bound(addr)
        self.isolation[addr] = value


    def check_addr_bound(self, addr: int):
        if not 50 <= addr < 100:
            raise IndexError("Isolation Memory access out of bounds")
        
        return addr - 50

    def set_near_maps_info(self, near_maps: List[int]):
        for idx in range(50, 58):
            self.isolation[idx - 50] = near_maps[idx - 50]

    def clear_isolation_memory(self):
        for i in range(len(self.isolation)):
            self.isolation[i] = 0



class VM:
    def __init__(self, scores: int, sharedmemory: SharedMemory, isolation: IsolationMemory, chests=[], characters = []):
        self.all_code = self.parse_opcode()
        self.labels = {}

        self.scores = scores

        self.sharedmem = sharedmemory
        self.isolationmem = isolation

        self.chests = chests
        self.characters = characters

        self.pc = 0

    def check_opcode_format():
        pass

    def parse_opcode(self):
        pass

    def execute_opcode(self):
        pass

    def vm_run(self):
        '''
        ops:
        -1 error
        0 up
        1 down
        2 left
        3 right
        4 interact
        5 attack
        6 fork
        '''
        pass



shared = SharedMemory()
pid0_isolation = IsolationMemory()
scores = 0


