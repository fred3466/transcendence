const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Game variables
const paddleWidth = 10;
const paddleHeight = 100;
const ballRadius = 10;

let paddle1Y = (canvas.height - paddleHeight) / 2;
let paddle2Y = (canvas.height - paddleHeight) / 2;
let ballX = canvas.width / 2;
let ballY = canvas.height / 2;
let ballSpeedX = 5;
let ballSpeedY = 3;

let upPressed = false;
let downPressed = false;

let gameStarted = false;

let score1 = 0;
let score2 = 0;

const scoreBoard = document.createElement('div');
scoreBoard.id = 'scoreBoard';

const leftScoreSpan = document.createElement('span');
leftScoreSpan.id = 'leftScore';
const rightScoreSpan = document.createElement('span');
rightScoreSpan.id = 'rightScore';
scoreBoard.appendChild(leftScoreSpan);
scoreBoard.appendChild(rightScoreSpan);
leftScoreSpan.style.float = 'left';
rightScoreSpan.style.float = 'right';

scoreBoard.style.color = 'white';
scoreBoard.style.fontSize = '24px';
scoreBoard.style.textAlign = 'center';
scoreBoard.style.marginBottom = '10px';
document.getElementById('game-container').insertBefore(scoreBoard, canvas);

// Game over message
const gameOverMessage = document.createElement('div');
gameOverMessage.id = 'gameOverMessage';
gameOverMessage.style.fontSize = '32px';
gameOverMessage.style.textAlign = 'center';
gameOverMessage.style.display = 'none';
document.getElementById('game-container').appendChild(gameOverMessage);

// Event listeners for key presses
document.addEventListener('keydown', keyDownHandler);
document.addEventListener('keyup', keyUpHandler);

function keyDownHandler(e) {
    if (e.key === 'ArrowUp') {
        upPressed = true;
    } else if (e.key === 'ArrowDown') {
        downPressed = true;
    }
}

function keyUpHandler(e) {
    if (e.key === 'ArrowUp') {
        upPressed = false;
    } else if (e.key === 'ArrowDown') {
        downPressed = false;
    }
}

function startGame() {
    document.getElementById('waiting-room').style.display = 'none'; // Hide waiting room
    document.getElementById('game-container').style.display = 'block'; // Show game

    gameOverMessage.style.display = 'none'; // Hide game over message
    score1 = 0;
    score2 = 0;
    updateScoreBoard();

    gameStarted = true;
    requestAnimationFrame(draw); // Start the game loop
}

function moveAI(random = false) {
    let tempBallX = ballX;
    let tempBallY = ballY;
    let tempBallSpeedY = ballSpeedY;

    // Predict the Y position of the ball when it reaches the AI paddle
    let maxIterations = 1000; // Set a maximum number of iterations to prevent infinite loop
    let iterations = 0;

    while (tempBallX <= canvas.width - paddleWidth && iterations < maxIterations)
	{
        tempBallX += ballSpeedX;
        tempBallY += tempBallSpeedY;

        // Reverse ball Y direction when it hits top or bottom wall
        if (tempBallY < 0 || tempBallY > canvas.height)
            tempBallSpeedY = -tempBallSpeedY;
        iterations++;
    }

    let predictedY = tempBallY;
    let paddleCenterY = paddle2Y + paddleHeight / 2;

	if (random === false)
	{
		if (paddleCenterY <= predictedY - 5)
			paddle2Y += 5; // Move down
		else if (paddleCenterY >= predictedY + 5)
			paddle2Y -= 5; // Move up
	}
	else
	{
		if (paddleCenterY <= predictedY - 5)
			paddle2Y -= 5;
		else if (paddleCenterY >= predictedY + 5)
			paddle2Y += 5;
	}

    // Prevent AI paddle from going off the screen
    if (paddle2Y < 0)
			paddle2Y = 0;
    if (paddle2Y + paddleHeight > canvas.height)
			paddle2Y = canvas.height - paddleHeight;
}


function updateScoreBoard() {
    document.getElementById('leftScore').textContent = `${user} : ${score1}`;
    document.getElementById('rightScore').textContent = `AI: ${score2}`;
}

function draw() {
    if (!gameStarted) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw paddles
    ctx.fillStyle = '#FFFFFF';

    // Paddle 1
    ctx.fillRect(0, paddle1Y, paddleWidth, paddleHeight);

    // Paddle 2
    ctx.fillRect(canvas.width - paddleWidth, paddle2Y, paddleWidth, paddleHeight);

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

    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Ball collision with top and bottom walls
    if (ballY + ballRadius > canvas.height || ballY - ballRadius < 0) {
        ballSpeedY = -ballSpeedY;
    }

    // Ball collision with player paddle
    if (ballX - ballRadius < paddleWidth && ballY > paddle1Y && ballY < paddle1Y + paddleHeight) {
        ballSpeedX = -ballSpeedX;
    }

    // Ball collision with AI paddle
    if (ballX + ballRadius > canvas.width - paddleWidth && ballY > paddle2Y && ballY < paddle2Y + paddleHeight) {
        ballSpeedX = -ballSpeedX;
    }

    // Ball goes off screen (left or right)
    if (ballX - ballRadius < 0) {
        score2++; // AI scores
        resetBall();
    }
    if (ballX + ballRadius > canvas.width) {
        score1++; // Player scores
        resetBall();
    }

    // Update the score
    updateScoreBoard();

    // Check for game over
    if (score1 >= 5 || score2 >= 5) {
        gameOver();
        return;
    }

    // Move player paddle based on key presses
    if (upPressed && paddle1Y > 0) {
        paddle1Y -= 7;
    } else if (downPressed && paddle1Y + paddleHeight < canvas.height) {
        paddle1Y += 7;
    }

	if (typeof draw.randomAI === 'undefined') {
		draw.randomAI = 0;
	}

	draw.randomAI++;

	if (draw.randomAI < 300)
    	moveAI(false);
	else if (draw.randomAI < 360)
		moveAI(true);
	else
		draw.randomAI = 0;

    requestAnimationFrame(draw);
}

function resetBall() {
    ballX = canvas.width / 2;
    ballY = canvas.height / 2;
    ballSpeedX = -ballSpeedX; // Change direction
    ballSpeedY = (Math.random() > 0.5 ? 3 : -3); // Randomize the Y direction
}

function gameOver() {
    gameStarted = false;
    gameOverMessage.textContent = score1 >= 5 ? 'Player Wins!' : 'AI Wins!';
    gameOverMessage.style.display = 'block';

    // Apply styles to center the game over message
    gameOverMessage.style.position = 'absolute';
    gameOverMessage.style.top = '50%';
    gameOverMessage.style.left = '50%';
    gameOverMessage.style.transform = 'translate(-50%, -50%)';
    gameOverMessage.style.display = 'flex';
    gameOverMessage.style.alignItems = 'center';
    gameOverMessage.style.justifyContent = 'center';
    gameOverMessage.style.width = '100%';
    gameOverMessage.style.height = '100%';
    gameOverMessage.style.color = 'white';

    // Optionally redirect or reset the game
    setTimeout(function() {
        window.location.href = '/game/lobby/';
    }, 3000);
}

// Start the game immediately
startGame();
