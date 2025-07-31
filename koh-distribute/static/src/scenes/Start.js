// status: "running", "shutdown"
const RUNNING = "running";
const SHUTDOWN = "shutdown"
const HOST = ""

const tileSize = 32;
const scaleFactor = 0.8;
const displayTileSize = tileSize * scaleFactor;

export class Start extends Phaser.Scene {
    characters = {};
    chests = {};
    tiles_sprite = [];
    scores = { "1": [], "2": [], "3": [], "4": [], "5": [], "6": [], "7": [], "8": [], "9": [], "10": [], };
    turn = 0;
    scoreTextMap = {}; last_track = 0;
    turn_text = null;
    elasped_time = 0;
    pixel_textures = [];
    constructor() {
        super('Start');

        // 隨機生成地圖 (1 = wall, 0 = path)
        this.map = Array.from({ length: 50 }, () =>
            Array.from({ length: 50 }, () => 0)
        );
        this.status = RUNNING;
    }

    preload() {
        this.load.image('path', 'static/assets/path.png');
        this.load.image('wall', 'static/assets/wall.png');
        for (let i = 1; i <= 10; i++) {
            this.pixel_textures.push(`character-${i}`)
            this.load.image(`character-${i}`, `static/assets/character-${i}.png`);
        }
        this.pixel_textures.push("chest")
        this.load.image('chest', 'static/assets/chest.png');
    }

    create_map() {
        for (let sprite of this.tiles_sprite) {
            sprite.destroy();
        }
        this.tiles_sprite = [];
        for (let y = 0; y < this.map.length; y++) {
            for (let x = 0; x < this.map[y].length; x++) {
                const key = this.map[y][x] === 1 ? 'wall' : 'path';
                const tile = this.add.image(x * displayTileSize, y * displayTileSize, key);
                tile.setOrigin(0);
                tile.setScale(scaleFactor);
                this.tiles_sprite.push(tile);
            }
        }
    }

    create() {

        this.create_map();

        this.key = this.input.keyboard.addKeys({
            plus: Phaser.Input.Keyboard.KeyCodes.PLUS,
            minus: Phaser.Input.Keyboard.KeyCodes.MINUS,
            shift: Phaser.Input.Keyboard.KeyCodes.SHIFT,
            next: Phaser.Input.Keyboard.KeyCodes.ONE,
            all: Phaser.Input.Keyboard.KeyCodes.TWO
        });

        this.start_game();
    }
    start_event = null;
    sync_event = null;

    reset() {
        for (let chest of Object.values(this.chests)) {
            chest.sprite.destroy();
        }
        for (let character of Object.values(this.characters)) {
            character.sprite.destroy();
        }
        this.characters = {};
        this.chests = {};
    }

    load_score() {
        let startX = 20;
        let startY = 20;
        const color = [
            "#630c0c",
            "#3b5528",
            "#b9983b",
            "#4180b9",
            "#843693",
            "#63c4c9",
            "#c2d84c",
            "#e88a45",
            "#c92067",
            "#20c955"
        ]
        for (let id of Object.keys(this.scores)) {
            let s = this.turn < this.scores[id].length ? this.scores[id][this.turn] : 0;
            if (!this.scoreTextMap[id]) {
                const text = this.add.text(startX, startY, `Player ${id}: ${s}`, {
                    fontSize: '32px',
                    color: color[id - 1]
                }).setDepth(1000).setAlpha(0.4).setBackgroundColor("#000000");
                this.scoreTextMap[id] = text;
            } else {
                this.scoreTextMap[id].setText(`Player ${id}: ${s}`);
            }
            startY += 32;
        }
        if (!this.turn_text) {
            this.turn_text = this.add.text(startX, startY, `Turn ${this.turn}`, {
                fontSize: '32px',
                color: "#ffffff"
            }).setDepth(1000).setAlpha(0.4).setBackgroundColor("#000000");
        }
    }

    restart() {
        console.log("restart");
        if (this.sync_event) {
            this.sync_event.remove();
        }
        this.status = SHUTDOWN;
        this.start_event = this.time.addEvent({
            delay: 1000, // 毫秒
            callback: this.start_game,
            callbackScope: this,
            loop: true
        });
    }

    async start_game() {
        this.reset();
        let r = await fetch(`${HOST}/api/round_info`).then(r => r.json());
        if (r["status"] == "running" && !r["expired"]) {
            this.status = RUNNING;
        } else {
            if (this.status == RUNNING) {
                this.restart();
            } else {
                this.status = SHUTDOWN;
            }
            return;
        }

        if (this.start_event) {
            this.start_event.remove();
            this.start_event = null;
        }
        console.log(this.status)
        this.map = await this.get_map();
        this.create_map();
        this.sync_score();
        this.load_score();
        this.sync_character();
        this.sync_chest();
        this.sync_event = this.time.addEvent({
            delay: 1000, // 毫秒
            callback: async () => {
                let r = await fetch(`${HOST}/api/round_info`).then(r => r.json());
                if (r["status"] != "running" || r["expired"]) {
                    this.restart();
                    return;
                }
                if (!r["simulate_finished"]) {
                    this.sync_character();
                    this.sync_chest();
                    this.sync_score();
                }
            },
            callbackScope: this,
            loop: true
        });
    }

