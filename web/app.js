import { createGame, determineWinner, getLegalActions, playMove } from "./game.js";
import { loadBrowserDQN } from "./dqn.js";

const COLORS = ["", "Ruby red", "Emerald green", "Sapphire blue", "Topaz yellow", "Amethyst purple", "Aquamarine cyan", "Amber orange"];
const boardElement = document.querySelector("#board");
const toastElement = document.querySelector("#toast");
const boardNote = document.querySelector("#board-note");
const modelStatus = document.querySelector("#model-status");
const statusDot = document.querySelector(".status-dot");
const cellButtons = [];

let dqn = null;
let game = null;
let mode = "ai";
let difficulty = "Easy";
let colorCount = 2;
let busy = false;
let toastTimer = 0;

for (let index = 0; index < 81; index += 1) {
  const cell = document.createElement("button");
  cell.className = "cell";
  cell.type = "button";
  cell.setAttribute("role", "gridcell");
  cell.dataset.index = String(index);
  cell.setAttribute("aria-label", `Row ${Math.floor(index / 9) + 1}, column ${(index % 9) + 1}, empty`);
  cell.addEventListener("click", () => handleCellClick(index));
  boardElement.append(cell);
  cellButtons.push(cell);
}

function showToast(message, isError = false) {
  toastElement.textContent = message;
  toastElement.classList.toggle("error", isError);
  toastElement.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toastElement.classList.remove("visible"), 3000);
}

function activePlayerLabel() {
  if (game?.mode === "local") return game.currentPlayer === 0 ? "PLAYER 1 TURN" : "PLAYER 2 TURN";
  return game?.currentPlayer === 0 ? "YOUR TURN" : "DQN IS THINKING";
}

function render() {
  const active = Boolean(game);
  const aiTurn = active && game.mode === "ai" && game.currentPlayer === 1;
  cellButtons.forEach((cell, index) => {
    const color = active ? game.board[index] : 0;
    cell.replaceChildren();
    cell.classList.toggle("selected", active && game.selected === index);
    cell.classList.toggle(
      "last-move",
      active && game.lastMove && (game.lastMove.source === index || game.lastMove.destination === index),
    );
    cell.classList.toggle("clearing", Boolean(active && game.lastMove?.cleared.includes(index) && busy));
    cell.disabled = !active || game.gameOver || busy || aiTurn;
    if (color) {
      const orb = document.createElement("span");
      orb.className = `orb color-${color}`;
      cell.append(orb);
    }
    const selected = active && game.selected === index;
    cell.setAttribute(
      "aria-label",
      `Row ${Math.floor(index / 9) + 1}, column ${(index % 9) + 1}, ${color ? COLORS[color] : "empty"}${selected ? ", selected" : ""}`,
    );
  });

  document.querySelector("#restart-button").disabled = !active || busy;
  document.querySelector("#player-one-score").textContent = String(active ? game.scores[0] : 0).padStart(2, "0");
  document.querySelector("#player-two-score").textContent = String(active ? game.scores[1] : 0).padStart(2, "0");
  document.querySelector("#best-line").textContent = active && game.bestLine ? `${game.bestLine} ORBS` : "—";
  document.querySelector("#player-one-name").textContent = active && game.mode === "local" ? "PLAYER 1" : "YOU";
  document.querySelector("#player-two-name").textContent = active && game.mode === "local" ? "PLAYER 2" : "DQN";
  document.querySelector("#player-one-caption").textContent = active && game.mode === "local" ? "GREEN ORBS" : "YOUR POINTS";
  document.querySelector("#player-two-caption").textContent = active && game.mode === "local" ? "ORANGE ORBS" : "AGENT POINTS";
  document.querySelector("#score-player-one").classList.toggle("active", !active || game.currentPlayer === 0);
  document.querySelector("#score-player-two").classList.toggle("active", Boolean(active && game.currentPlayer === 1));

  const turnLabel = document.querySelector("#turn-label");
  const turnIndicator = document.querySelector("#turn-indicator");
  const gameStateLabel = document.querySelector("#game-state-label");
  turnIndicator.classList.toggle("live", active && !game.gameOver && !aiTurn && !busy);
  turnIndicator.classList.toggle("thinking", Boolean(active && (aiTurn || busy)));
  if (!active) {
    turnLabel.textContent = "Choose your game";
    gameStateLabel.textContent = "READY";
  } else if (game.gameOver) {
    const winner = determineWinner(game.scores);
    turnLabel.textContent = winner === null ? "A perfect tie" : winner === 0 ? (game.mode === "local" ? "Player 1 wins" : "You win") : (game.mode === "local" ? "Player 2 wins" : "DQN takes it");
    gameStateLabel.textContent = "GAME OVER";
  } else {
    turnLabel.textContent = busy ? "DQN is thinking…" : activePlayerLabel();
    gameStateLabel.textContent = busy ? "AI TURN" : "IN PLAY";
  }
  gameStateLabel.classList.toggle("in-game", active && !game.gameOver);
  if (active && game.lastMove) {
    const from = coordinate(game.lastMove.source);
    const to = coordinate(game.lastMove.destination);
    boardNote.textContent = game.lastMove.score
      ? `${game.lastMove.score} points · ${game.lastMove.lineLength || game.bestLine} connected`
      : `Moved ${from} → ${to} · new orbs spawned`;
  } else {
    boardNote.textContent = "Connect five or more orbs of the same color";
  }
}

