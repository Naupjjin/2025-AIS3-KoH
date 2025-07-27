#include <string>
#include <stdio.h>

struct VM_Character
{
    int x, y;
    bool is_fork;
};

struct VM_Chest
{
    int x, y;
};

extern "C" int vm_run(
    int team_id,
    const char opcode_cstr[],
    unsigned int *buffer,
    VM_Character **players, int player_count,
    VM_Chest **chests, int chest_count)
{
    printf("%d\n", team_id);
    for (int i = 0; i < player_count; i++)
    {
        VM_Character *player = players[i];
        printf("%d %d\n", player->x, player->y);
    }
    return 0;
}