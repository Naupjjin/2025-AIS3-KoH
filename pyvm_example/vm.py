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
    def __init__(self, team_id: int, scores: int, memory: Memory, opcode: str , chests: list, characters: list):

        self.team_id = team_id

        self.labels = {}

        self.scores = scores

        self.memory = memory

        self.chests = chests
        self.characters = characters

        self.pc = 0
        self.opcode_list = self.parse_opcode(opcode)
        self.check_opcode_format(self.opcode_list)

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

        for tokens in opcode_list:
            instr = tokens[0]

            if instr not in OPCODE_FORMAT:
                raise ValueError(f"Unknown opcode: {instr}")

            expected_argc = OPCODE_FORMAT[instr]
            actual_argc = len(tokens) - 1

            if expected_argc != actual_argc:
                raise ValueError(f"Opcode '{instr}' expects {expected_argc} arguments, got {actual_argc}")

    def execute_opcode(self):
        '''
        return 
        0 success (遇到 ret)
        raise error (invalid op 或 exception)
        '''
        self.pc = 0
        while self.pc < len(self.opcode_list):
            tokens = self.opcode_list[self.pc]
            op = tokens[0]

            match op:
                case "mov":
                    dst, src = map(int, tokens[1:3])
                    self.memory.write_memory(dst, self.memory.read_memory(src))

                case "movi": 
                    dst, base, index = map(int, tokens[1:4])
                    addr = self.memory.read_memory(index) + base
                    value = self.memory.read_memory(addr)
                    self.memory.write_memory(self.memory.read_memory(dst), value)

                case "addc":
                    dst, constant = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(dst) + constant
                    self.memory.write_memory(dst, value)

                case "addm":
                    dst, src = map(int, tokens[1:3])
                    value = self.memory.read_memory(dst) + self.memory.read_memory(src)
                    self.memory.write_memory(dst, value)

                case "shr":
                    dst, constant = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(dst) >> constant
                    self.memory.write_memory(dst, value)

                case "shl":
                    dst, constant = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(dst) << constant
                    self.memory.write_memory(dst, value)

                case "mulc":
                    dst, constant = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(dst) * constant
                    self.memory.write_memory(dst, value)

                case "mulm":
                    dst, src = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(dst) * self.memory.read_memory(src)
                    self.memory.write_memory(dst, value)

                case "divm":
                    dst, src = int(tokens[1]), int(tokens[2])
                    divisor = self.memory.read_memory(src)
                    if divisor == 0:
                        return -1
                    value = self.memory.read_memory(dst) // divisor
                    self.memory.write_memory(dst, value)

                case "je":
                    a, b = int(tokens[1]), int(tokens[2])
                    label = tokens[3]
                    if self.memory.read_memory(a) == self.memory.read_memory(b):
                        self.pc = self.labels[label]
                        continue

                case "jg":
                    a, b = int(tokens[1]), int(tokens[2])
                    label = tokens[3]
                    if self.memory.read_memory(a) > self.memory.read_memory(b):
                        self.pc = self.labels[label]
                        continue

                case "inc":
                    dst = int(tokens[1])
                    self.memory.write_memory(dst, self.memory.read_memory(dst) + 1)

                case "dec":
                    dst = int(tokens[1])
                    self.memory.write_memory(dst, self.memory.read_memory(dst) - 1)

                case "and":
                    a, b = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(a) & self.memory.read_memory(b)
                    self.memory.write_memory(a, value)

                case "or":
                    a, b = int(tokens[1]), int(tokens[2])
                    value = self.memory.read_memory(a) | self.memory.read_memory(b)
                    self.memory.write_memory(a, value)

                case "ng":
                    a = int(tokens[1])
                    value = ~self.memory.read_memory(a)
                    self.memory.write_memory(a, value)

                case "load_score":
                    mem = int(tokens[1])
                    self.memory.write_memory(mem, self.scores)

                

                case "ret":
                    return 0

                case _:
                    raise Exception(f"Unknown instruction: {tokens}") # Unknown instruction

            self.pc += 1



        return 0


            
        

    def vm_run(self) -> int:
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

        self.execute_opcode()
        return ops

    def debug(self):
        print(self.opcode_list)
        for i in range(5):
            print(self.memory.read_memory(i))


player0_opcode = '''
addc 0 100;
addc 1 123;
mulc 1 3;
addc 0 269;
je 0 1 label_1;
addc 2 12345;
ret;
label_1;
addc 3 124;
ret;
'''

player0_info = {
    "team_id": 0,
    "scores": 100,
}

chests = [(1,2),(57, 86),(7,25)]


player0_shared = SharedMemory()
player0_Memory = Memory(player0_shared)

player0_vm = VM(player0_info["team_id"], player0_info["scores"], player0_Memory, player0_opcode)
player0_vm.vm_run()
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
