let currentLevel = 1;
let levelConfigs = [];
const baseImages = {};
const objectImages = {};
const bases = [];
let selectedBase = null;
let selectedObjects = [];

// Toggle this to enable or disable verbose logging during gameplay.
const DEBUG = false;

/**
 * Helper to log debug information conditionally.
 * It prints to the console only when the DEBUG flag is true so normal
 * gameplay isn't cluttered by messages.
 */
function debugLog(...args) {
    if (DEBUG) {
        console.log(...args);
    }
}

// BASE_BOTTOM defines how far from the bottom of the base the
// first object in the stack is positioned. The value is expressed
// as a percentage of the base width so scaling remains consistent
// across different screen sizes.
const BASE_BOTTOM = 0.28; // % of base width from the bottom
const OBJECT_WIDTH = 0.8; // % of base width
const OBJECT_UP = 0.618; // % of object height
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
 * Represents a single base platform. Each object on the base is stored
 * with a flag indicating whether it is currently selected. The draw
 * method reads this flag to offset selected objects upward so the
 * selection is visible without removing them from the stack.
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
        const objWidth = this.w * OBJECT_WIDTH;
        let currentY = this.y + this.h - this.w * BASE_BOTTOM;
        for (const obj of this.objects) {
            const objImg = objectImages[obj.name];
            const aspect = objImg.height / objImg.width;
            const objHeight = objWidth * aspect;
            const objX = this.x + (this.w - objWidth) / 2;
            currentY -= objHeight;
            let drawY = currentY;
            if (obj.isSelected) {
                drawY -= OBJECT_UP * objHeight;
            }
            ctx.drawImage(objImg, objX, drawY, objWidth, objHeight);
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
            const objs = cell.objects.map(name => ({ name, isSelected: false }));
            const b = new Base(cell.baseHeight, objs);
            const x = startX + ci * (baseW + hGap) * scale;
            const y = startY + ri * (baseH + vGap) * scale;
            b.setRect(x, y, baseW * scale, baseH * scale);
            bases.push(b);
        });
    });
}

/**
 * Render all bases. Selected objects are drawn with an offset directly
 * inside the Base.draw() implementation.
 */
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
 * Update the game screen for the provided level number by preparing
 * layout for the level and drawing it on the canvas.
 */
async function showLevel(number) {
    const level = levelConfigs[number - 1];
    if (!level) return;
    selectedBase = null;
    selectedObjects = [];
    await prepareLevel(level);
    drawLevel();
}

const screens = {
    start: document.getElementById('start-screen'),
    game: document.getElementById('game-screen'),
    completed: document.getElementById('completed-screen')
};
/**
 * Toggle which screen is visible by changing the `active` CSS class.
 * Only one screen is displayed at a time so the others get hidden.
 */

function showScreen(name) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[name].classList.add('active');
}

/**
 * Manage selection and movement of objects when the user clicks on a base.
 * Selected objects are flagged instead of removed so they can be drawn
 * slightly above their original spot. Dropping the selection moves those
 * flagged objects to another base if allowed or clears the flag when
 * cancelled.
 */
function handleCanvasClick(evt) {
    const rect = canvas.getBoundingClientRect();
    const x = evt.clientX - rect.left;
    const y = evt.clientY - rect.top;
    const clickedBase = bases.find(b => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h);
    debugLog('Canvas click', x, y);
    if (!clickedBase) {
        debugLog('Click missed all bases');
        return;
    }
    debugLog('Clicked base', bases.indexOf(clickedBase));

    if (!selectedBase) {
        if (clickedBase.objects.length === 0) return;
        const color = clickedBase.objects[clickedBase.objects.length - 1].name;
        selectedObjects = [];
        for (let i = clickedBase.objects.length - 1; i >= 0; i--) {
            const obj = clickedBase.objects[i];
            if (obj.name === color) {
                obj.isSelected = true;
                selectedObjects.push(obj);
            } else {
                break;
            }
        }
        selectedBase = clickedBase;
        debugLog('Selected', selectedObjects.length, 'object(s) from base', bases.indexOf(clickedBase));
    } else if (selectedBase === clickedBase) {
        selectedObjects.forEach(o => { o.isSelected = false; });
        selectedBase = null;
        selectedObjects = [];
        debugLog('Selection cancelled');
    } else {
        const target = clickedBase;
        const color = selectedObjects[0].name;
        const top = target.objects[target.objects.length - 1];
        if (target.objects.length === 0 || (top && top.name === color)) {
            const free = target.baseHeight - target.objects.length;
            const moveCount = Math.min(free, selectedObjects.length);
            const moved = [];
            for (let i = 0; i < moveCount; i++) {
                moved.push(selectedBase.objects.pop());
            }
            for (let i = moved.length - 1; i >= 0; i--) {
                const obj = moved[i];
                obj.isSelected = false;
                target.objects.push(obj);
            }
            selectedObjects.splice(0, moveCount);
            debugLog('Moved', moveCount, 'object(s) to base', bases.indexOf(target));
        }
        selectedObjects.forEach(o => { o.isSelected = false; });
        selectedBase = null;
        selectedObjects = [];
    }
    drawLevel();
}

document.getElementById('start-button').addEventListener('click', () => {
    showScreen('game');
    // Wait one frame so layout recalculates with the game screen visible
    requestAnimationFrame(() => showLevel(currentLevel));
});

canvas.addEventListener('click', handleCanvasClick);


document.getElementById('next-button').addEventListener('click', () => {
    currentLevel += 1;
    showLevel(currentLevel);
    showScreen('game');
});

// Kick off loading of the configuration when the script loads.
loadLevelConfigs();

