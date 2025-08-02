#include "vm.h"
#include <vector>
#include <string>
#include <sstream>
#include <unordered_map>
#include <cstring>
#include <iostream>
#include <algorithm>
#include <chrono>
#include <charconv>

#define MAP_SIZE (50)

static const std::unordered_map<std::string_view, unsigned char> opcode_map = {
    {"mov", INS_MOV},
    {"movi", INS_MOVI},
    {"add", INS_ADD},
    {"shr", INS_SHR},
    {"shl", INS_SHL},
    {"mul", INS_MUL},
    {"div", INS_DIV},
    {"je", INS_JE},
    {"jg", INS_JG},
    {"inc", INS_INC},
    {"dec", INS_DEC},
    {"and", INS_AND},
    {"or", INS_OR},
    {"ng", INS_NG},
    {"ret", INS_RET},
    {"load_score", INS_LOAD_SCORE},
    {"load_loc", INS_LOAD_LOC},
    {"load_map", INS_LOAD_MAP},
    {"get_id", INS_GET_ID},
    {"locate_nearest_k_chest", INS_LOCATE_NEAREST_CHEST},
    {"locate_nearest_k_character", INS_LOCATE_NEAREST_CHAR},
};

struct stoi_result
{
    bool success = false;
    int value = 0;
    operator bool() const { return success; }
};

static stoi_result stoi(std::string_view s, int base = 10)
{
    int result_num;
    auto result =
        std::from_chars(s.data(), s.data() + s.size(), result_num, base);
    if (result.ec == std::errc::invalid_argument)
    {
        return {};
    }
    return stoi_result{.success = true, .value = result_num};
}

unsigned int parse_immediate(std::string_view token)
{
    if (token.size() >= 2 && token[0] == '#')
    {
        return stoi(token.substr(1)).value;
    }
    return 0;
}

std::vector<std::string_view> split_tokens(std::string_view line)
{
    std::vector<std::string_view> tokens;
    size_t start = 0;
    while (start < line.size())
    {
        while (start < line.size() && isspace(line[start]))
            start++;
        size_t end = start;
        while (end < line.size() && !isspace(line[end]))
            end++;
        if (end > start)
            tokens.emplace_back(line.substr(start, end - start));
        start = end;
    }
    return tokens;
}

