import { createGame, getLegalActions, playMove } from "./game.js";
import { loadBrowserDQN } from "./dqn.js";

const COLORS = ["", "Ruby red", "Emerald green", "Sapphire blue", "Topaz yellow", "Amethyst purple", "Aquamarine cyan", "Amber orange"];
const SPAWN_COUNTS = { Easy: 1, Medium: 2, Hard: 3 };
const boardElement = document.querySelector("#board");
const toastElement = document.querySelector("#toast");
const boardNote = document.querySelector("#board-note");
const modelStatus = document.querySelector("#model-status");
const statusDot = document.querySelector(".status-dot");
const cellButtons = [];

let dqn = null;
let game = null;
let difficulty = "Easy";
let colorCount = 2;
let busy = false;
let paused = false;
let scheduledMove = null;
let runToken = 0;
let toastTimer = 0;

for (let index = 0; index < 81; index += 1) {
  const cell = document.createElement("button");
  cell.className = "cell";
  cell.type = "button";
  cell.setAttribute("role", "gridcell");
  cell.dataset.index = String(index);
  cell.setAttribute("aria-label", `Row ${Math.floor(index / 9) + 1}, column ${(index % 9) + 1}, empty`);
  cell.disabled = true;
  boardElement.append(cell);
  cellButtons.push(cell);
}

function showToast(message, isError = false) {
  toastElement.textContent = message;
  toastElement.classList.toggle("error", isError);
  toastElement.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toastElement.classList.remove("visible"), 3500);
}

function coordinate(index) {
  return `${String.fromCharCode(65 + (index % 9))}${Math.floor(index / 9) + 1}`;
}

function updateSummary() {
  const panel = document.querySelector("#summary-panel");
  if (!game?.gameOver) {
    panel.hidden = true;
    return;
  }
  const failed = Boolean(game.runError);
  panel.hidden = false;
  document.querySelector("#summary-heading").textContent = failed ? "Run stopped" : "AI game finished";
  document.querySelector("#summary-result").textContent = failed
    ? game.runError
    : `No legal moves remain. The trained DQN scored ${game.scores[0]} points in ${game.turnCount} moves.`;
  document.querySelector("#summary-score").textContent = String(game.scores[0]);
  document.querySelector("#summary-moves").textContent = String(game.turnCount);
  document.querySelector("#summary-lines").textContent = String(game.linesCleared);
  document.querySelector("#summary-best-line").textContent = game.bestLine ? `${game.bestLine} orbs` : "—";
  document.querySelector("#summary-difficulty").textContent = game.difficulty;
  document.querySelector("#summary-colors").textContent = String(game.colorCount);
}

function render() {
  const active = Boolean(game);
  const route = new Set(active && game.lastMove ? game.lastMove.path : []);
  cellButtons.forEach((cell, index) => {
    const color = active ? game.board[index] : 0;
    cell.replaceChildren();
    cell.classList.toggle("route", route.has(index) && color === 0);
    cell.classList.toggle("route-origin", Boolean(active && game.lastMove?.source === index));
    cell.classList.toggle("route-destination", Boolean(active && game.lastMove?.destination === index));
    cell.classList.toggle("last-move", Boolean(active && game.lastMove && (game.lastMove.source === index || game.lastMove.destination === index)));
    cell.classList.toggle("clearing", Boolean(active && game.lastMove?.cleared.includes(index)));
    cell.disabled = true;
    if (color) {
      const orb = document.createElement("span");
      orb.className = `orb color-${color}`;
      cell.append(orb);
    }
    const routeLabel = active && game.lastMove?.source === index
      ? ", move source"
      : active && game.lastMove?.destination === index
        ? ", move destination"
        : route.has(index) ? ", glowing move path" : "";
    cell.setAttribute(
      "aria-label",
      `Row ${Math.floor(index / 9) + 1}, column ${(index % 9) + 1}, ${color ? COLORS[color] : "empty"}${routeLabel}`,
    );
  });

  document.querySelector("#ai-score").textContent = String(active ? game.scores[0] : 0).padStart(2, "0");
  document.querySelector("#move-count").textContent = String(active ? game.turnCount : 0);
  document.querySelector("#line-count").textContent = String(active ? game.linesCleared : 0);
  document.querySelector("#best-line").textContent = active && game.bestLine ? `${game.bestLine} ORBS` : "—";
  document.querySelector("#game-state-label").textContent = !active ? "READY" : game.gameOver ? "FINISHED" : paused ? "PAUSED" : busy ? "AI THINKING" : "IN PLAY";
  document.querySelector("#turn-label").textContent = !active ? "AI is getting ready" : game.gameOver ? "AI run complete" : paused ? "Autoplay paused" : busy ? "DQN is choosing a move…" : "DQN is playing";
  document.querySelector("#turn-indicator").classList.toggle("live", Boolean(active && !game.gameOver && !paused && !busy));
  document.querySelector("#turn-indicator").classList.toggle("thinking", Boolean(active && !game.gameOver && !paused && busy));
  document.querySelector("#pause-button").textContent = paused ? "RESUME" : "PAUSE";
  document.querySelector("#pause-button").disabled = !active || game.gameOver;
  document.querySelector("#restart-button").disabled = !dqn || busy;

  if (active && game.lastMove) {
    const from = coordinate(game.lastMove.source);
    const to = coordinate(game.lastMove.destination);
    boardNote.textContent = game.lastMove.score
      ? `Line cleared: +${game.lastMove.score} points · ${game.lastMove.lineLength || game.bestLine} connected`
      : `AI moved ${from} → ${to} · glowing cells show the route`;
  } else {
    boardNote.textContent = "The AI’s move path will appear here.";
  }
  updateSummary();
}

