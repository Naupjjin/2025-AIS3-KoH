from ctypes import *
import glob
import random
import copy
import concurrent.futures
import threading
import json
import time

class VM_Character(Structure):
    _fields_ = [("x", c_int), ("y", c_int), ("is_fork", c_bool)]

class VM_Chest(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

class VM_Buffer(Structure):
    _pack_ = 1
    _fields_ = [("global", c_uint * 50), ("self", c_uint * 8), ("tmp", c_uint * 42)]

class Chest:
    type:int = 0
    score = 0
    param = []
    result = []
    def reverse_chal(self):
        self.param = [random.randint(0, 65536) for _ in range(5)]
        self.result = self.param.reverse()
        self.score = 30
    def sort_chal(self):
        self.param = [random.randint(0, 65536) for _ in range(7)]
        self.result = copy.deepcopy(self.param)
        self.result.sort()
        self.score = 40
    def rsa_chal(self):
        self.score = 50
        pass
    def point_addition_chal(self):
        self.score = 60
        pass
    
    CHALS = [reverse_chal, sort_chal, rsa_chal, point_addition_chal]

    def __init__(self, x: int, y: int):
        self.vm_chest = VM_Chest(x, y)
        self.type = random.randrange(0, len(self.CHALS))
        self.CHALS[self.type](self)

    def interact():
        return
    
    
class Character:
    def __init__(self, x: int, y :int, is_fork: bool):
        self.vm_char = VM_Character(x, y, is_fork)
        self.selfbuf = (c_uint * 8)()
        self.health = 3
        self.is_fork = is_fork
        self.move_to = None
        self.last_attackers: set[Player] = {}
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
        self.buffer = VM_Buffer()
        self.script = script
        self.forks = [Character(0, 0, False)]
        self.score = 0
        self.fork_cost = 10
        pass
class Record:
    team_num: int
    spawn_x: int
    spawn_y: int
    spawn_turn: int
    dead_turn: int = -1
    opcodes: list[int]
    def __init__(self, team_num, spawn_x, spawn_y, spawn_turn):
        self.team_num = team_num
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.spawn_turn = spawn_turn
        self.opcodes = []
        pass


MOVE_SCORE = 1
KILL_FORK_SCORE = 50

PATH = 0
WALL = 1
CHEST = 2
CHARACTER = 4


class Simulator:
    players: list[Player]
    chests: list[Chest]
    records: dict[Character, Record]
    turn: int = 0
    def __init__(self, team_num):
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
        '''
        bool vm_parse_script(
            const char script[]
        );
        '''
        self.vm.vm_parse_script.argtypes = [c_char_p]
        self.vm.vm_parse_script.restype = c_bool
        self.team_num = team_num
        self.new_round()
        return
    def new_round(self):
        maps = glob.glob("maps/*.txt")
        self.read_map(random.choice(maps))
        self.players = []
        self.chests = []
        self.records = {}
        self.chest_records = []
        for i in range(10):
            new_chest = Chest(random.randrange(0, 200), random.randrange(0, 200))
            self.chests.append(new_chest)
            self.chest_records.append({
                "x": new_chest.vm_chest.x,
                "y": new_chest.vm_chest.y,
                "spawn_turn": self.turn,
                "dead_turn": -1
            })

        for i in range(1, self.team_num + 1):
            new_player = Player(i, "")
            self.players.append(new_player)
            player_char = new_player.forks[0]
            player_char.vm_char.x = random.randrange(0, 200)
            player_char.vm_char.y = random.randrange(0, 200)
            self.records[player_char] = Record(i, player_char.vm_char.x, player_char.vm_char.y, self.turn)
        pass

    def read_map(self, map: str):
        self.map = [[0 for i in range(200)] for j in range(200)]
        self.turnmap = copy.deepcopy(self.map)
        m = open(map, "r").read()
        i = 0
        for line in m.splitlines():
            for j in range(200):
                if line[j] == '#':
                    self.map[i][j] = 1
            i += 1
    def set_script(self, id: int, script: str):
        if id > len(self.players):
            return
        self.players[id - 1].script = script
    
    def check_script(self, script: str):
        return self.vm.vm_parse_script(script.encode())
    
    def move(self, player: Player, character: Character, dx:int, dy:int):
        rx = character.vm_char.x + dx
        ry = character.vm_char.y + dy
        if rx >= 0 and rx < 200 and ry >= 0 and ry < 200:
            if self.map[ry][rx] == 0:
                player.score += MOVE_SCORE
                character.move_to = (rx, ry)

    def attack(self, player: Player, character: Character):
        print("attack")
        for p in self.players:
            for fork in p.forks:
                if character.can_interact(fork.vm_char.x, fork.vm_char.y):
                    if character.is_fork:
                        print(f"attack player {p.id}")
                    else:
                        print(f"attack player {p.id} fork")    
                    fork.last_attackers.add(player)
                    fork.health -= 1
        

    def interact(self, player: Player, character: Character):
        print("interact")
        for chest in self.chests:
            if character.can_interact(chest.vm_chest.x, chest.vm_chest.y):
                print("interact chest")

                # the result is store in buf[50] ~ buf[57]
                i = 1
                for r in chest.result:
                    # fill param
                    if character.selfbuf[i] != r:
                        character.selfbuf[0] = chest.type
                        j = 1
                        for p in chest.param:
                            character.selfbuf[j] = p
                            j +=1
                        return
                    i += 1
                self.chests.remove(chest)
                player.score += chest.score
                return


    def fork(self, player: Player, character: Character):
        if len(player.forks) >= 4:
            print("exceeds fork limit")
            return 
        if player.score >= player.fork_cost:
            new_char = Character(character.vm_char.x, character.vm_char.y, True)
            player.forks.append(new_char)
            player.score -= player.fork_cost
            player.fork_cost *= 2
            self.records[new_char] = Record(player.id, new_char.vm_char.x, new_char.vm_char.y, self.turn)
            print("fork")
        return
    
    def dump_records(self):
        records = {}
        for key, value in self.records.items():
            if value.team_num not in records:
                records[value.team_num] = []
            records[value.team_num].append({
                "opcodes": ''.join(str(i) for i in value.opcodes),
                "spawn_x": value.spawn_x,
                "spawn_y": value.spawn_y,
                "spawn_turn": value.spawn_turn,
                "dead_turn": value.dead_turn,
                "is_fork": key.is_fork
            })
        return json.dumps(records)
    def dump_scores(self):
        scores = {}
        for player in self.players:
            scores[player.id] = player.score
        return json.dumps(scores)

    def simulate(self):
        character_num = 0
        self.turnmap = copy.deepcopy(self.map)
        # fill map data
        for chest in self.chests:
            self.turnmap[chest.vm_chest.y][chest.vm_chest.x] |= CHEST

        for player in self.players:
            for fork in player.forks:
                self.turnmap[fork.vm_char.y][fork.vm_char.x] |= CHARACTER

        # count total character number

        for player in self.players:    
            character_num += len(player.forks)

        characters = (POINTER(VM_Character) * character_num)()
        chests = (POINTER(VM_Chest) * len(self.chests))()
        i = 0
        for player in self.players:
            for fork in player.forks:
                characters[i] = pointer(fork.vm_char)
                i += 1

        # record results
        character_opcode = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.players)) as executor:
            def execute_vm(player: Player):
                result_list = []
                for fork in player.forks:
                    memset(player.buffer.tmp, 0, 42 * sizeof(c_uint))
                    memmove(player.buffer.self, fork.selfbuf, 8 * sizeof(c_uint))
                    id = player.id
                    if fork.is_fork:
                        id = 0
                    # # fill information
                    player.buffer.tmp[0] = id
                    dx = [0, 1, 1, 1, 0, -1, -1, -1]
                    dy = [-1, -1, 0, 1, 1, 1, 0, -1]
                    for i in range(8):
                        x = fork.vm_char.x + dx[i]
                        y = fork.vm_char.y + dy[i]
                        if x < 0 or x >= 200 or y < 0 or y >= 200:
                            player.buffer.tmp[i + 1] = WALL
                        else:
                            player.buffer.tmp[i + 1] = self.turnmap[y][x]
                    opcode = self.vm.vm_run(id, player.script.encode(), cast(pointer(player.buffer), POINTER(c_uint)),
                            characters, character_num,
                            chests, len(self.chests), player.score, fork.vm_char)
                    memmove(fork.selfbuf, player.buffer.self, 8 * sizeof(c_uint))
                    result_list.append((player, fork, opcode))
                return result_list
            jobs:list[concurrent.futures.Future] = []
            for player in self.players:
                jobs.append(executor.submit(execute_vm, player))
            for job in jobs:
                character_opcode += job.result()
        # do operations
        for player, character, opcode in character_opcode:
            self.records[character].opcodes.append(opcode)
            match opcode:
                case 1:
                    self.move(player, character, 0, -1)
                case 2:
                    self.move(player, character, 0, 1)
                case 3:
                    self.move(player, character, -1, 0)
                case 4:
                    self.move(player, character, 1, 0)
                case 5:
                    self.interact(player, character)
                case 6:
                    self.attack(player, character)
                case 7:
                    self.fork(player, character)
        # remove dead characters
        for player in self.players:
            for fork in player.forks:
                if fork.move_to != None:
                    fork.vm_char.x, fork.vm_char.y = fork.move_to
                    print(f"move to {fork.vm_char.x} {fork.vm_char.y}")
                    fork.move_to = None
                if fork.health <= 0:
                    if fork.is_fork:
                        for attacker in fork.last_attackers:
                            attacker.score += KILL_FORK_SCORE
                        player.forks.remove(fork)
                        self.records[fork].dead_turn = self.turn
                    else:
                        for attacker in player.character.last_attackers:
                            attacker.score += player.score // 3
                        player.score -= player.score // 3
                        #respawn
                fork.last_attackers.clear()

        self.turn += 1
        return
    
    def debug(self, n_turn):
        print(f"=== Turn {n_turn} ===")
        debug_map = [['#' if self.map[y][x] else '.' for x in range(200)] for y in range(200)]

        for player in self.players:
            for i, fork in enumerate(player.forks):
                x = fork.vm_char.x
                y = fork.vm_char.y
                if 0 <= x < 200 and 0 <= y < 200:
                    if fork.is_fork:
                        debug_map[y][x] = chr(ord('a') + ((player.id - 1) % 26))  # 分身：小寫
                    else:
                        debug_map[y][x] = chr(ord('A') + ((player.id - 1) % 26))  # 主體：大寫

        for chest in self.chests:
            x = chest.vm_chest.x
            y = chest.vm_chest.y
            if 0 <= x < 200 and 0 <= y < 200:
                debug_map[y][x] = '$'

        for row in debug_map:
            print(''.join(row))

    
if __name__ == "__main__":
    sim = Simulator(4)
    sim.read_map("maps/map_01.txt")
    sim.players[0].script = '''
loop:
    je 0 0 loop

    '''
    print(random.randrange(0,4))