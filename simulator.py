from ctypes import *

class VM_Character(Structure):
    _fields_ = [("x", c_int), ("y", c_int), ("is_fork", c_bool)]

class VM_Chest(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

class VM_Buffer(Structure):
    _pack_ = 1
    _fields_ = [("global", c_uint * 50), ("self", c_uint * 8), ("tmp", c_uint * 42)]

class Chest:
    def chal1() -> bool:
        return
    CHALS = [(chal1, 100)]

    def __init__(self, x: int, y: int):
        self.vm_chest = VM_Chest(x, y)
        self.chals = self.chal1

    def interact():
        return
    
class Character:
    def __init__(self, x: int, y :int, is_fork: bool):
        self.vm_char = VM_Character(x, y, is_fork)
        self.selfbuf = (c_uint * 8)()
    def can_interact(self, x:int, y:int):
        self_x = self.vm_char.x 
        self_y = self.vm_char.y
        # surrounding cells
        if self_x != x and self_y != y and abs(self_x - x) <= 1 and abs(self_y - y) <= 1:
            return True
        return False

class Player:
    forks: list[Character]
    def __init__(self, id: int, script: str):
        self.id = id
        self.character = Character(0, 0, False)
        self.buffer = VM_Buffer()
        self.script = script
        self.forks = []
        self.score = 0
        pass

class Simulator:
    players: list[Player]
    chests: list[Chest]
    def __init__(self, team_nums):
        self.vm = CDLL('./vm.lib')
        '''
int vm_run(
    int team_id,
    const char opcode_cstr[],
    unsigned int* buffer,
    VM_Character** players, int player_count,
    VM_Chest** chests, int chest_count,
    int scores, VM_Character* self
);
        '''
        self.vm.vm_run.argtypes = [c_int, c_char_p, POINTER(c_uint),
                                    POINTER(POINTER(VM_Character)), c_int,
                                    POINTER(POINTER(VM_Chest)), c_int, c_int, POINTER(VM_Character)]
        self.vm.vm_run.restype = c_int
        self.players = []
        self.chests = []
        for i in range(1, team_nums + 1):
            self.players.append(Player(i, ""))
        return
    
    def move(self, character: Character, dx:int, dy:int):
        character.vm_char.x += dx
        character.vm_char.y += dy
        print(f"move to {character.vm_char.x} {character.vm_char.y}")

    def attack(self, character: Character):
        print("attack")
        for player in self.players:
            if character.can_interact(player.character.vm_char.x, player.character.vm_char.y):
                print(f"attack player {player.id}")
            for fork in player.forks:
                if character.can_interact(fork.vm_char.x, fork.vm_char.y):
                    print(f"attack player {player.id} fork")            
        pass

    def interact(self, character: Character):
        print("interact")
        for chest in self.chests:
            if character.can_interact(chest.vm_chest.x, chest.vm_chest.y):
                print("interact chest")

        pass

    def fork(self, character: Character, player: Player):
        player.forks.append(Character(character.vm_char.x, character.vm_char.y, True))
        print("fork")
        pass

    def simulate(self):
        character_num = 0
        for player in self.players:
            character_num += 1
            for _ in player.forks:
                character_num += 1

        characters = (POINTER(VM_Character) * character_num)()
        chests = (POINTER(VM_Chest) * len(self.chests))()
        i = 0
        for player in self.players:
            characters[i] = pointer(player.character.vm_char)
            i += 1
            for fork in player.forks:
                characters[i] = pointer(fork.vm_char)
        character_opcode = []
        for player in self.players:

            memset(player.buffer.tmp, 0, 42 * sizeof(c_uint))
            memmove(player.buffer.self, player.character.selfbuf, 8 * sizeof(c_uint))

            opcode = self.vm.vm_run(player.id, player.script.encode(), cast(pointer(player.buffer), POINTER(c_uint)),
                        characters, character_num,
                        chests, len(self.chests), player.score, player.character.vm_char)
            memmove(player.character.selfbuf, player.buffer.self, 8 * sizeof(c_uint))
            character_opcode.append((player, player.character, opcode))
            for fork in player.forks:
                memset(player.buffer.tmp, 0, 42 * sizeof(c_uint))
                memmove(player.buffer.self, fork.selfbuf, 8 * sizeof(c_uint))

                opcode = self.vm.vm_run(0, player.script.encode(), cast(pointer(player.buffer), POINTER(c_uint)),
                        characters, character_num,
                        chests, len(self.chests), player.score, fork.vm_char)
                memmove(fork.selfbuf, player.buffer.self, 8 * sizeof(c_uint))
                character_opcode.append((player, fork, opcode))

        for player, character, opcode in character_opcode:
            match opcode:
                case 0:
                    self.move(character, 0, 1)
                case 1:
                    self.move(character, 0, -1)
                case 2:
                    self.move(character, 1, 0)
                case 3:
                    self.move(character, -1, 0)
                case 4:
                    self.interact(character)
                case 5:
                    self.attack(character)
                case 6:
                    self.fork(character, player)
            
        return
    
if __name__ == "__main__":
    sim = Simulator(1)
    sim.players[0].script = '''
        addc 0 100;
        addc 1 23;
        mulc 1 2;
        addc 1 54;
        load_score 5;
        get_id 6;
        locate_nearest_k_chest 0 7;
        locate_nearest_k_chest 1 9;
        locate_nearest_k_chest 2 11;
        locate_nearest_k_character 0, 15;
        locate_nearest_k_character 1, 18;
        locate_nearest_k_character 2, 21;
        je 0 1 label_1;
        addc 2 9999;
        ret;
        label_1;
        addc 3 777;
        ret;
'''
    for i in range(200):
        sim.simulate()