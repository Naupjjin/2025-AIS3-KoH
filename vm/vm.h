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

int vm_run(
    int team_id,
    const char opcode_cstr[],
    unsigned int* buffer,
    VM_Character** players, int player_count,
    VM_Chest** chests, int chest_count,
    int scores, VM_Character* self
);

#ifdef __cplusplus
}
#endif
