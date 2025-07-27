import re

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

        mem[58:62]
        prev turn 

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
    def __init__(self, team_id: int, pid: int, scores: int, memory: Memory, opcode: str , chests = [], characters = []):
        '''
        chests: all chests (x,y)
        characters: all characters (x,y,id)
        '''
        self.team_id = team_id
        self.pid = pid
        self.labels = {}

        self.scores = scores

        self.memory = memory

        self.chests = chests
        self.characters = characters

        self.pc = 0
        self.all_code = self.parse_opcode(opcode)
        self.check_opcode_format(self.all_code)

    def parse_opcode(self, opcode: str) -> list:

        lines = opcode.strip().split(";")
        result = []
        pc = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # label_<number> 
            if re.fullmatch(r'label_\d+', line):
                self.labels[line] = pc
                continue

            tokens = line.split()
            result.append(tokens)
            pc += 1

        return result

    def check_opcode_format(self, opcode_list: list):
        OPCODE_FORMAT = {
            "mov": 2,
            "movi": 3,
            "addc": 2,
            "addm": 2,
            "shr": 2,
            "shl": 2,
            "mulc": 2,
            "mulm": 2,
            "divm": 2,
            "je": 3,
            "jg": 3,
            "inc": 1,
            "dec": 1,
            "and": 2,
            "or": 2,
            "ng": 1,
            "ret": 0,
            "load_score": 1,
            "locate_nearest_k_chest": 2,
            "locate_nearest_k_character": 2,
        }
        pass

    def execute_opcode(self, opcode_list: list):
        '''
        return 
        0 success
        -1 failed
        '''
        opcode = ""

            
        

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
        return {
            "ops": 0,
            "team_id": 0,
            "pid": 0
        }

    def debug(self):
        print(self.all_code)


player0_opcode = '''
addc 0 100;
addc 1 123;
mulc 1 3;
je 0 1 label_1;
addc 2 12345;
ret;
label_1;
add 3 124;
ret;
'''

player0_info = {
    "team_id": 0,
    "pid": 100,
    "scores": 100,
}

player0_shared = SharedMemory()
player0_Memory = Memory(player0_shared)

player0_vm = VM(player0_info["team_id"], player0_info["pid"], player0_info["scores"], player0_Memory, player0_opcode)
player0_vm.debug()

'''
all opcode:
// mem1 = mem2
mov <mem1> <mem2>

// mem1 = mem2[mem3]
movi <mem1> <mem2> <mem3>
// mem1 += constant
addc <mem1> #<constant>
// mem1 += mem2
addm <mem1> <mem2>
shr <mem1> #<constant>
shl <mem1> #<constant>
mulc <mem1> #<constant>
mulm <mem1> <mem2>
divm <mem1> <mem2>
je <mem1> <mem2> $<label>
jg <mem1> <mem2> $<label>
inc <mem1>
dec <mem2>
and <mem1> <mem2>
or <mem1> <mem2>

// mem = ~mem
ng <mem1>

ret (end)

// mem1 = score
load_score <mem1>

// mem2[0], mem2[1] = chest[mem1].xy
locate_nearest_k_chest <mem1> <mem2>

// mem2[0], mem2[1], mem2[2] = character[k].is_fork, character[k].xy
locate_nearest_k_character <mem1> <mem2>

; Separate opcodes
'''
