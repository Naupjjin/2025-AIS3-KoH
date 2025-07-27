#include "vm.h"
#include <vector>
#include <string>
#include <sstream>
#include <unordered_map>
#include <cstring>
#include <iostream>
#include <algorithm>
#include <chrono>


void parse_opcode(
    const std::string& opcode_str,
    std::vector<std::vector<std::string>>& instructions,
    std::unordered_map<std::string, int>& labels
) {
    std::istringstream iss(opcode_str);
    std::string line;
    int pc = 0;

    while (std::getline(iss, line, ';')) {

        size_t start = line.find_first_not_of(" \t\n\r");
        size_t end = line.find_last_not_of(" \t\n\r");
        if (start == std::string::npos) continue;
        line = line.substr(start, end - start + 1);

        if (line.empty()) continue;

 
        if (line.rfind("label_", 0) == 0) {
            labels[line] = pc;
            continue;
        }

        std::istringstream token_iss(line);
        std::vector<std::string> tokens;
        std::string token;
        while (token_iss >> token) {
            tokens.push_back(token);
        }

        if (!tokens.empty()) {
            instructions.push_back(tokens);
            pc++;
        }
    }
}

void check_opcode_format(const std::vector<std::vector<std::string>>& opcode_list) {

    static const std::unordered_map<std::string, int> OPCODE_FORMAT = {
        {"mov", 2},
        {"movi", 3},
        {"add", 2},
        {"sub", 2},
        {"shr", 2},
        {"shl", 2},
        {"mul", 2},  
        {"div", 2},
        {"je", 3},
        {"jg", 3},
        {"inc", 1},
        {"dec", 1},
        {"and", 2},
        {"or", 2},
        {"ng", 1},
        {"ret", 1},
        {"load_score", 1},
        {"get_id", 1},
        {"locate_nearest_k_chest", 2},
        {"locate_nearest_k_character", 2},
    };

    for (const auto& tokens : opcode_list) {
        if (tokens.empty()) {
            throw std::runtime_error("Empty instruction encountered");
        }

        const std::string& instr = tokens[0];

        auto it = OPCODE_FORMAT.find(instr);
        if (it == OPCODE_FORMAT.end()) {
            throw std::runtime_error("Unknown opcode: " + instr);
        }

        int expected_argc = it->second;
        int actual_argc = static_cast<int>(tokens.size()) - 1;

        if (expected_argc != actual_argc) {
            throw std::runtime_error("Opcode '" + instr + "' expects " 
                + std::to_string(expected_argc) + " arguments, got " 
                + std::to_string(actual_argc));
        }
    }
}

