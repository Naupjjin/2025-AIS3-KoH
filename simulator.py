from ctypes import *

class VM_Character(Structure):
    _fields_ = [("x", c_int), ("y", c_int), ("is_fork", c_bool)]

class VM_Chest(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

class Chest:
    def chal1() -> bool:
        return
    CHALS = [(chal1, 100)]

    def __init__(self, x: int, y: int):
        self.chest = VM_Chest(x, y)
        self.chals = self.chal1

    def interact():
        return

class Player:
    def __init__(self, id: int, script: str):
        self.id = id
        self.character = VM_Character(0, 0, False)
        self.buffer = (c_uint * 50)()
        self.script = script
        self.forks = []
        self.score = 0
        pass

    def move(self, dx: int, dy: int):
        self.character.x += dx
        self.character.y += dy

    def interact(self):
        return

    def attack(self):
        return

    def fork(self):
        self.forks.append(VM_Character(self.character.x,
                                        self.character.y, True))
        return

    def operate(self, opcode: int):
        match opcode:
            case 0:
                self.move(0, 1)
            case 1:
                self.move(0, -1)
            case 2:
                self.move(1, 0)
            case 3:
                self.move(-1, 0)
            case 4:
                self.interact()
            case 5:
                self.attack()
            case 6:
                self.fork()


class Simulator:
    players: list[Player]
    chests: list[Chest]
    def __init__(self, team_nums):
        self.vm = CDLL('./vm.lib')
        self.vm.vm_run.argtypes = [c_int, c_char_p, POINTER(c_uint),
                                    POINTER(POINTER(VM_Character)), c_int,
                                    POINTER(POINTER(VM_Chest)), c_int, c_int]
        self.vm.vm_run.restype = c_int
        self.players = []
        self.chests = []
        for i in range(1, team_nums + 1):
            self.players.append(Player(i, ""))
        return
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
            characters[i] = pointer(player.character)
            i += 1
            for fork in player.forks:
                characters[i] = pointer(fork)

        for player in self.players:
            self.vm.vm_run(player.id, player.script.encode(), player.buffer,
                        characters, character_num,
                        chests, len(self.chests), player.score)
        return
    
if __name__ == "__main__":
    sim = Simulator(10)
    sim.simulate()