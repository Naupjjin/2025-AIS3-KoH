import { Start } from './scenes/Start.js';

const config = {
    type: Phaser.AUTO,
    title: 'Mortis Bot',
    description: '',
    parent: 'game-container',
    width: 1280,
    height: 1280,
    backgroundColor: '#000000',
    pixelArt: false,
    scene: [
        Start
    ],
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
}

new Phaser.Game(config);
            