    async sync_character() {
        console.log("sync character");
        let records = await fetch(`${HOST}/get_character_records`).then(r => r.json());
        let i = 1;
        for (const [player, charList] of Object.entries(records)) {
            for (const char of charList) {
                if (!this.characters[char.cid]) {
                    this.characters[char.cid] = {
                        player: player,
                        spawn_x: char.spawn_x,
                        spawn_y: char.spawn_y,
                        opcodes: char.opcodes.split('').map(o => parseInt(o)),
                        spawn_turn: char.spawn_turn,
                        dead_turn: char.dead_turn,
                        sprite: this.add.image(
                            char.spawn_x * displayTileSize - displayTileSize / 2,
                            char.spawn_y * displayTileSize - displayTileSize,
                            `character-${i}`
                        ).setScale(scaleFactor).setOrigin(0)
                    };
                } else {
                    this.characters[char.cid].opcodes = char.opcodes.split('').map(o => parseInt(o));
                    this.characters[char.cid].dead_turn = char.dead_turn;
                }
            }
            i++;
        }
        console.log(records);
    }

    async sync_chest() {
        console.log("sync chest");
        let records = await fetch(`${HOST}/get_chest_records`).then(r => r.json());
        for (const chest of records) {
            if (!this.chests[chest.cid]) {
                this.chests[chest.cid] = {
                    cid: chest.cid,
                    x: chest.x,
                    y: chest.y,
                    spawn_turn: chest.spawn_turn,
                    opened_turn: chest.opened_turn,
                    sprite: this.add.image(
                        chest.x * displayTileSize,
                        chest.y * displayTileSize,
                        "chest"
                    ).setScale(scaleFactor).setOrigin(0)
                };
            } else {
                this.chests[chest.cid].opened_turn = chest.opened_turn;
            }
        }
        console.log(records);
    }
    async sync_score() {
        console.log("sync score");
        let records = await fetch(`${HOST}/get_score_records`).then(r => r.json());
        this.scores = records;
        console.log(this.scores);
    }

    async get_map() {
        console.log("get map");
        try {
            let r = await fetch(`${HOST}/get_map`).then(r => r.json());
            return r;
        } catch {
        }
    }


    check_movable(x, y) {
        return x >= 0 && x < 50 && y >= 0 && y < 50 && this.map[y][x] == 0;
    }
    cooldown = 100;
    last_pressed = 0;
    update(time) {
        if (this.key.plus.isDown) {
            if (time - this.last_pressed > this.cooldown) {
                if (this.key.shift.isDown) {
                    this.turn = Math.min(200, this.turn + 10);
                } else {
                    this.turn = Math.min(200, this.turn + 1);
                }
                this.last_pressed = time
            }
        } else if (this.key.minus.isDown) {
            if (time - this.last_pressed > this.cooldown) {
                if (this.key.shift.isDown) {
                    this.turn = Math.max(0, this.turn - 10);
                } else {
                    this.turn = Math.max(0, this.turn - 1);
                }
                this.last_pressed = time
            }
        }
        if (Phaser.Input.Keyboard.JustDown(this.key.next)) {
            let keys = Object.keys(this.characters);
            for (let tex of this.pixel_textures){
                this.textures.get(tex).setFilter(Phaser.Textures.FilterMode.NEAREST);
            }
            if (this.last_track > keys.length) {
                this.last_track = 0
            }
            let sprite = this.characters[keys[this.last_track]].sprite;
            while (!sprite.visible) {
                this.last_track++;
                this.last_track %= keys.length;
                sprite = this.characters[keys[this.last_track]].sprite;
            }
            this.cameras.main.startFollow(sprite, false, 0.1, 0.1,
                -displayTileSize / 2, -displayTileSize);  // 追蹤角色
            this.cameras.main.zoomTo(5, 500);
            this.last_track++;
            this.last_track %= keys.length;

        } else if (this.key.all.isDown) {
            for (let tex of this.pixel_textures){
                this.textures.get(tex).setFilter(Phaser.Textures.FilterMode.LINEAR);
            }
            this.cameras.main.stopFollow();
            this.cameras.main.pan(640, 640, 500);
            this.cameras.main.zoomTo(1, 500);
        }

        for (let character of Object.values(this.characters)) {
            let x = character.spawn_x;
            let y = character.spawn_y;
            for (let i = character.spawn_turn; i < this.turn && this.turn < character.opcodes.length; i++) {
                switch (character.opcodes[i]) {
                    // up
                    case 1:
                        if (this.check_movable(x, y - 1)) y--;
                        break
                    // down
                    case 2:
                        if (this.check_movable(x, y + 1)) y++;
                        break
                    // left
                    case 3:
                        if (this.check_movable(x - 1, y)) x--;
                        break
                    // right
                    case 4:
                        if (this.check_movable(x + 1, y)) x++;
                        break
                }
            }
            if (this.turn < character.spawn_turn || (character.dead_turn != -1 && this.turn > character.dead_turn)) {
                character.sprite.setVisible(false);
            } else {
                character.sprite.setVisible(true);
            }
            character.sprite
                .setPosition(
                    x * displayTileSize - displayTileSize / 2,
                    y * displayTileSize - displayTileSize);
        }
        for (let chest of Object.values(this.chests)) {
            if (this.turn < chest.spawn_turn || (chest.opened_turn != -1 && this.turn > chest.opened_turn)) {
                chest.sprite.setVisible(false);
            } else {
                chest.sprite.setVisible(true);
            }
        }
        this.load_score();

        if (this.turn_text) {
            this.turn_text.setText(`Turn ${this.turn}`); `Turn ${this.turn}`
        }

    }
}
