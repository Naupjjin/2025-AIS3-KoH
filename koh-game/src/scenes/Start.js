// status: "running", "shutdown"
const RUNNING = "running";
const SHUTDOWN = "shutdown"
const HOST = "http://127.0.0.1:48763"

const tileSize = 32;
const scaleFactor = 0.3;
const displayTileSize = tileSize * scaleFactor;

export class Start extends Phaser.Scene {
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
    }

    create_map() {
        for (let y = 0; y < this.map.length; y++) {
            for (let x = 0; x < this.map[y].length; x++) {
                const key = this.map[y][x] === 1 ? 'wall' : 'path';
                const tile = this.add.image(x * displayTileSize, y * displayTileSize, key);
                tile.setOrigin(0);
                tile.setScale(scaleFactor);
            }
        }
    }


    create() {

        this.create_map();

        const worldSize = 200 * displayTileSize;
        this.cameras.main.setBounds(0, 0, worldSize, worldSize);

        // 拖曳 camera
        this.input.on('pointerdown', (pointer) => {
            this.dragStartPoint = new Phaser.Math.Vector2(pointer.x, pointer.y);
            this.camStartPoint = new Phaser.Math.Vector2(this.cameras.main.scrollX, this.cameras.main.scrollY);
        });

        this.input.on('pointermove', (pointer) => {
            if (!pointer.isDown || !this.dragStartPoint || !this.camStartPoint) return;

            const dragX = pointer.x - this.dragStartPoint.x;
            const dragY = pointer.y - this.dragStartPoint.y;

            this.cameras.main.scrollX = this.camStartPoint.x - dragX;
            this.cameras.main.scrollY = this.camStartPoint.y - dragY;
        });

        this.input.on('pointerup', () => {
            this.dragStartPoint = null;
            this.camStartPoint = null;
        });
        this.start_game();

    }
    start_event = null;
    sync_event = null;

    async start_game() {

        await this.get_round_info();
        if (this.status == SHUTDOWN && !this.start_event) {
            this.start_event = this.time.addEvent({
                delay: 2000, // 毫秒
                callback: this.start_game,
                callbackScope: this,
                loop: true
            });
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
        this.sync_event = this.time.addEvent({
            delay: 2000, // 毫秒
            callback: this.sync_character,
            callbackScope: this,
            loop: true
        });
    }

    async sync_character() {
        let records = await this.get_character_records();
        console.log(records);
    }
    async get_round_info() {
        try {
            let r = await fetch(`${HOST}/round_info`).then(r => r.json());
            r["status"] = true;
            if (r["status"]) {
                this.status = RUNNING;
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

    async update() {

    }
}