Instruction parse_full_instruction(std::string_view line, std::unordered_map<std::string_view, unsigned short> &symtab)
{
    Instruction inst{INS_INVALID, 0, 0, 0};

    auto tokens = split_tokens(line);
    if (tokens.empty())
        return inst;

    auto it = opcode_map.find(tokens[0]);
    if (it == opcode_map.end())
        return inst;
    inst.opcode = it->second;

    auto get_num = [](std::string_view tok, char prefix) -> stoi_result
    {
        if (tok.size() >= 2 && tok[0] == prefix)
            return stoi(tok.substr(1));
        return {};
    };

    auto get_raw_num = [](std::string_view tok) -> stoi_result
    {
        return stoi(tok);
    };

#define PARSE_OR_FAIL(VAR, EXPR)                             \
    auto VAR = EXPR;                                         \
    do                                                       \
    {                                                        \
        if (!VAR)                                            \
        {                                                    \
            return {INS_INVALID, 0, 0, 0};                   \
        }                                                    \
    } while (0)
    switch (inst.opcode)
    {
    case INS_INC:
    case INS_DEC:
    case INS_NG:
    case INS_LOAD_SCORE:
    case INS_LOAD_LOC:
    case INS_GET_ID:
    {
        if (tokens.size() < 2)
            return inst;
        PARSE_OR_FAIL(r1, get_raw_num(tokens[1]));
        inst.arg1 = r1.value;
        break;
    }
    case INS_RET:
    {
        if (tokens.size() < 2)
            return inst;
        if (tokens[1][0] == '#')
        {
            PARSE_OR_FAIL(imm, get_num(tokens[1], '#'));
            inst.arg2 = imm.value;
            inst.opcode |= CONST_INST;
        }
        else
        {
            PARSE_OR_FAIL(r1, get_raw_num(tokens[1]));
            inst.arg2 = r1.value;
        }
        break;
    }
    case INS_MOV:
    case INS_ADD:
    case INS_SHR:
    case INS_SHL:
    case INS_MUL:
    case INS_DIV:
    case INS_AND:
    case INS_OR:
    {
        if (tokens.size() < 3)
            return inst;
        PARSE_OR_FAIL(r1, get_raw_num(tokens[1]));
        inst.arg1 = r1.value;

        if (tokens[2][0] == '#')
        {
            PARSE_OR_FAIL(imm, get_num(tokens[2], '#'));
            inst.arg2 = imm.value;
            inst.opcode |= CONST_INST;
        }
        else
        {
            PARSE_OR_FAIL(r2, get_raw_num(tokens[2]));
            inst.arg2 = r2.value;
        }
        break;
    }
    case INS_MOVI:
    {
        if (tokens.size() < 3)
            return inst;
        PARSE_OR_FAIL(a1, get_raw_num(tokens[1]));
        PARSE_OR_FAIL(a2, get_raw_num(tokens[2]));
        inst.arg1 = a1.value;
        inst.arg2 = a2.value;
        break;
    }
    case INS_JE:
    case INS_JG:
    {
        if (tokens.size() < 4)
            return inst;
        PARSE_OR_FAIL(r1, get_raw_num(tokens[1]));
        inst.arg1 = r1.value;

        if (tokens[2][0] == '#')
        {
            PARSE_OR_FAIL(imm, get_num(tokens[2], '#'));
            inst.arg2 = imm.value;
            inst.opcode |= CONST_INST;
        }
        else
        {
            PARSE_OR_FAIL(r2, get_raw_num(tokens[2]));
            inst.arg2 = r2.value;
        }
        auto iter = symtab.find(tokens[3]);
        if (iter == symtab.end())
        {
            return {INS_INVALID, 0, 0, 0};
        }
        inst.arg3 = iter->second;
        break;
    }
    case INS_LOCATE_NEAREST_CHEST:
    case INS_LOCATE_NEAREST_CHAR:
    {
        if (tokens.size() < 3)
            return inst;
        PARSE_OR_FAIL(rdst, get_raw_num(tokens[1]));
        if (tokens[2][0] == '#')
        {
            PARSE_OR_FAIL(k, get_num(tokens[2], '#'));
            inst.opcode |= CONST_INST;
            inst.arg2 = k.value;
        }
        else
        {
            PARSE_OR_FAIL(k, get_raw_num(tokens[2]));
            inst.arg2 = k.value;
        }
        inst.arg1 = rdst.value;
        break;
    }
    case INS_LOAD_MAP:
    {
        if (tokens.size() < 4)
            return inst;
        PARSE_OR_FAIL(rdst, get_raw_num(tokens[1]));
        PARSE_OR_FAIL(x, get_raw_num(tokens[2]));
        PARSE_OR_FAIL(y, get_raw_num(tokens[3]));
        inst.arg1 = rdst.value;
        inst.arg2 = x.value;
        inst.arg3 = y.value;
        break;
    }
    default:
        return inst;
    }

    return inst;
}

bool parse_opcode(
    const std::string_view opcode_str,
    std::vector<Instruction> &instructions, int &error_line)
{
    std::unordered_map<std::string_view, unsigned short> labels;
    {
        unsigned short pc = 0;
        size_t line_start = 0;

        while (line_start < opcode_str.size())
        {
            size_t line_end = opcode_str.find('\n', line_start);
            if (line_end == std::string_view::npos)
                line_end = opcode_str.size();

            std::string_view line = opcode_str.substr(line_start, line_end - line_start);

            // Trim 前後空白
            size_t start = line.find_first_not_of(" \t\r");
            if (start == std::string_view::npos)
            {
                line_start = line_end + 1;
                continue;
            }
            size_t end = line.find_last_not_of(" \t\r");
            line = line.substr(start, end - start + 1);

            if (line.empty())
            {
                line_start = line_end + 1;
                continue;
            }

            // 檢查是否為 label
            size_t colon = line.find(':');
            bool is_comment = line.substr(0, 2) == "//";
            if (colon != std::string_view::npos && !is_comment)
            {
                std::string_view label = line.substr(0, colon);

                // 去除 label 前後空白
                size_t lstart = label.find_first_not_of(" \t\r");
                size_t lend = label.find_last_not_of(" \t\r");
                if (lstart != std::string_view::npos && lend != std::string_view::npos)
                {
                    label = label.substr(lstart, lend - lstart + 1);
                    labels[label] = pc;
                }
            }
            else if (!is_comment)
            {
                pc++; // 只有非 label 行才算一條實際指令
            }

            line_start = line_end + 1;
        }
    }
    {
        int line_parsed = 0;
        size_t line_start = 0;

        while (line_start < opcode_str.size())
        {
            line_parsed++;
            size_t line_end = opcode_str.find('\n', line_start);
            if (line_end == std::string_view::npos)
                line_end = opcode_str.size();

            std::string_view line = opcode_str.substr(line_start, line_end - line_start);

            // Trim 前後空白
            size_t start = line.find_first_not_of(" \t\r");
            if (start == std::string_view::npos)
            {
                line_start = line_end + 1;
                continue;
            }
            size_t end = line.find_last_not_of(" \t\r");
            line = line.substr(start, end - start + 1);

            if (line.empty())
            {
                line_start = line_end + 1;
                continue;
            }

            // 檢查是否為 label
            size_t colon = line.find(':');
            bool is_comment = line.substr(0, 2) == "//";
            if (colon != std::string_view::npos || is_comment)
            {
                line_start = line_end + 1;
                continue;
            }
            auto inst = parse_full_instruction(line, labels);
            if (inst.opcode == INS_INVALID)
            {

                error_line = line_parsed;
                return false;
            }
            instructions.push_back(inst);

            line_start = line_end + 1;
        }
    }
    return true;
}

