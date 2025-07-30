// status: "running", "shutdown"
const RUNNING = "running";
const SHUTDOWN = "shutdown"
const HOST = "http://127.0.0.1:48763"

export class Start extends Phaser.Scene {
    constructor() {
        super('Start');

        // 隨機生成地圖 (1 = wall, 0 = path)
        this.map = Array.from({ length: 200 }, () =>
            Array.from({ length: 200 }, () => Math.random() > 0.8 ? 1 : 0)
        );
        this.status = SHUTDOWN;
        this.dragStartPoint = null;
        this.camStartPoint = null;
    }

    preload() {
        this.load.image('path', 'assets/path.png');
        this.load.image('wall', 'assets/wall.png');
    }


    create() {
        const tileSize = 32;
        const scaleFactor = 0.25;
        const displayTileSize = tileSize * scaleFactor;

        for (let y = 0; y < this.map.length; y++) {
            for (let x = 0; x < this.map[y].length; x++) {
                const key = this.map[y][x] === 1 ? 'wall' : 'path';
                const tile = this.add.image(x * displayTileSize, y * displayTileSize, key);
                tile.setOrigin(0);
                tile.setScale(scaleFactor);
            }
        }

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
    }
    last_error_time = 0;
    async get_round_info(){
        try{
            let r = await fetch(`${HOST}/round_info`).then(r=>r.json());
            console.log(r);
            if(r["status"]){
                this.status = RUNNING;
            }else{
                this.last_error_time = Date.now();
            }
        }catch{
            this.last_error_time = Date.now();
        }
    }

    update() {
        /* Round start */
        if(this.status == SHUTDOWN) {
            if(Date.now() - this.last_error_time > 2000){
                this.get_round_info();
            } 
            return
        }
    }
}
