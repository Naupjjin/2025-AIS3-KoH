import random
import os

def generate_map(width=50, height=50, wall_ratio=0.12):
    grid = [['.' for _ in range(width)] for _ in range(height)]
    wall_count = int(width * height * wall_ratio)
    added = 0

    while added < wall_count:
        cluster_len = random.randint(5, 20)
        thick = 1 if random.random() < 0.8 else random.randint(2, 4)
        horizontal = random.choice([True, False])
        x = random.randint(0, width - (cluster_len if horizontal else thick))
        y = random.randint(0, height - (thick if horizontal else cluster_len))

        for dy in range(thick):
            for dx in range(cluster_len):
                cx = x + dx if horizontal else x + dy
                cy = y + dy if horizontal else y + dx
                if 0 <= cx < width and 0 <= cy < height and grid[cy][cx] == '.':
                    grid[cy][cx] = '#'
                    added += 1
                    if added >= wall_count:
                        break
            if added >= wall_count:
                break

    return grid

for i in range(1, 6):
    data = generate_map()
    with open(f"map_{i:02}.txt", "w") as f:
        f.write("\n".join("".join(row) for row in data))
