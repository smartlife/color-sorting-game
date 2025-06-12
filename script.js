let currentLevel = 1;

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
});

document.getElementById('complete-button').addEventListener('click', () => {
    document.getElementById('completed-title').textContent = `Level ${currentLevel} Completed`;
    showScreen('completed');
});

document.getElementById('next-button').addEventListener('click', () => {
    currentLevel += 1;
    document.getElementById('game-title').textContent = `Game Screen - Level ${currentLevel}`;
    showScreen('game');
});

