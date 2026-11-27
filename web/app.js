import { createGame, findPath, getLegalActions, playMove } from "./game.js";
import { loadBrowserDQN } from "./dqn.js";

const COLORS = ["", "Ruby red", "Emerald green", "Sapphire blue", "Topaz yellow", "Amethyst purple", "Aquamarine cyan", "Amber orange"];
const SPAWN_COUNTS = { Easy: 1, Medium: 2, Hard: 3 };
const MOVE_STEP_MS = 320;
const DESTINATION_HOLD_MS = 550;
const BETWEEN_MOVES_MS = 1100;
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
let animationTimer = null;
let animationFrame = null;
let moveAnimation = null;
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

const movingOrbLayer = document.createElement("div");
movingOrbLayer.className = "moving-orb-layer";
movingOrbLayer.setAttribute("aria-hidden", "true");
boardElement.append(movingOrbLayer);

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
  const displayedPath = moveAnimation?.path ?? (active && game.lastMove ? game.lastMove.path : []);
  const route = new Set(displayedPath);
  const movingCell = moveAnimation ? moveAnimation.path[moveAnimation.step] : null;
  cellButtons.forEach((cell, index) => {
    const color = active ? game.board[index] : 0;
    let orb = cell.querySelector(".orb");
    if (color === 0) {
      orb?.remove();
    } else if (orb?.dataset.color !== String(color)) {
      orb?.remove();
      orb = null;
    }
    if (color && !orb && moveAnimation?.source !== index) {
      orb = document.createElement("span");
      orb.className = `orb color-${color}`;
      orb.dataset.color = String(color);
      cell.append(orb);
    }
    cell.classList.toggle("route", route.has(index) && color === 0);
    cell.classList.toggle("route-origin", Boolean(moveAnimation ? moveAnimation.source === index : active && game.lastMove?.source === index));
    cell.classList.toggle("route-destination", Boolean(moveAnimation ? moveAnimation.destination === index : active && game.lastMove?.destination === index));
    cell.classList.toggle("move-current", movingCell === index);
    cell.classList.toggle("last-move", Boolean(!moveAnimation && active && game.lastMove && (game.lastMove.source === index || game.lastMove.destination === index)));
    cell.classList.toggle("clearing", Boolean(active && game.lastMove?.cleared.includes(index)));
    cell.disabled = true;
    let routeLabel = "";
    if (moveAnimation?.source === index) routeLabel = ", moving orb source";
    else if (moveAnimation?.destination === index) routeLabel = ", AI move destination";
    else if (movingCell === index) routeLabel = ", orb moving along path";
    else if (route.has(index)) routeLabel = ", glowing move path";
    else if (active && game.lastMove?.source === index) routeLabel = ", move source";
    else if (active && game.lastMove?.destination === index) routeLabel = ", move destination";
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
  document.querySelector("#turn-label").textContent = !active ? "AI is getting ready" : game.gameOver ? "AI run complete" : paused ? "Autoplay paused" : moveAnimation ? `Moving ${coordinate(movingCell)}…` : busy ? "DQN is choosing a move…" : "DQN is playing";
  document.querySelector("#turn-indicator").classList.toggle("live", Boolean(active && !game.gameOver && !paused && !busy));
  document.querySelector("#turn-indicator").classList.toggle("thinking", Boolean(active && !game.gameOver && !paused && busy));
  document.querySelector("#pause-button").textContent = paused ? "RESUME" : "PAUSE";
  document.querySelector("#pause-button").disabled = !active || game.gameOver;
  document.querySelector("#restart-button").disabled = !dqn || busy;

  if (moveAnimation) {
    boardNote.textContent = `Moving ${COLORS[moveAnimation.color]} orb ${coordinate(moveAnimation.source)} → ${coordinate(moveAnimation.destination)} · one cell at a time`;
  } else if (active && game.lastMove) {
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
  if (animationTimer !== null) window.clearTimeout(animationTimer);
  if (animationFrame !== null) window.cancelAnimationFrame(animationFrame);
  if (moveAnimation?.orbElement) {
    moveAnimation.orbElement.classList.remove("in-transit");
    moveAnimation.orbElement.removeAttribute("style");
    cellButtons[moveAnimation.source].append(moveAnimation.orbElement);
  }
  movingOrbLayer.replaceChildren();
  scheduledMove = null;
  animationTimer = null;
  animationFrame = null;
  moveAnimation = null;
  busy = false;
}

function positionMovingOrb(index, xOffset = 0, yOffset = 0) {
  const layerRect = movingOrbLayer.getBoundingClientRect();
  const cellRect = cellButtons[index].getBoundingClientRect();
  const x = cellRect.left - layerRect.left + (cellRect.width - moveAnimation.orbElement.offsetWidth) / 2 + xOffset;
  const y = cellRect.top - layerRect.top + (cellRect.height - moveAnimation.orbElement.offsetHeight) / 2 + yOffset;
  moveAnimation.orbElement.style.transform = `translate3d(${x}px, ${y}px, 0)`;
}

function completeAnimatedMove(token) {
  if (token !== runToken || !game || !moveAnimation) return;
  const { source, destination } = moveAnimation;
  const orb = moveAnimation.orbElement;
  const result = playMove(game, source, destination);
  if (!result.ok) throw new Error(`The DQN selected an invalid move: ${result.reason}`);
  orb.classList.remove("in-transit");
  orb.removeAttribute("style");
  if (result.score && game.lastMove.cleared.includes(destination)) orb.remove();
  else cellButtons[destination].append(orb);
  movingOrbLayer.replaceChildren();
  moveAnimation = null;
  animationTimer = null;
  busy = false;
  if (result.score) showToast(`DQN clears a line — +${result.score} points.`);
  render();
  if (!game.gameOver) scheduleAIMove(BETWEEN_MOVES_MS);
}

function animateMove(token) {
  if (token !== runToken || !moveAnimation || paused) return;
  if (!moveAnimation.segment && moveAnimation.step < moveAnimation.path.length - 1) {
    const from = moveAnimation.path[moveAnimation.step];
    const to = moveAnimation.path[moveAnimation.step + 1];
    const fromRect = cellButtons[from].getBoundingClientRect();
    const toRect = cellButtons[to].getBoundingClientRect();
    moveAnimation.segment = {
      from,
      to,
      fromX: 0,
      fromY: 0,
      toX: toRect.left - fromRect.left,
      toY: toRect.top - fromRect.top,
      startedAt: performance.now() - (moveAnimation.elapsed || 0),
    };
    moveAnimation.step += 1;
    moveAnimation.elapsed = 0;
  }
  if (moveAnimation.segment) {
    const segment = moveAnimation.segment;
    const frame = (now) => {
      animationFrame = null;
      if (token !== runToken || !moveAnimation || paused) return;
      const progress = Math.min(1, (now - segment.startedAt) / MOVE_STEP_MS);
      const eased = progress * progress * (3 - 2 * progress);
      positionMovingOrb(segment.from, segment.toX * eased, segment.toY * eased);
      if (progress < 1) {
        animationFrame = window.requestAnimationFrame(frame);
        return;
      }
      moveAnimation.segment = null;
      moveAnimation.elapsed = 0;
      render();
      animateMove(token);
    };
    animationFrame = window.requestAnimationFrame(frame);
    return;
  }
  animationTimer = window.setTimeout(() => {
    animationTimer = null;
    try {
      completeAnimatedMove(token);
    } catch (error) {
      game.runError = error instanceof Error ? error.message : String(error);
      game.gameOver = true;
      busy = false;
      showToast(game.runError, true);
      render();
    }
  }, DESTINATION_HOLD_MS);
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
      const path = findPath(game.board, source, destination);
      if (!path) throw new Error("The DQN selected a move without a clear path.");
      moveAnimation = {
        source,
        destination,
        color: game.board[source],
        path,
        step: 0,
        orbElement: cellButtons[source].querySelector(".orb"),
      };
      if (!moveAnimation.orbElement) throw new Error("The DQN's selected orb is missing from the board.");
      const sourceRect = cellButtons[source].getBoundingClientRect();
      const orb = moveAnimation.orbElement;
      orb.style.position = "absolute";
      orb.style.left = "0";
      orb.style.top = "0";
      orb.style.width = `${sourceRect.width * 0.68}px`;
      orb.style.height = `${sourceRect.height * 0.68}px`;
      orb.style.margin = "0";
      orb.style.animation = "none";
      orb.style.transition = "none";
      orb.classList.add("in-transit");
      movingOrbLayer.append(orb);
      positionMovingOrb(source);
      void orb.offsetWidth;
      orb.style.transition = "";
      render();
      animateMove(token);
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
    if (moveAnimation) {
      if (moveAnimation.segment) {
        moveAnimation.segment.startedAt = performance.now() - moveAnimation.elapsed;
      }
      render();
      animateMove(runToken);
    } else {
      scheduleAIMove(500);
    }
  } else {
    paused = true;
    if (scheduledMove !== null) window.clearTimeout(scheduledMove);
    if (animationTimer !== null) window.clearTimeout(animationTimer);
    if (animationFrame !== null && moveAnimation?.segment) {
      window.cancelAnimationFrame(animationFrame);
      animationFrame = null;
      moveAnimation.elapsed = Math.min(MOVE_STEP_MS, performance.now() - moveAnimation.segment.startedAt);
    }
    scheduledMove = null;
    animationTimer = null;
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
