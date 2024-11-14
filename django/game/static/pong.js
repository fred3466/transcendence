// static/pong.js

const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
let socketUrl = protocol + '://' + window.location.host + '/ws/pong/' + party_id + '/';
console.log(`WebSocket URL: ${socketUrl}`);

if (match_id) {
    socketUrl += `${match_id}/`;
}
console.log(`WebSocket URL: ${socketUrl}`);
const socket = new WebSocket(socketUrl);

let userId = null;
let playerIds = [];  // To hold player IDs
let isPlayerOne = false;
let isPlayerTwo = false;
let isPlayerThree = false;

let playerUsernames = {};

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Game variables
const paddleWidth = 10;
const paddleHeight = 100;
const ballRadius = 10;

let paddle1Y = (canvas.height - paddleHeight) / 2;  // Left paddle (Player 1)
let paddle2Y = (canvas.height - paddleHeight) / 2;  // Right paddle (Player 2)
let paddle3X = (canvas.width - paddleHeight) / 2;   // Top paddle (Player 3)

let ballX = canvas.width / 2;
let ballY = canvas.height / 2;

let upPressed = false;
let downPressed = false;
let leftPressed = false;
let rightPressed = false;

let gameStarted = false;

const scoreBoard = document.createElement('div');
scoreBoard.id = 'scoreBoard';

const leftScoreSpan = document.createElement('span');
leftScoreSpan.id = 'leftScore';
const rightScoreSpan = document.createElement('span');
rightScoreSpan.id = 'rightScore';
const topScoreSpan = document.createElement('span');
topScoreSpan.id = 'topScore';

scoreBoard.appendChild(leftScoreSpan);
scoreBoard.appendChild(rightScoreSpan);
scoreBoard.appendChild(topScoreSpan);

leftScoreSpan.style.float = 'left';
rightScoreSpan.style.float = 'right';
topScoreSpan.style.display = 'block';
topScoreSpan.style.textAlign = 'center';

scoreBoard.style.color = 'white';
scoreBoard.style.fontSize = '24px';
scoreBoard.style.textAlign = 'center';
scoreBoard.style.marginBottom = '10px';
document.getElementById('game-container').insertBefore(scoreBoard, canvas);

let scores = {};

// Event listeners for key presses
document.addEventListener('keydown', keyDownHandler);
document.addEventListener('keyup', keyUpHandler);

// Key down handler
function keyDownHandler(e) {
    if (isPlayerThree) {
        if (e.key === 'ArrowLeft') {
            leftPressed = true;
        } else if (e.key === 'ArrowRight') {
            rightPressed = true;
        }
    } else if (isPlayerOne || isPlayerTwo) {
        if (e.key === 'ArrowUp') {
            upPressed = true;
        } else if (e.key === 'ArrowDown') {
            downPressed = true;
        }
    }
}

// Key up handler
function keyUpHandler(e) {
    if (isPlayerThree) {
        if (e.key === 'ArrowLeft') {
            leftPressed = false;
        } else if (e.key === 'ArrowRight') {
            rightPressed = false;
        }
    } else if (isPlayerOne || isPlayerTwo) {
        if (e.key === 'ArrowUp') {
            upPressed = false;
        } else if (e.key === 'ArrowDown') {
            downPressed = false;
        }
    }
}


// WebSocket event handlers
socket.onopen = function() {
    console.log('WebSocket connection opened');
};

function startCountdown(duration) {
    let countdownTime = duration;

    function updateCountdown() {
        // Clear the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Display the countdown number
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 72px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        if (countdownTime > 0) {
            ctx.fillText(countdownTime, canvas.width / 2, canvas.height / 2);
            countdownTime--;
            setTimeout(updateCountdown, 1000);
        } else {
            ctx.fillText('GO!', canvas.width / 2, canvas.height / 2);
            // Wait a moment before starting the game to show 'GO!'
            setTimeout(function() {
                gameStarted = true;
                requestAnimationFrame(draw);
            }, 500);
        }
    }

    updateCountdown();
}

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.action === 'set_user_id') {
        userId = parseInt(data.user_id);
        console.log(`Your user ID is: ${userId}`);
    }

    if (data.action === 'start_game') {
        gameStarted = false;
        document.getElementById('waiting-room').style.display = 'none';
        document.getElementById('game-container').style.display = 'block';

        playerIds = data.player_ids.map(id => parseInt(id));
        playerUsernames = data.player_usernames;

        // Determine player role
        if (userId === playerIds[0]) {
            isPlayerOne = true;
        } else if (userId === playerIds[1]) {
            isPlayerTwo = true;
        } else if (playerIds.length === 3 && userId === playerIds[2]) {
            isPlayerThree = true;
        } else {
            console.error('User ID does not match any player ID');
        }

        // Initialize scores
        scores = {};
        playerIds.forEach(id => {
            scores[id] = 0;
        });

        const countdownDuration = data.countdown_duration || 3;
        startCountdown(countdownDuration);
    }

    if (data.action === 'update_state') {
        // Update game state based on data from server
        ballX = data.ballX;
        ballY = data.ballY;
        scores = data.scores;
    
        const paddles = data.paddles;
        playerIds.forEach(playerId => {
            const paddle = paddles[playerId];
            if (paddle.orientation === 'vertical') {
                if (playerId === playerIds[0]) {
                    paddle1Y = paddle.y;
                } else if (playerId === playerIds[1]) {
                    paddle2Y = paddle.y;
                }
            } else if (paddle.orientation === 'horizontal' && playerIds.length === 3) {
                paddle3X = paddle.x;
            }
        });
    
        // Update the score display
        updateScoreBoard();
    }

    if (data.action === 'game_over') {
        scores = data.scores;
        updateScoreBoard();
        gameStarted = false;

        const canvas = document.getElementById('gameCanvas');
        const gameoverMessage = document.getElementById('gameover-message');

        // Get canvas position relative to its parent
        const canvasRect = canvas.getBoundingClientRect();
        const parentRect = canvas.parentElement.getBoundingClientRect();

        // Calculate the position of the canvas relative to its parent
        const topPosition = canvas.offsetTop;
        const leftPosition = canvas.offsetLeft;

        // Apply styles to position the gameover message over the canvas
        gameoverMessage.style.position = 'absolute';
        gameoverMessage.style.top = topPosition + 'px';
        gameoverMessage.style.left = leftPosition + 'px';
        gameoverMessage.style.width = canvas.width - 44 + 'px';
        gameoverMessage.style.height = canvas.height  - 32 + 'px';
        gameoverMessage.style.display = 'flex';

        document.getElementById('gameover-text').textContent = data.message + ' Redirecting...';
        // Optionally redirect or reset the game
        setTimeout(function() {
            if (match_id) {
                window.location.href = '/game/tournaments/'+ tournament_id + '/progress/';
                return;
            }
            else {
                window.location.href = '/game/lobby/';
            }
        }, 3000);
    }
};