int execute_opcode(
    const std::vector<Instruction> &instructions,
    const std::unordered_map<std::string, int> &labels,
    VM_Character *self,
    unsigned int *buffer,
    int buffer_size, // 100
    int team_id,
    int scores,
    VM_Chest **chests,
    int chest_count,
    unsigned char *map,
    VM_Character **players,
    int player_count)
{
    int pc = 0;
    auto start_time = std::chrono::steady_clock::now();

    int chest_call_count = 0;
    int character_call_count = 0;
    int CHEST_CHARACTER_CALL_LIMIT = 5;

    auto read_mem = [&](int addr) -> unsigned int
    {
        if (addr < 0 || addr >= buffer_size)
        {
            throw std::runtime_error("Memory read out of bounds");
        }
        return buffer[addr];
    };

    auto write_mem = [&](int addr, unsigned int val)
    {
        if (addr < 0 || addr >= buffer_size)
        {
            throw std::runtime_error("Memory write out of bounds");
        }
        buffer[addr] = val;
    };

    auto is_constant = [](const std::string &token)
    {
        return !token.empty() && token[0] == '#';
    };

    auto parse_operand = [&](const std::string &token) -> unsigned int
    {
        if (is_constant(token))
        {
            return std::stoi(token.substr(1));
        }
        else
        {
            int addr = std::stoi(token);
            return read_mem(addr);
        }
    };
    while (pc < (int)instructions.size())
    {

        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - start_time).count();
        if (elapsed >= 250)
        {
            return 0;
        }

        const auto &inst = instructions[pc++];

        auto opcode = inst.opcode & ~CONST_INST;
        auto is_const = inst.opcode & CONST_INST;
        auto r = is_const ? inst.arg2 : read_mem(inst.arg2);
        switch (opcode)
        {
        case INS_MOV:
            write_mem(inst.arg1, r);
            break;
        case INS_MOVI:
        {
            unsigned int dst = read_mem(inst.arg1);
            unsigned int src = read_mem(inst.arg2);
            write_mem(read_mem(dst), read_mem(src));
            break;
        }
        case INS_ADD:
            write_mem(inst.arg1, read_mem(inst.arg1) + r);
            break;
        case INS_SHR:
            write_mem(inst.arg1, read_mem(inst.arg1) >> r);
            break;
        case INS_SHL:
            write_mem(inst.arg1, read_mem(inst.arg1) << r);
            break;
        case INS_MUL:
            write_mem(inst.arg1, read_mem(inst.arg1) * r);
            break;
        case INS_DIV:
        {
            unsigned int divisor = r;
            if (divisor == 0)
                return -1;
            write_mem(inst.arg1, read_mem(inst.arg1) / divisor);
            break;
        }
        case INS_JE:
            if (read_mem(inst.arg1) == r)
            {
                pc = inst.arg3;
            }
            break;
        case INS_JG:
            if (read_mem(inst.arg1) > r)
            {
                pc = inst.arg3;
            }
            break;
        case INS_INC:
            write_mem(inst.arg1, read_mem(inst.arg1) + 1);
            break;
        case INS_DEC:
            write_mem(inst.arg1, read_mem(inst.arg1) - 1);
            break;
        case INS_AND:
            write_mem(inst.arg1, read_mem(inst.arg1) & r);
            break;
        case INS_OR:
            write_mem(inst.arg1, read_mem(inst.arg1) | r);
            break;
        case INS_NG:
            write_mem(inst.arg1, ~read_mem(inst.arg1));
            break;
        case INS_RET:
            return r;
        case INS_LOAD_SCORE:
            write_mem(inst.arg1, scores);
            break;
        case INS_LOAD_LOC:
            write_mem(inst.arg1, self->x);
            write_mem(inst.arg1 + 1, self->y);
            break;
        case INS_LOAD_MAP:
        {
            auto x = read_mem(inst.arg2);
            auto y = read_mem(inst.arg3);
            if (x >= 0 && x < MAP_SIZE && y >= 0 && y < MAP_SIZE){
                write_mem(inst.arg1, map[y * MAP_SIZE + x]);
            }else{
                write_mem(inst.arg1, 1);
            }
            break;
        }

        case INS_GET_ID:
        {
            write_mem(inst.arg1, team_id);
            break;
        }
        case INS_LOCATE_NEAREST_CHEST:
        {
            int mem_base = inst.arg1;
            unsigned int k = r;
            if (k >= (unsigned int)chest_count || chest_call_count + character_call_count >= CHEST_CHARACTER_CALL_LIMIT)
            {
                write_mem(mem_base, -1);
                write_mem(mem_base + 1, -1);
                break;
            }

            chest_call_count++;
            struct Entry
            {
                int x, y, dist, idx;
            };
            std::vector<Entry> chest_info;
            for (int i = 0; i < chest_count; ++i)
            {
                int dx = chests[i]->x - self->x;
                int dy = chests[i]->y - self->y;
                int dist = dx * dx + dy * dy;
                chest_info.push_back({chests[i]->x, chests[i]->y, dist, i});
            }
            std::sort(chest_info.begin(), chest_info.end(), [](auto &a, auto &b)
                      { return a.dist < b.dist; });
            write_mem(mem_base, chest_info[k].x);
            write_mem(mem_base + 1, chest_info[k].y);
            break;
        }
        case INS_LOCATE_NEAREST_CHAR:
        {
            int mem_base = inst.arg1;
            unsigned int k = r;
            if (k >= (unsigned int)player_count || chest_call_count + character_call_count >= CHEST_CHARACTER_CALL_LIMIT)
            {
                write_mem(mem_base, -1);
                write_mem(mem_base + 1, -1);
                write_mem(mem_base + 2, -1);
                break;
            }
            character_call_count++;
            struct Entry
            {
                int x, y, dist, idx;
                Entry(int x, int y, int d, int i) : x(x), y(y), dist(d), idx(i) {}
            };
            std::vector<Entry> character_info;
            for (int i = 0; i < player_count; ++i)
            {
                int dx = players[i]->x - self->x;
                int dy = players[i]->y - self->y;
                int dist = dx * dx + dy * dy;
                character_info.emplace_back(players[i]->x, players[i]->y, dist, i);
            }
            std::sort(character_info.begin(), character_info.end(), [](auto &a, auto &b)
                      { return a.dist < b.dist; });
            int idx = character_info[k].idx;
            write_mem(mem_base, players[idx]->is_fork ? 1 : 0);
            write_mem(mem_base + 1, players[idx]->x);
            write_mem(mem_base + 2, players[idx]->y);
            break;
        }
        default:
            throw std::runtime_error("Unknown instruction opcode");
        }
    }

    return 0;
}

