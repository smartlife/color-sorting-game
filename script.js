let currentLevel = 1;
let levelConfigs = [];
const baseImages = {};
const objectImages = {};
const bases = [];

// BASE_BOTTOM defines how far from the bottom of the base the
// first object in the stack is positioned. The value is expressed
// as a percentage of the base width so scaling remains consistent
// across different screen sizes.
const BASE_BOTTOM = 0.25; // 25% of base width from the bottom
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');

/**
 * Helper to load an image and return a promise that resolves
 * with the Image object when it is ready for drawing.
 */
function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

/**
 * Represents a single base platform. It stores the base height,
 * the objects placed on it and the calculated drawing rectangle.
 * Position and size are assigned during layout.
 */
class Base {
    constructor(baseHeight, objects) {
        this.baseHeight = baseHeight;
        this.objects = objects;
        this.x = 0;
        this.y = 0;
        this.w = 0;
        this.h = 0;
    }

    setRect(x, y, w, h) {
        this.x = x;
        this.y = y;
        this.w = w;
        this.h = h;
    }

    draw() {
        const img = baseImages[this.baseHeight];
        ctx.drawImage(img, this.x, this.y, this.w, this.h);
        // Objects stack from the point BASE_BOTTOM above the bottom of
        // the base. Each object is scaled based on width but keeps its
        // original aspect ratio so non-square graphics are drawn
        // correctly.
        const objWidth = this.w * 0.8;
        let currentY = this.y + this.h - this.w * BASE_BOTTOM;
        for (const name of this.objects) {
            const objImg = objectImages[name];
            const aspect = objImg.height / objImg.width;
            const objHeight = objWidth * aspect;
            const objX = this.x + (this.w - objWidth) / 2;
            currentY -= objHeight;
            ctx.drawImage(objImg, objX, currentY, objWidth, objHeight);
        }
    }
}

/**
 * Calculate layout for a level and preload all required images.
 * The algorithm gathers unique base heights and object colors,
 * loads their images if needed and then positions each base in
 * a grid. Horizontal spacing is 20% of base width and vertical
 * spacing is 50% of base width. The entire level is scaled to fit
 * within the canvas while keeping 5% margins on the sides and top
 * and a 15% margin at the bottom.
 */
async function prepareLevel(level) {
    bases.length = 0;
    const neededBases = new Set();
    const neededObjects = new Set();
    level.rows.forEach(row => row.forEach(cell => {
        neededBases.add(cell.baseHeight);
        cell.objects.forEach(o => neededObjects.add(o));
    }));

    await Promise.all([...neededBases].map(h => {
        if (baseImages[h]) return Promise.resolve();
        return loadImage(`img/base_${h}.png`).then(img => { baseImages[h] = img; });
    }));
    await Promise.all([...neededObjects].map(o => {
        if (objectImages[o]) return Promise.resolve();
        return loadImage(`img/object_${o}.png`).then(img => { objectImages[o] = img; });
    }));

    const sampleBase = baseImages[[...neededBases][0]];
    const baseW = sampleBase.width;
    const baseH = sampleBase.height;
    const hGap = baseW * 0.2;
    const vGap = baseW * 0.5;

    const rows = level.rows;
    const rowCount = rows.length;
    const maxCells = Math.max(...rows.map(r => r.length));

    const unscaledW = maxCells * baseW + (maxCells - 1) * hGap;
    const unscaledH = rowCount * baseH + (rowCount - 1) * vGap;

    const cw = canvas.width = canvas.clientWidth;
    const ch = canvas.height = canvas.clientHeight;
    const areaW = cw * 0.9;
    const areaH = ch * 0.8;
    const scale = Math.min(areaW / unscaledW, areaH / unscaledH);

    const startX = cw * 0.05 + (areaW - unscaledW * scale) / 2;
    const startY = ch * 0.05 + (areaH - unscaledH * scale) / 2;

    rows.forEach((row, ri) => {
        row.forEach((cell, ci) => {
            const b = new Base(cell.baseHeight, cell.objects);
            const x = startX + ci * (baseW + hGap) * scale;
            const y = startY + ri * (baseH + vGap) * scale;
            b.setRect(x, y, baseW * scale, baseH * scale);
            bases.push(b);
        });
    });
}

function drawLevel() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    bases.forEach(b => b.draw());
}

/**
 * Load level configuration from an external JSON file.
 * The JSON contains an array of level objects. Each level
 * describes rows of cells where a cell has a base height and
 * a list of game objects. Once loaded the first level is shown.
 */
async function loadLevelConfigs() {
    try {
        const response = await fetch('levels.json');
        levelConfigs = await response.json();
        showLevel(currentLevel);
    } catch (err) {
        console.error('Failed to load level configuration', err);
    }
}

/**
 * Update the game screen for the provided level number. This demo
 * only sets the title but real rendering would use the level data.
 */
async function showLevel(number) {
    document.getElementById('game-title').textContent = `Game Screen - Level ${number}`;
    const level = levelConfigs[number - 1];
    if (!level) return;
    await prepareLevel(level);
    drawLevel();
}

const screens = {
    start: document.getElementById('start-screen'),
    game: document.getElementById('game-screen'),
    completed: document.getElementById('completed-screen')
};

function showScreen(name) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[name].classList.add('active');
}

document.getElementById('start-button').addEventListener('click', () => {
    showScreen('game');
    showLevel(currentLevel);
});

document.getElementById('complete-button').addEventListener('click', () => {
    document.getElementById('completed-title').textContent = `Level ${currentLevel} Completed`;
    showScreen('completed');
});

document.getElementById('next-button').addEventListener('click', () => {
    currentLevel += 1;
    showLevel(currentLevel);
    showScreen('game');
});

// Kick off loading of the configuration when the script loads.
loadLevelConfigs();

