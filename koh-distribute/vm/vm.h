#pragma once

#ifdef __cplusplus
extern "C" {
#endif

struct VM_Character {
    int x, y;
    bool is_fork;
};

struct VM_Chest {
    int x, y;
};

enum {
    INS_MOV = 0,                 // mov <mem1> <mem2> or mov <mem1> #<constant>
    INS_MOVI,                    // movi <mem1> <mem2> <mem3>

    INS_ADD,                     // add <mem1> <mem2> or add <mem1> #<constant>
    INS_SHR,                     // shr <mem1> <mem2> or shr <mem1> #<constant>
    INS_SHL,                     // shl <mem1> <mem2> or shl <mem1> #<constant>
    INS_MUL,                     // mul <mem1> <mem2> or mul <mem1> #<constant>
    INS_DIV,                     // div <mem1> <mem2> or div <mem1> #<constant>

    INS_JE,                      // je <mem1> <mem2> $<label> or je <mem1> #<constant> $<label>
    INS_JG,                      // jg <mem1> <mem2> $<label> or jg <mem1> #<constant> $<label>

    INS_INC,                     // inc <mem1>
    INS_DEC,                     // dec <mem2>
    INS_AND,                     // and <mem1> <mem2> or and <mem1> #<constant>
    INS_OR,                      // or <mem1> <mem2> or or <mem1> #<constant>
    INS_NG,                      // ng <mem1>

    INS_RET,                     // ret <mem1> or ret #<constant>

    INS_LOAD_SCORE,             // load_score <mem1>
    INS_LOAD_LOC,               // load_loc <mem1>
    INS_LOAD_MAP,               // load_map <mem1> <mem2> <mem3>
    INS_GET_ID,                 // get_id <mem1>
    
    INS_LOCATE_NEAREST_CHEST,   // locate_nearest_k_chest k <mem2>
    INS_LOCATE_NEAREST_CHAR,    // locate_nearest_k_character k <mem2>

    INS_COUNT,                   // total number of instructions
    INS_INVALID = 0xff
};

/* opcode 1xxxxxxx -> const */
/* opcode 0xxxxxxx -> mem */
#define CONST_INST ((unsigned char)0x80)

struct Instruction{
    unsigned char opcode;
    unsigned char arg1;
    unsigned short arg3;
    unsigned int arg2;
};

bool vm_parse_script(
    const char script[],
    int *error_line
);

int vm_run(
    int team_id,
    const char script_cstr[],
    unsigned int* buffer,
    VM_Character** players, int player_count,
    VM_Chest** chests, int chest_count,
    unsigned char* map,
    int scores, VM_Character* self
);

#ifdef __cplusplus
}
#endif
