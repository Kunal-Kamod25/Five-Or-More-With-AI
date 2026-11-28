export const BOARD_SIZE = 9;
export const CELL_COUNT = BOARD_SIZE * BOARD_SIZE;
export const LINE_SCORES = new Map([[5, 10], [6, 12], [7, 14], [8, 16], [9, 18]]);
export const SPAWN_COUNTS = Object.freeze({ Easy: 1, Medium: 2, Hard: 3 });
const DIRECTIONS = [[-1, 0], [1, 0], [0, -1], [0, 1]];

function randomInt(max) {
  return Math.floor(Math.random() * max);
}

function shuffled(values) {
  const result = values.slice();
  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = randomInt(i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

export function cellXY(index) {
  return [index % BOARD_SIZE, Math.floor(index / BOARD_SIZE)];
}

export function findPath(board, source, destination) {
  if (!Number.isInteger(source) || !Number.isInteger(destination)) return null;
  if (source < 0 || source >= CELL_COUNT || destination < 0 || destination >= CELL_COUNT) return null;
  if (!board[source] || board[destination] !== 0) return null;

  const frontier = [source];
  const parent = new Int16Array(CELL_COUNT);
  parent.fill(-2);
  parent[source] = -1;

  for (let cursor = 0; cursor < frontier.length; cursor += 1) {
    const current = frontier[cursor];
    if (current === destination) {
      const path = [];
      for (let step = destination; step !== -1; step = parent[step]) path.push(step);
      return path.reverse();
    }

    const [x, y] = cellXY(current);
    for (const [dx, dy] of DIRECTIONS) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || nx >= BOARD_SIZE || ny < 0 || ny >= BOARD_SIZE) continue;
      const next = ny * BOARD_SIZE + nx;
      if (board[next] !== 0 || parent[next] !== -2) continue;
      parent[next] = current;
      frontier.push(next);
    }
  }
  return null;
}

export function getLegalActions(board) {
  const actions = [];
  for (let source = 0; source < CELL_COUNT; source += 1) {
    if (!board[source]) continue;
    const frontier = [source];
    const visited = new Uint8Array(CELL_COUNT);
    visited[source] = 1;
    for (let cursor = 0; cursor < frontier.length; cursor += 1) {
      const current = frontier[cursor];
      const [x, y] = cellXY(current);
      for (const [dx, dy] of DIRECTIONS) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || nx >= BOARD_SIZE || ny < 0 || ny >= BOARD_SIZE) continue;
        const next = ny * BOARD_SIZE + nx;
        if (visited[next] || board[next] !== 0) continue;
        visited[next] = 1;
        frontier.push(next);
        actions.push(source * CELL_COUNT + next);
      }
    }
  }
  return actions;
}

export function findMatches(board) {
  const matches = new Set();
  const lines = [];
  for (let y = 0; y < BOARD_SIZE; y += 1) {
    for (let x = 0; x < BOARD_SIZE; x += 1) {
      const color = board[y * BOARD_SIZE + x];
      if (!color) continue;
      for (const [dx, dy] of [[1, 0], [0, 1]]) {
        const previousX = x - dx;
        const previousY = y - dy;
        if (
          previousX >= 0 && previousY >= 0
          && board[previousY * BOARD_SIZE + previousX] === color
        ) continue;

        const line = [];
        let currentX = x;
        let currentY = y;
        while (
          currentX < BOARD_SIZE && currentY < BOARD_SIZE
          && board[currentY * BOARD_SIZE + currentX] === color
        ) {
          line.push(currentY * BOARD_SIZE + currentX);
          currentX += dx;
          currentY += dy;
        }
        if (line.length >= 5) {
          lines.push(line);
          line.forEach((index) => matches.add(index));
        }
      }
    }
  }
  return { positions: [...matches], lines };
}

function clearMatches(board) {
  const matches = findMatches(board);
  let score = 0;
  for (const line of matches.lines) score += LINE_SCORES.get(line.length) ?? 0;
  matches.positions.forEach((index) => { board[index] = 0; });
  return { score, lines: matches.lines, cleared: matches.positions };
}

function spawnPieces(board, amount, colorCount) {
  const empty = [];
  for (let index = 0; index < CELL_COUNT; index += 1) {
    if (board[index] === 0) empty.push(index);
  }
  const positions = shuffled(empty).slice(0, amount);
  for (const index of positions) board[index] = randomInt(colorCount) + 1;
  return positions;
}

function createBoard(colorCount) {
  const board = new Array(CELL_COUNT).fill(0);
  spawnPieces(board, 5, colorCount);
  clearMatches(board);
  return board;
}

export function createGame({ mode = "ai", difficulty = "Easy", colorCount = 2 } = {}) {
  if (!Object.hasOwn(SPAWN_COUNTS, difficulty)) throw new RangeError("Choose Easy, Medium, or Hard.");
  if (!Number.isInteger(colorCount) || colorCount < 1 || colorCount > 7) throw new RangeError("Color count must be between 1 and 7.");
  if (mode !== "ai" && mode !== "human" && mode !== "local") throw new RangeError("Choose AI, human, or two-player mode.");
  return {
    board: createBoard(colorCount),
    mode,
    difficulty,
    colorCount,
    scores: [0, 0],
    currentPlayer: 0,
    selected: null,
    lastMove: null,
    gameOver: false,
    turnCount: 0,
    linesCleared: 0,
    bestLine: 0,
    history: [],
    lastAction: null,
    lastReward: 0,
  };
}

export function playMove(game, source, destination) {
  if (game.gameOver) return { ok: false, reason: "This game is over. Start a new game to play again." };
  const path = findPath(game.board, source, destination);
  if (!path) return { ok: false, reason: "That cell can’t be reached. Choose an empty cell connected by a clear path." };

  const actor = game.currentPlayer;
  const color = game.board[source];
  game.board[destination] = color;
  game.board[source] = 0;
  game.turnCount += 1;

  let result = clearMatches(game.board);
  let spawn = [];
  if (result.score === 0) {
    spawn = spawnPieces(game.board, SPAWN_COUNTS[game.difficulty], game.colorCount);
    const spawnedMatches = clearMatches(game.board);
    result = {
      score: result.score + spawnedMatches.score,
      lines: result.lines.concat(spawnedMatches.lines),
      cleared: [...new Set(result.cleared.concat(spawnedMatches.cleared))],
    };
  }
  game.scores[actor] += result.score;
  game.linesCleared += result.lines.length;
  game.bestLine = Math.max(game.bestLine, ...result.lines.map((line) => line.length), 0);
  game.selected = null;
  game.lastMove = {
    source,
    destination,
    path,
    cleared: result.cleared,
    spawned: spawn,
    lineLength: result.lines.reduce((best, line) => Math.max(best, line.length), 0),
  };
  game.lastAction = source * CELL_COUNT + destination;
  game.lastReward = result.score;
  game.history.unshift({
    turn: game.turnCount,
    player: actor,
    source,
    destination,
    score: result.score,
    cleared: result.cleared.length,
    lineLength: result.lines.reduce((best, line) => Math.max(best, line.length), 0),
  });
  if (game.history.length > 8) game.history.length = 8;

  game.gameOver = getLegalActions(game.board).length === 0;
  if (!game.gameOver && game.mode === "local") game.currentPlayer = actor === 0 ? 1 : 0;
  return { ok: true, score: result.score, lines: result.lines, gameOver: game.gameOver };
}

export function determineWinner(scores) {
  if (scores[0] > scores[1]) return 0;
  if (scores[1] > scores[0]) return 1;
  return null;
}