function stopScheduledMove() {
  runToken += 1;
  if (scheduledMove !== null) window.clearTimeout(scheduledMove);
  scheduledMove = null;
  busy = false;
}

function scheduleAIMove(delay = 450) {
  if (!game || game.gameOver || paused) return;
  stopScheduledMove();
  const token = runToken;
  render();
  scheduledMove = window.setTimeout(() => {
    scheduledMove = null;
    if (token !== runToken || !game || game.gameOver || paused) return;
    try {
      busy = true;
      render();
      const legalActions = getLegalActions(game.board);
      if (!legalActions.length) {
        game.gameOver = true;
        busy = false;
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
      busy = false;
      render();
      if (game.gameOver) {
        return;
      }
      scheduleAIMove(750);
    } catch (error) {
      game.runError = error instanceof Error ? error.message : String(error);
      game.gameOver = true;
      busy = false;
      showToast(game.runError, true);
      render();
    }
  }, delay);
}

function startGame() {
  if (!dqn) {
    showToast("The trained DQN is still loading. Try again in a moment.", true);
    return;
  }
  stopScheduledMove();
  paused = false;
  game = createGame({ mode: "ai", difficulty, colorCount });
  document.querySelector("#setup-page").hidden = true;
  document.querySelector("#game-page").hidden = false;
  document.querySelector("#setup-link").classList.remove("active");
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
  scheduleAIMove(650);
}

function returnToSetup() {
  stopScheduledMove();
  paused = false;
  document.querySelector("#game-page").hidden = true;
  document.querySelector("#setup-page").hidden = false;
  document.querySelector("#setup-link").classList.add("active");
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function togglePause() {
  if (!game || game.gameOver) return;
  if (paused) {
    paused = false;
    scheduleAIMove(180);
  } else {
    paused = true;
    stopScheduledMove();
    render();
  }
}

document.querySelectorAll("[data-difficulty]").forEach((button) => {
  button.addEventListener("click", () => {
    difficulty = button.dataset.difficulty;
    document.querySelector("#difficulty-value").textContent = difficulty.toUpperCase();
    document.querySelector("#difficulty-hint").textContent = `${SPAWN_COUNTS[difficulty]} new ${SPAWN_COUNTS[difficulty] === 1 ? "orb appears" : "orbs appear"} after a move.`;
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
document.querySelector("#play-again-button").addEventListener("click", startGame);
document.querySelector("#back-button").addEventListener("click", returnToSetup);
document.querySelector("#pause-button").addEventListener("click", togglePause);

render();
loadBrowserDQN().then((model) => {
  dqn = model;
  statusDot.classList.remove("loading", "error");
  modelStatus.textContent = "DQN READY · IN BROWSER";
  document.querySelector("#start-button").disabled = false;
  document.querySelector("#restart-button").disabled = false;
  document.querySelector("#mode-note").textContent = `Trained ${model.meta.runId} · ${Number(model.meta.environmentSteps).toLocaleString()} training steps · runs locally in your browser.`;
}).catch((error) => {
  statusDot.classList.add("error");
  statusDot.classList.remove("loading");
  modelStatus.textContent = "DQN UNAVAILABLE";
  document.querySelector("#mode-note").textContent = "Model load failed. Refresh the page to retry.";
  showToast(error.message, true);
});