void debug_print_parsed(
    const std::vector<std::vector<std::string>> &instructions,
    const std::unordered_map<std::string, int> &labels)
{
    std::cout << "Parsed instructions:\n";
    for (size_t i = 0; i < instructions.size(); ++i)
    {
        std::cout << "  [" << i << "] ";
        for (const auto &tok : instructions[i])
        {
            std::cout << tok << " ";
        }
        std::cout << "\n";
    }

    std::cout << "Parsed labels:\n";
    for (const auto &[label, pc] : labels)
    {
        std::cout << "  " << label << " => " << pc << "\n";
    }
}

extern "C" bool vm_parse_script(
    const char script[], int *error_line)
{
    std::vector<Instruction> instructions;
    return parse_opcode(std::string(script), instructions, *error_line);
}

extern "C" int vm_run(
    int team_id,
    const char opcode_cstr[],
    unsigned int *buffer,
    VM_Character **players, int player_count,
    VM_Chest **chests, int chest_count,
    unsigned char *map,
    int scores, VM_Character *self)
{

    std::vector<Instruction> instructions;
    std::unordered_map<std::string, int> labels;

    int ret = 0;
    int error_line = 0;
    try
    {
        parse_opcode(opcode_cstr, instructions, error_line);
        // check_opcode_format(instructions);
    }
    catch (const std::runtime_error &e)
    {
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
    try
    {
        ret = execute_opcode(instructions, labels, self, buffer, 100, team_id, scores, chests, chest_count, map, players, player_count);
    }
    catch (const std::runtime_error &e)
    {
        std::cerr << "[vm_run error] error: " << e.what() << "\n";
        ret = 0;
    }
    if (ret < -1 || ret > 7)
        ret = 0;

    return ret;
}
