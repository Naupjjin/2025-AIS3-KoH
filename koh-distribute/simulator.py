from ctypes import *
import glob
import random
import copy
import concurrent.futures
import threading
import json
import time
import math
import os

MAP_SIZE = 50

class VM_Character(Structure):
    _fields_ = [("x", c_int), ("y", c_int), ("is_fork", c_bool)]

class VM_Chest(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

class VM_Buffer(Structure):
    _pack_ = 1
    _fields_ = [("global", c_uint * 50), ("self", c_uint * 8), ("tmp", c_uint * 42)]

last_chest_id = 0
class Chest:
    cid: int
    type:int = 0
    score = 0
    param = []
    result = []
    def reverse_chal(self):
        self.param = [random.randint(0, 65536) for _ in range(7)]
        self.result = copy.deepcopy(self.param)
        self.param.reverse()
        self.score = 30

    def sort_chal(self):
        self.param = [random.randint(0, 65536) for _ in range(7)]
        self.result = copy.deepcopy(self.param)
        self.result.sort()
        self.score = 40
    
    def point_addition_chal(self):
        self.score = 60

        # y^2 = x^3 + a*x + b (mod p)
        p = 9739
        a, b = 3, 7

        def inv_mod(x, m):
            return pow(x, -1, m)

        def is_on_curve(x, y):
            return (y * y - (x * x * x + a * x + b)) % p == 0

        def point_add(P, Q):
            x1, y1 = P
            x2, y2 = Q

            if x1 == x2 and (y1 + y2) % p == 0:
                return None  

            if P != Q:
                lam = ((y2 - y1) * inv_mod((x2 - x1) % p, p)) % p
            else:
                if y1 == 0:
                    return None 
                lam = ((3 * x1 * x1 + a) * inv_mod((2 * y1) % p, p)) % p

            x3 = (lam * lam - x1 - x2) % p
            y3 = (lam * (x1 - x3) - y1) % p
            return (x3, y3)

        def random_point():
            while True:
                x = random.randint(0, p - 1)
                rhs = (x**3 + a*x + b) % p
            
                if pow(rhs, (p-1)//2, p) != 1:
                    continue  
                for y in range(p):
                    if (y*y) % p == rhs:
                        return (x, y)

        while True:
            P = random_point()
            Q = random_point()
            R = point_add(P, Q)
            if R is not None:
                break

        # print(f"P = {P}")
        # print(f"Q = {Q}")
        # print(f"P + Q = {R}")
        # a, b, p, px, py, qx, qy
        self.param = [a, b, p, P[0], P[1], Q[0], Q[1]]
        self.result = [R[0], R[1]]

    def rsa_chal(self):
        self.score = 50

        def is_prime(n):
            if n < 2:
                return False
            if n % 2 == 0:
                return n == 2
            r = int(n ** 0.5) + 1
            for i in range(3, r, 2):
                if n % i == 0:
                    return False
            return True

        def gen_prime(low=1000, high=50000):
            while True:
                n = random.randint(low, high)
                if is_prime(n):
                    return n

        def egcd(a, b):
            if b == 0:
                return (a, 1, 0)
            g, x1, y1 = egcd(b, a % b)
            return (g, y1, x1 - (a // b) * y1)

        def modinv(a, m):
            g, x, y = egcd(a, m)
            if g != 1:
                return None
            return x % m

        def rsa_gen():

            p = gen_prime()
            q = gen_prime()
            n = p * q
            if n > 2**32 - 1:
                return rsa_gen() 

            phi = (p - 1) * (q - 1)

            e = 65537  
            if math.gcd(e, phi) != 1:
                return rsa_gen()
            d = modinv(e, phi)

            m = random.randint(2, n-1)

            c = pow(m, e, n)

            m2 = pow(c, d ,n)
            if m2 != m:
                return rsa_gen

            return (p, q, e, c, m)

        rsa_list = rsa_gen()
        self.param = [rsa_list[0], rsa_list[1], rsa_list[2], rsa_list[3]]
        self.result = [rsa_list[4]]

    
    CHALS = [reverse_chal, sort_chal, rsa_chal, point_addition_chal]

    def __init__(self, map):
        global last_chest_id
        self.cid = last_chest_id
        last_chest_id += 1
        rx = random.randrange(0, MAP_SIZE)
        ry = random.randrange(0, MAP_SIZE)
        if map != None:
            while map[ry][rx] == WALL:
                rx = random.randrange(0, MAP_SIZE)
                ry = random.randrange(0, MAP_SIZE)
        self.vm_chest = VM_Chest(rx, ry)
        self.type = random.randrange(1, len(self.CHALS)+1)
        self.CHALS[self.type - 1](self)
    
last_cid = 0
class Character:
    def __init__(self, x: int, y :int, is_fork: bool):
        global last_cid
        self.vm_char = VM_Character(x, y, is_fork)
        self.selfbuf = (c_uint * 8)()
        self.is_fork = is_fork
        self.move_to = None
        self.cid = last_cid
        last_cid += 1
        self.last_attackers: set[Player] = set()
        if self.is_fork:
            self.health = 2
        else:
            self.health = 3
    def can_interact(self, x:int, y:int):
        self_x = self.vm_char.x 
        self_y = self.vm_char.y
        # surrounding cells
        if not (self_x == x and self_y == y) and abs(self_x - x) <= 1 and abs(self_y - y) <= 1:
            return True
        return False
    def spawn(self, map: list[list[int]]):

        rx = random.randrange(0, MAP_SIZE)
        ry = random.randrange(0, MAP_SIZE)
        if map != None:
            while map[ry][rx] == WALL:
                rx = random.randrange(0, MAP_SIZE)
                ry = random.randrange(0, MAP_SIZE)
        self.vm_char.x = rx
        self.vm_char.y = ry

class Player:
    forks: list[Character]
    def __init__(self, id: int, script: str):
        self.id = id
        self.buffer = VM_Buffer()
        self.script = script
        self.forks = [Character(0, 0, False)]
        self.score = 0
        self.fork_cost = 70
        pass
class CharacterRecord:
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

class ChestRecord:
    x: int
    y: int
    spawn_turn: int
    opened_turn: int = -1
    def __init__(self, x, y, spawn_turn):
        self.x = x
        self.y = y
        self.spawn_turn = spawn_turn
        pass

class ScoreRecord:
    team_id: int
    scores: list[int]
    def __init__(self, team_id):
        self.team_id = team_id
        self.scores = [0]
        pass



MOVE_SCORE = 1
KILL_FORK_SCORE = 40
KILL_PLAYER_SCORE = 70

PATH = 0
WALL = 1
CHEST = 2
CHARACTER = 4


class Simulator:
    players: list[Player]
    chests: list[Chest]
    char_records: dict[Character, CharacterRecord]
    chest_records: dict[Chest, ChestRecord]
    score_records: dict[Player, ScoreRecord]
    turn: int = 0
    def __init__(self, team_num):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.vm = CDLL(os.path.join(self.base_dir, "vm.lib"))
        '''
        int vm_run(
            int team_id,
            const char opcode_cstr[],
            unsigned int* buffer,
            VM_Character** players, int player_count,
            VM_Chest** chests, int chest_count,
            unsigned char* map,
            int scores, VM_Character* self
        );
        '''
        self.vm.vm_run.argtypes = [c_int, c_char_p, POINTER(c_uint),
                                    POINTER(POINTER(VM_Character)), c_int,
                                    POINTER(POINTER(VM_Chest)), c_int,
                                    POINTER(c_uint8),
                                    c_int, POINTER(VM_Character)]
        self.vm.vm_run.restype = c_int
        '''
        bool vm_parse_script(
            const char script[]
        );
        '''
        self.vm.vm_parse_script.argtypes = [c_char_p, POINTER(c_int)]
        self.vm.vm_parse_script.restype = c_bool
        self.team_num = team_num
        self.new_round()
        return
    def new_round(self):
        global last_cid, last_chest_id
        last_chest_id = 0
        last_cid = 0
        maps = glob.glob(os.path.join(self.base_dir, "maps/*.txt"))
        self.read_map(random.choice(maps))

    def read_map(self, map: str):
        self.map = [[0 for i in range(MAP_SIZE)] for j in range(MAP_SIZE)]
        m = open(map, "r").read()
        i = 0
        for line in m.splitlines():
            if i == MAP_SIZE:
                break
            for j in range(MAP_SIZE):
                if line[j] == '#':
                    self.map[i][j] = 1
            i += 1

        # replant chests
        self.chests = []
        self.chest_records = {}
        for i in range(10):
            new_chest = Chest(self.map)
            self.chests.append(new_chest)
            self.chest_records[new_chest] = ChestRecord(new_chest.vm_chest.x, new_chest.vm_chest.y, self.turn)

        # respawn character
        self.players = []
        self.char_records = {}
        for i in range(1, self.team_num + 1):
            new_player = Player(i, "")
            self.players.append(new_player)
            player_char = new_player.forks[0]
            player_char.spawn(self.map)
            self.char_records[player_char] = CharacterRecord(i, player_char.vm_char.x, player_char.vm_char.y, self.turn)
        pass
        self.score_records = {}
        for p in self.players:
            self.score_records[p] = ScoreRecord(p.id) 

    def set_script(self, id: int, script: str):
        if id > len(self.players):
            return
        self.players[id - 1].script = script
    
    def check_script(self, script: str) -> tuple[bool, int]:
        error_line = c_int(0)
        success = self.vm.vm_parse_script(script.encode(), pointer(error_line))
        return (success, error_line.value)
    
    def move(self, player: Player, character: Character, dx:int, dy:int):
        rx = character.vm_char.x + dx
        ry = character.vm_char.y + dy
        if rx >= 0 and rx < MAP_SIZE and ry >= 0 and ry < MAP_SIZE:
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
                self.chest_records[chest].opened_turn = self.turn
                player.score += chest.score
                return


    def fork(self, player: Player, character: Character):
        if len(player.forks) >= 4:
            print("exceeds fork limit")
            return 
        if player.score >= player.fork_cost:
            new_char = Character(character.vm_char.x, character.vm_char.y, True)
            self.char_records[new_char] = CharacterRecord(player.id, new_char.vm_char.x, new_char.vm_char.y, self.turn)
            player.forks.append(new_char)
            player.score -= player.fork_cost
            player.fork_cost *= 1.2
            print("fork")
        return
    
    def dump_character_records(self):
        records = {}
        for key, value in self.char_records.items():
            if value.team_num not in records:
                records[value.team_num] = []
            records[value.team_num].append({
                "cid": key.cid,
                "opcodes": ''.join(str(i) for i in value.opcodes),
                "spawn_x": value.spawn_x,
                "spawn_y": value.spawn_y,
                "spawn_turn": value.spawn_turn,
                "dead_turn": value.dead_turn,
                "is_fork": key.is_fork
            })
        return json.dumps(records)
    
    def dump_chest_records(self):
        records = []
        for key, value in self.chest_records.items():
            records.append({
                "cid": key.cid,
                "x": value.x,
                "y": value.y,
                "spawn_turn": value.spawn_turn,
                "opened_turn": value.opened_turn
            })
        return json.dumps(records)
    def dump_scores(self):
        scores = {}
        for player in self.players:
            scores[player.id] = player.score
        return scores
    
    def dump_score_records(self):
        records = {}
        for key, value in self.score_records.items():
            records[key.id] = value.scores
        return records

    def simulate(self):
        character_num = 0
        self.turnmap = ((c_uint8 * MAP_SIZE) * MAP_SIZE)()
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):
                self.turnmap[i][j] = self.map[i][j]
        if self.turn % 10 == 0:
            for i in range(2):
                new_chest = Chest(self.map)
                self.chests.append(new_chest)
                self.chest_records[new_chest] = ChestRecord(new_chest.vm_chest.x, new_chest.vm_chest.y, self.turn)
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

        i = 0
        for chest in self.chests:
                chests[i] = pointer(chest.vm_chest)
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
                    opcode = 0
                    opcode = self.vm.vm_run(id, player.script.encode(), cast(pointer(player.buffer), POINTER(c_uint)),
                            characters, character_num,
                            chests, len(self.chests), cast(pointer(self.turnmap), POINTER(c_uint8)), player.score, fork.vm_char)
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
            if character in self.char_records:
                self.char_records[character].opcodes.append(opcode)
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
                    print(f"{player.id}: move to {fork.vm_char.x} {fork.vm_char.y}")
                    fork.move_to = None
                if fork.health <= 0:
                    for attacker in fork.last_attackers:
                        player.forks.remove(fork)
                        self.char_records[fork].dead_turn = self.turn
                        if fork.is_fork:
                            attacker.score += KILL_FORK_SCORE
                        else:
                            attacker.score += KILL_PLAYER_SCORE

                    if not fork.is_fork:
                        # respawn
                        new_char = Character(0, 0, False)
                        new_char.spawn(self.map)
                        self.char_records[new_char] = CharacterRecord(player.id, new_char.vm_char.x, new_char.vm_char.y, self.turn)
                        player.forks.append(new_char)
                fork.last_attackers.clear()

        for p in self.players:
            self.score_records[p].scores.append(p.score)
        self.turn += 1
        return
