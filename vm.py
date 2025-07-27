UINT_MASK = 0xFFFFFFFF

class SharedMemory:
    def __init__(self):
        '''
        mem[0:50] shared memory

        '''
        self.shared = [0 for _ in range(50)]


    def __getitem__(self, addr):
        addr = int(addr)

        return self.shared[addr] & UINT_MASK
        

    def __setitem__(self, addr, value):
        addr = int(addr)
        value = value & UINT_MASK

        self.shared[addr] = value


    def clear_shared_memory(self):
        for i in range(len(self.shared)):
            self.shared[i] = 0        

class IsolationMemory:
    def __init__(self):
        '''
        mem[50:58]
        50 51 52
        53 *  54
        55 56 57
        mem[58:100] : reserved
        '''
        self.isolation = [0 for _ in range(50)]


    def __getitem__(self, addr: int):
        addr = int(addr)

        return self.isolation[addr] & UINT_MASK
        

    def __setitem__(self, addr: int, value: int):
        addr = int(addr)
        value = value & UINT_MASK
        self.isolation[addr] = value


    def clear_isolation_memory(self):
        for i in range(len(self.isolation)):
            self.isolation[i] = 0

class Memory:
    def __init__(self, shared_memory: SharedMemory):
        self.sharedmem = shared_memory
        self.isolationmem = IsolationMemory()

    def read_memory(self, addr):
        addr = int(addr)
        if 0 <= addr < 50:
            return self.sharedmem[addr]
        elif 50 <= addr < 100:
            return self.isolationmem[addr - 50]
        else:
            raise IndexError(f"Invalid memory read at address {addr}")

    def write_memory(self, addr, value):
        addr = int(addr)
        value = value & UINT_MASK
        if 0 <= addr < 50:
            self.sharedmem[addr] = value
        elif 50 <= addr < 100:
            self.isolationmem[addr - 50] = value
        else:
            raise IndexError(f"Invalid memory write at address {addr}")


'''
VM will return 
- ops
- team id
- pid
'''

class VM:
    def __init__(self, team_id: int, pid: int, scores: int, memory: Memory , chests = [], characters = []):
        '''
        chests: all chests (x,y)
        characters: all characters (x,y,id)
        '''
        self.team_id = team_id
        self.pid = pid

        self.all_code = self.parse_opcode()
        self.labels = {}

        self.scores = scores

        self.memory = memory

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

        team_id: 1~10
        pid: 
        '''
        pass





