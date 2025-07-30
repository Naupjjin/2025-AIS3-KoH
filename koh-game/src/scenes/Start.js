// status: "running", "shutdown"
const RUNNING = "running";
const SHUTDOWN = "shutdown"
const HOST = "http://127.0.0.1:48763"

const tileSize = 32;
const scaleFactor = 0.8;
const displayTileSize = tileSize * scaleFactor;
const worldSize = 100 * displayTileSize;


export class Start extends Phaser.Scene {
    characters = {};
    chests = {};
    tiles_sprite = [];
    turn = 0;
    constructor() {
        super('Start');

        // 隨機生成地圖 (1 = wall, 0 = path)
        this.map = Array.from({ length: 200 }, () =>
            Array.from({ length: 200 }, () => 0)
        );
        this.status = SHUTDOWN;
        this.dragStartPoint = null;
        this.camStartPoint = null;
    }

    preload() {
        this.load.image('path', 'assets/path.png');
        this.load.image('wall', 'assets/wall.png');
        this.load.image('character', 'assets/character.png');
        this.load.image('chest', 'assets/chest.png');
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

    async start_game() {
        this.reset();
        await this.get_round_info();
        if (this.status == SHUTDOWN) {
            if (!this.start_event) {
                this.start_event = this.time.addEvent({
                    delay: 2000, // 毫秒
                    callback: this.start_game,
                    callbackScope: this,
                    loop: true
                });
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

        this.sync_character();
        this.sync_chest();
        this.sync_event = this.time.addEvent({
            delay: 3000, // 毫秒
            callback: () => {
                this.get_round_info();
                this.sync_character();
                this.sync_chest();
            },
            callbackScope: this,
            loop: true
        });
    }

    async sync_character() {
        let records = await this.get_character_records();
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
                            char.spawn_x * displayTileSize,
                            char.spawn_y * displayTileSize,
                            "character"
                        ).setScale(scaleFactor).setOrigin(0)
                    };
                } else {
                    this.characters[char.cid].opcodes = char.opcodes.split('').map(o => parseInt(o));
                    this.characters[char.cid].dead_turn = char.dead_turn;
                }
            }
        }
        console.log(records);
    }

    async sync_chest() {
        let records = await this.get_chest_records();
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
    async get_round_info() {
        console.log("get round info");
        try {
            let r = await fetch(`${HOST}/round_info`).then(r => r.json());
            if (r["status"]) {
                this.status = RUNNING;
            } else {
                if(this.status == RUNNING){
                    console.log("restart");
                    this.sync_event.remove();
                    this.status = SHUTDOWN;
                    this.start_game();
                }else{
                    this.status = SHUTDOWN;
                }
            }
        } catch {
        }
    }

    async get_map() {
        console.log("get map");
        try {
            let r = await fetch(`${HOST}/get_map`).then(r => r.json());
            return r;
        } catch {
        }
    }

    async get_character_records() {
        console.log("get_character_records");
        try {
            let r = await fetch(`${HOST}/get_character_records`).then(r => r.json());
            return r;
        } catch {
        }
    }

    async get_chest_records() {
        console.log("get_chest_records");
        try {
            let r = await fetch(`${HOST}/get_chest_records`).then(r => r.json());
            return r;
        } catch {
        }
    }

    check_movable(x, y) {
        return x >= 0 && x < 200 && y >= 0 && y < 200 && this.map[y][x] == 0;
    }
    update() {
        if (this.key.plus.isDown) {
            if (this.turn < 200) this.turn++;
            console.log(this.turn);
        } else if (this.key.minus.isDown) {
            if (this.turn > 0) this.turn--;
            console.log(this.turn);
        }
        for (let character of Object.values(this.characters)) {
            let x = character.spawn_x;
            let y = character.spawn_y;
            for (let i = character.spawn_turn; i < this.turn && this.turn < character.opcodes.length; i++) {
                switch (character.opcodes[i]) {
                    // up
                    case 1:
                        if (this.check_movable(x, y - 1)) y--;
                    // down
                    case 2:
                        if (this.check_movable(x, y + 1)) y++;
                    // left
                    case 3:
                        if (this.check_movable(x - 1, y)) x--;
                    // right
                    case 4:
                        if (this.check_movable(x + 1, y)) x++;
                }
            }
            if (this.turn < character.spawn_turn || (character.dead_turn != -1 && this.turn > character.dead_turn)) {
                character.sprite.setVisible(false);
            } else {
                character.sprite.setVisible(true);
            }
            character.sprite
                .setPosition(x * displayTileSize, y * displayTileSize);
        }
        for (let chest of Object.values(this.chests)) {
            if (this.turn < chest.spawn_turn || (chest.opened_turn != -1 && this.turn > chest.opened_turn)) {
                chest.sprite.setVisible(false);
            } else {
                chest.sprite.setVisible(true);
            }
        }
    }
}