int execute_opcode(
    const std::vector<std::vector<std::string>>& instructions,
    const std::unordered_map<std::string, int>& labels,
    VM_Character* self,
    unsigned int* buffer,
    int buffer_size, // 100
    int team_id,
    int scores,
    VM_Chest** chests,      
    int chest_count,
    VM_Character** players,
    int player_count 
) {
    int pc = 0;
    auto start_time = std::chrono::steady_clock::now(); 

    auto read_mem = [&](int addr) -> unsigned int {
        if (addr < 0 || addr >= buffer_size) {
            throw std::runtime_error("Memory read out of bounds");
        }
        return buffer[addr];
    };

    auto write_mem = [&](int addr, unsigned int val) {
        if (addr < 0 || addr >= buffer_size) {
            throw std::runtime_error("Memory write out of bounds");
        }
        buffer[addr] = val;
    };

    auto is_constant = [](const std::string& token) {
        return !token.empty() && token[0] == '#';
    };
    
    auto parse_operand = [&](const std::string& token) -> unsigned int {
        if (is_constant(token)) {
            return std::stoi(token.substr(1));
        } else {
            int addr = std::stoi(token);
            return read_mem(addr);
        }
    };

    while (pc < (int)instructions.size()) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start_time).count();
        if (elapsed >= 3) {
            return 0;  
        }

        const auto& tokens = instructions[pc];
        const std::string& op = tokens[0];
        pc++;

        /*
        // mem1 = mem2
        mov <mem1> <mem2>
        mov <mem1> #<constant>

        // mem1 = mem2[mem3]
        movi <mem1> <mem2> <mem3>
        // mem1 += constant
        add <mem1> <mem2>
        add <mem1> #<constant>

        shr <mem1> <mem2>
        shr <mem1> #<constant>
        shl <mem1> <mem2>
        shl <mem1> #<constant>

        mul <mem1> <mem2>
        mul <mem1> #<constant>

        div <mem1> <mem2>
        div <mem1> #<constant>

        je <mem1> <mem2> $<label>
        je <mem1> #<constant> $<label>
        jg <mem1> <mem2> $<label>
        jg <mem1> #<constant> $<label>

        inc <mem1>
        dec <mem2>
        and <mem1> <mem2>
        and <mem1> #<mem2>
        or <mem1> <mem2>
        or <mem1> #<mem2>

        // mem = ~mem
        ng <mem1>

        ret <mem1> (end)
        ret #<constant> (end)

        // mem1 = score
        load_score <mem1>
        get_id <mem1>

        // mem2[0], mem2[1] = chest[k].xy
        locate_nearest_k_chest k <mem2>

        // mem2[0], mem2[1], mem2[2] = character[k].is_fork, character[k].xy
        locate_nearest_k_character k <mem2>


        ; Separate opcodes
        */

        if (op == "mov") {
            int dst = std::stoi(tokens[1]);
            unsigned int value = parse_operand(tokens[2]);
            write_mem(dst, value);
        }
        else if (op == "movi") {
            int dst = std::stoi(tokens[1]);
            int base = std::stoi(tokens[2]);
            int index = std::stoi(tokens[3]);
            unsigned int addr = read_mem(index) + base;
            unsigned int value = read_mem(addr);
            write_mem(dst, value);
        }
        else if (op == "add") {
            int dst = std::stoi(tokens[1]);
            unsigned int value = read_mem(dst) + parse_operand(tokens[2]);
            write_mem(dst, value);
        }
        else if (op == "sub") {
            int dst = std::stoi(tokens[1]);
            unsigned int value = read_mem(dst) - parse_operand(tokens[2]);
            write_mem(dst, value);
        }
        else if (op == "shr") {
            int dst = std::stoi(tokens[1]);
            unsigned int value = read_mem(dst) >> parse_operand(tokens[2]);
            write_mem(dst, value);
        }
        else if (op == "shl") {
            int dst = std::stoi(tokens[1]);
            unsigned int value = read_mem(dst) << parse_operand(tokens[2]);
            write_mem(dst, value);
        }
        else if (op == "mul") {
            int dst = std::stoi(tokens[1]);
            unsigned int value = read_mem(dst) * parse_operand(tokens[2]);
            write_mem(dst, value);
        }
        else if (op == "div") {
            int dst = std::stoi(tokens[1]);
            unsigned int divisor = parse_operand(tokens[2]);
            if (divisor == 0) return -1;
            write_mem(dst, read_mem(dst) / divisor);
        }
        else if (op == "je") {
            unsigned int lhs = parse_operand(tokens[1]);
            unsigned int rhs = parse_operand(tokens[2]);
            const std::string& label = tokens[3];
            if (lhs == rhs) {
                auto it = labels.find(label);
                if (it == labels.end()) throw std::runtime_error("Label not found: " + label);
                pc = it->second;
                continue;
            }
        }
        else if (op == "jg") {
            unsigned int lhs = parse_operand(tokens[1]);
            unsigned int rhs = parse_operand(tokens[2]);
            const std::string& label = tokens[3];
            if (lhs > rhs) {
                auto it = labels.find(label);
                if (it == labels.end()) throw std::runtime_error("Label not found: " + label);
                pc = it->second;
                continue;
            }
        }
        else if (op == "inc") {
            // inc <mem1>
            int dst = std::stoi(tokens[1]);
            write_mem(dst, read_mem(dst) + 1);
        }
        else if (op == "dec") {
            // dec <mem2>
            int dst = std::stoi(tokens[1]);
            write_mem(dst, read_mem(dst) - 1);
        }
        else if (op == "ng") {
            // ng <mem1>
            int a = std::stoi(tokens[1]);
            write_mem(a, ~read_mem(a));
        }
        else if (op == "and") {
            int dst = std::stoi(tokens[1]);
            write_mem(dst, read_mem(dst) & parse_operand(tokens[2]));
        }
        else if (op == "or") {
            int dst = std::stoi(tokens[1]);
            write_mem(dst, read_mem(dst) | parse_operand(tokens[2]));
        }
        else if (op == "ret") {
            unsigned int value = parse_operand(tokens[1]);
            return value;
        }
        else if (op == "load_score") {
            // load_score <mem1>
            int dst = std::stoi(tokens[1]);
            write_mem(dst, scores);
            
        }
        else if (op == "get_id") {
            // get_id <mem1>
            int dst = std::stoi(tokens[1]);
            write_mem(dst, team_id);
        }
        else if (op == "locate_nearest_k_chest") {
            unsigned int k = std::stoi(tokens[1]);
            int mem_base = std::stoi(tokens[2]);

            if (k >= (unsigned int)chest_count){
                write_mem(mem_base, -1);
                write_mem(mem_base + 1, -1);
                continue;
            }
        
            struct Entry {
                int x, y, dist, idx;
            };
        
            std::vector<Entry> chest_info;
            for (int i = 0; i < chest_count; ++i) {
                int dx = chests[i]->x - self->x;
                int dy = chests[i]->y - self->y;
                int dist = dx * dx + dy * dy;
                chest_info.push_back({chests[i]->x, chests[i]->y, dist, i});
            }
        
            std::sort(chest_info.begin(), chest_info.end(), [](const Entry& a, const Entry& b) {
                return a.dist < b.dist;
            });
        
            write_mem(mem_base, chest_info[k].x);
            write_mem(mem_base + 1, chest_info[k].y);
        }        
        else if (op == "locate_nearest_k_character") {
            unsigned int k = std::stoi(tokens[1]);
            int mem_base = std::stoi(tokens[2]);

            if (k >= (unsigned int)player_count) {
                write_mem(mem_base, -1);
                write_mem(mem_base + 1, -1);
                write_mem(mem_base + 2, -1);
                continue;
            }

            struct Entry {
                int x, y, dist, idx;
                Entry(int x_, int y_, int dist_, int idx_) : x(x_), y(y_), dist(dist_), idx(idx_) {}
            };
        
            std::vector<Entry> character_info;
            for (int i = 0; i < player_count; ++i) {
                int dx = players[i]->x - self->x;
                int dy = players[i]->y - self->y;
                int dist = dx * dx + dy * dy;
                character_info.emplace_back(players[i]->x, players[i]->y, dist, i);
            }
        
            std::sort(character_info.begin(), character_info.end(), [](const Entry& a, const Entry& b) {
                return a.dist < b.dist;
            });
        
            int idx = character_info[k].idx;
            write_mem(mem_base, players[idx]->is_fork ? 1 : 0);
            write_mem(mem_base + 1, players[idx]->x);
            write_mem(mem_base + 2, players[idx]->y);
        }
        else {
            throw std::runtime_error("Unknown instruction: " + op);
        }

    }

    return 0;
}