function coordinate(index) {
  return `${String.fromCharCode(65 + (index % 9))}${Math.floor(index / 9) + 1}`;
}

function handleCellClick(index) {
  if (!game || busy || game.gameOver || (game.mode === "ai" && game.currentPlayer === 1)) return;
  const color = game.board[index];
  if (color) {
    game.selected = game.selected === index ? null : index;
    render();
    return;
  }
  if (game.selected === null) {
    showToast("Select one of your orbs first.");
    return;
  }

  const result = playMove(game, game.selected, index);
  if (!result.ok) {
    showToast(result.reason);
    return;
  }
  render();
  if (result.score) showToast(`Line cleared — +${result.score} points!`);
  else showToast(`${SPAWN_LABEL[difficulty]} new ${colorCount === 1 ? "orb" : "orbs"} arrived.`);
  if (game.gameOver) {
    showToast(gameOverMessage());
    render();
    return;
  }
  if (game.mode === "ai" && game.currentPlayer === 1) scheduleAIMove();
}

const SPAWN_LABEL = { Easy: 1, Medium: 2, Hard: 3 };

function gameOverMessage() {
  const winner = determineWinner(game.scores);
  if (winner === null) return `Board full — it’s a tie at ${game.scores[0]} each.`;
  if (game.mode === "local") return `Player ${winner + 1} wins with ${game.scores[winner]} points!`;
  return winner === 0
    ? `You win ${game.scores[0]}–${game.scores[1]}!`
    : `The DQN wins ${game.scores[1]}–${game.scores[0]}. Play again?`;
}

function scheduleAIMove() {
  busy = true;
  render();
  window.setTimeout(() => {
    try {
      if (!game || game.gameOver || game.mode !== "ai" || game.currentPlayer !== 1) return;
      if (!dqn) throw new Error("The trained DQN is unavailable. Try a local two-player game.");
      const legalActions = getLegalActions(game.board);
      if (!legalActions.length) {
        game.gameOver = true;
        render();
        return;
      }
      const avoid = game.lastAction !== null && game.lastReward <= 0
        ? [((game.lastAction % 81) * 81) + Math.floor(game.lastAction / 81)]
        : [];
      const action = dqn.chooseAction(game.board, legalActions, avoid);
      if (action === null) throw new Error("The DQN could not select a legal move.");
      const source = Math.floor(action / 81);
      const destination = action % 81;
      const result = playMove(game, source, destination);
      if (!result.ok) throw new Error(`The DQN selected an invalid move: ${result.reason}`);
      if (result.score) showToast(`DQN clears a line — +${result.score} points.`);
    } catch (error) {
      showToast(error.message, true);
      if (game) game.gameOver = true;
    } finally {
      busy = false;
      render();
      if (game?.gameOver) showToast(gameOverMessage());
    }
  }, 420);
}

function startGame() {
  if (mode === "ai" && !dqn) {
    showToast("The trained DQN is still loading. Try again in a moment.", true);
    return;
  }
  game = createGame({ mode, difficulty, colorCount });
  busy = false;
  render();
  showToast(mode === "ai" ? "Game on. The DQN will take every other turn." : "Game on. Pass the keyboard after each move.");
  document.querySelector("#board").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

document.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    mode = button.dataset.mode;
    document.querySelectorAll("[data-mode]").forEach((option) => {
      const selected = option === button;
      option.classList.toggle("selected", selected);
      option.setAttribute("aria-pressed", String(selected));
    });
    document.querySelector("#start-button").disabled = mode === "ai" && !dqn;
    document.querySelector("#mode-note").textContent = mode === "ai"
      ? "A score-maximizing DQN policy, running right here in your browser."
      : "Two players share the board and take turns. Highest score wins.";
  });
});

document.querySelectorAll("[data-difficulty]").forEach((button) => {
  button.addEventListener("click", () => {
    difficulty = button.dataset.difficulty;
    document.querySelector("#difficulty-value").textContent = difficulty.toUpperCase();
    document.querySelectorAll("[data-difficulty]").forEach((option) => {
      option.setAttribute("aria-pressed", String(option === button));
    });
  });
});

document.querySelector("#color-count").addEventListener("input", (event) => {
  colorCount = Number(event.target.value);
  document.querySelector("#color-count-value").textContent = String(colorCount);
});
document.querySelector("#start-button").addEventListener("click", startGame);
document.querySelector("#restart-button").addEventListener("click", startGame);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && game?.selected !== null) {
    game.selected = null;
    render();
  }
});

render();
loadBrowserDQN().then((model) => {
  dqn = model;
  statusDot.classList.remove("loading", "error");
  modelStatus.textContent = "DQN READY · IN BROWSER";
  document.querySelector("#start-button").disabled = false;
  document.querySelector("#mode-note").textContent = `Trained ${model.meta.runId} · ${Number(model.meta.environmentSteps).toLocaleString()} training steps · runs in your browser.`;
}).catch((error) => {
  statusDot.classList.add("error");
  statusDot.classList.remove("loading");
  modelStatus.textContent = "DQN UNAVAILABLE";
  document.querySelector('[data-mode="ai"]').disabled = true;
  document.querySelector("#start-button").disabled = mode === "ai";
  document.querySelector("#mode-note").textContent = "Model load failed. Local two-player mode remains available.";
  showToast(error.message, true);
});