function updateScoreBoard() {
    const player1Id = playerIds[0];
    const player2Id = playerIds[1];
    document.getElementById('leftScore').textContent = `${playerUsernames[player1Id]}: ${scores[player1Id]}`;
    document.getElementById('rightScore').textContent = `${playerUsernames[player2Id]}: ${scores[player2Id]}`;

    if (playerIds.length === 3) {
        const player3Id = playerIds[2];
        document.getElementById('topScore').textContent = `${playerUsernames[player3Id]}: ${scores[player3Id]}`;
        document.getElementById('topScore').style.display = 'block';
    } else {
        document.getElementById('topScore').style.display = 'none';
    }
}


socket.onclose = function() {
    console.log('WebSocket connection closed');
};

// Send paddle movement to server
function sendPaddlePosition() {
    if (!gameStarted) return;

    let positionData = {};

    if (isPlayerOne) {
        if (typeof paddle1Y === 'number') {
            positionData = {'paddleY': paddle1Y};
        }
    } else if (isPlayerTwo) {
        if (typeof paddle2Y === 'number') {
            positionData = {'paddleY': paddle2Y};
        }
    } else if (isPlayerThree) {
        if (typeof paddle3X === 'number') {
            positionData = {'paddleX': paddle3X};
        }
    }

    if (Object.keys(positionData).length > 0) {
        socket.send(JSON.stringify({
            'action': 'move_paddle',
            ...positionData
        }));
    }
}

// Draw function
function draw() {
    if (!gameStarted) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw paddles
    ctx.fillStyle = '#FFFFFF';

    // Paddle 1 (Left)
    ctx.fillRect(0, paddle1Y, paddleWidth, paddleHeight);

    // Paddle 2 (Right)
    ctx.fillRect(canvas.width - paddleWidth, paddle2Y, paddleWidth, paddleHeight);

    // Paddle 3 (Top)
    if (playerIds.length === 3) {
        ctx.fillRect(paddle3X, 0, paddleHeight, paddleWidth);
    }

    // Draw ball
    ctx.beginPath();
    ctx.arc(ballX, ballY, ballRadius, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();
    ctx.closePath();

    // Draw borders
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    // Move paddles based on key presses
    if (isPlayerOne) {
        if (upPressed) {
            paddle1Y -= 7;
            if (paddle1Y < 0) paddle1Y = 0;
            sendPaddlePosition();
        }
        if (downPressed) {
            paddle1Y += 7;
            if (paddle1Y + paddleHeight > canvas.height) paddle1Y = canvas.height - paddleHeight;
            sendPaddlePosition();
        }
    } else if (isPlayerTwo) {
        if (upPressed) {
            paddle2Y -= 7;
            if (paddle2Y < 0) paddle2Y = 0;
            sendPaddlePosition();
        }
        if (downPressed) {
            paddle2Y += 7;
            if (paddle2Y + paddleHeight > canvas.height) paddle2Y = canvas.height - paddleHeight;
            sendPaddlePosition();
        }
    } else if (isPlayerThree && playerIds.length === 3) {
        if (leftPressed) {
            paddle3X -= 7;
            if (paddle3X < 0) paddle3X = 0;
            sendPaddlePosition();
        }
        if (rightPressed) {
            paddle3X += 7;
            if (paddle3X + paddleHeight > canvas.width) paddle3X = canvas.width - paddleHeight;
            sendPaddlePosition();
        }
    }


    requestAnimationFrame(draw);
}