void debug_print_parsed(
    const std::vector<std::vector<std::string>>& instructions,
    const std::unordered_map<std::string, int>& labels
) {
    std::cout << "Parsed instructions:\n";
    for (size_t i = 0; i < instructions.size(); ++i) {
        std::cout << "  [" << i << "] ";
        for (const auto& tok : instructions[i]) {
            std::cout << tok << " ";
        }
        std::cout << "\n";
    }

    std::cout << "Parsed labels:\n";
    for (const auto& [label, pc] : labels) {
        std::cout << "  " << label << " => " << pc << "\n";
    }
}


extern "C" int vm_run(
    int team_id,
    const char opcode_cstr[],
    unsigned int* buffer,
    VM_Character** players, int player_count,
    VM_Chest** chests, int chest_count,
    int scores, VM_Character* self
) {
    
    std::vector<std::vector<std::string>> instructions;
    std::unordered_map<std::string, int> labels;

    int ret = 0;

    try {
        parse_opcode(opcode_cstr, instructions, labels);
        check_opcode_format(instructions);
    } catch (const std::runtime_error& e) {
        std::cerr << "[vm_run error] error: " << e.what() << "\n";
        return -1;
    }
    
    /*
    -1 vm_run error
    ops:
    0 stop
    1 up
    2 down
    3 left
    4 right
    5 interact
    6 attack
    7 fork

    others –> 0
    */
    try {
        ret = execute_opcode(instructions, labels, self, buffer, 100, team_id, scores, chests, chest_count, players, player_count);
    } catch (const std::runtime_error& e) {
        std::cerr << "[vm_run error] error: " << e.what() << "\n";
        ret = 0;
    }
    if (ret < -1 || ret > 7) ret = 0;


    return ret;
}



int main() {

    unsigned int buffer[100] = {};

    
    VM_Character *players[] = {
        new VM_Character{42, 4, false},
        new VM_Character{3, 4, true},
        new VM_Character{52, 4, false}
    };

    VM_Character *self[] = {
        new VM_Character{6, 4, false}
    }; // test is self
     
    int player_count = sizeof(players) / sizeof(players[0]);

    VM_Chest *chests[] = {
        new VM_Chest{4, 4},
        new VM_Chest{7, 4},
        new VM_Chest{8, 4}
    };
    int chest_count = sizeof(chests) / sizeof(chests[0]);

    const char* opcode = R"(
        add 0 #26;
        add 1 #456;
        sub 1 #430;
        add 1000, #100;
        locate_nearest_k_character 1 2;
        je 0 #1 label_2;
        label_1;
        ret #3;
        label_2;
        ret #1;

    )";
    int scores = 100;
    int team_id = 7;

    int ops = vm_run(team_id, opcode, buffer, players, player_count, chests, chest_count, scores, self[0]);

    std::cout << "vm_run returned: " << ops << "\n";
    for (int i = 0; i < 30; ++i) {
        std::cout << "buffer[" << i << "] = " << buffer[i] << "\n";
    }

    return 0;
}


