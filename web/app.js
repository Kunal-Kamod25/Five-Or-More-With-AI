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
let playMode = "ai";
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
  const isHuman = game.mode === "human";
  document.querySelector("#summary-heading").textContent = failed ? "Run stopped" : isHuman ? "Game finished" : "AI game finished";
  document.querySelector("#summary-result").textContent = failed
    ? game.runError
    : `No legal moves remain. ${isHuman ? "You scored" : "The trained DQN scored"} ${game.scores[0]} points in ${game.turnCount} moves.`;
  document.querySelector("#summary-kicker").textContent = isHuman ? "GAME OVER" : "RUN COMPLETE";
  document.querySelector("#summary-score").textContent = String(game.scores[0]);
  document.querySelector("#summary-moves").textContent = String(game.turnCount);
  document.querySelector("#summary-lines").textContent = String(game.linesCleared);
  document.querySelector("#summary-best-line").textContent = game.bestLine ? `${game.bestLine} orbs` : "—";
  document.querySelector("#summary-difficulty").textContent = game.difficulty;
  document.querySelector("#summary-colors").textContent = String(game.colorCount);
}

function render() {
  const active = Boolean(game);
  const isHuman = active && game.mode === "human";
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
    cell.classList.toggle("selected", Boolean(isHuman && game.selected === index));
    cell.classList.toggle("last-move", Boolean(!moveAnimation && active && game.lastMove && (game.lastMove.source === index || game.lastMove.destination === index)));
    cell.classList.toggle("clearing", Boolean(active && game.lastMove?.cleared.includes(index)));
    cell.disabled = !isHuman || game.gameOver || busy;
    let routeLabel = "";
    if (moveAnimation?.source === index) routeLabel = ", moving orb source";
    else if (moveAnimation?.destination === index) routeLabel = ", AI move destination";
    else if (movingCell === index) routeLabel = ", orb moving along path";
    else if (route.has(index)) routeLabel = ", glowing move path";
    else if (active && game.lastMove?.source === index) routeLabel = ", move source";
    else if (active && game.lastMove?.destination === index) routeLabel = ", move destination";
    if (isHuman && game.selected === index) routeLabel += ", selected";
    cell.setAttribute(
      "aria-label",
      `Row ${Math.floor(index / 9) + 1}, column ${(index % 9) + 1}, ${color ? COLORS[color] : "empty"}${routeLabel}`,
    );
  });

  document.querySelector("#ai-score").textContent = String(active ? game.scores[0] : 0).padStart(2, "0");
  document.querySelector("#move-count").textContent = String(active ? game.turnCount : 0);
  document.querySelector("#line-count").textContent = String(active ? game.linesCleared : 0);
  document.querySelector("#best-line").textContent = active && game.bestLine ? `${game.bestLine} ORBS` : "—";
  document.querySelector("#game-state-label").textContent = !active ? "READY" : game.gameOver ? "FINISHED" : paused ? "PAUSED" : busy ? "AI THINKING" : isHuman ? "YOUR TURN" : "IN PLAY";
  document.querySelector("#turn-label").textContent = !active ? "AI is getting ready" : game.gameOver ? isHuman ? "No moves remain" : "AI run complete" : paused ? "Autoplay paused" : moveAnimation ? `Moving ${coordinate(movingCell)}…` : busy ? "DQN is choosing a move…" : isHuman ? game.selected === null ? "Choose an orb to move" : `Move ${coordinate(game.selected)} to an empty cell` : "DQN is playing";
  document.querySelector("#turn-indicator").classList.toggle("live", Boolean(active && !game.gameOver && !paused && !busy));
  document.querySelector("#turn-indicator").classList.toggle("thinking", Boolean(active && !game.gameOver && !paused && busy));
  document.querySelector("#pause-button").textContent = paused ? "RESUME" : "PAUSE";
  document.querySelector("#pause-button").hidden = isHuman;
  document.querySelector("#pause-button").disabled = !active || isHuman || game.gameOver;
  document.querySelector("#restart-button").disabled = (!dqn && !isHuman) || busy;
  document.querySelector("#game-mode-label").textContent = isHuman ? "HUMAN PLAY" : "AI AUTOPLAY";
  document.querySelector("#game-layout").setAttribute("aria-label", `${isHuman ? "Human" : "AI"} Five or More game`);
  document.querySelector("#score-heading").textContent = isHuman ? "YOUR SCORE" : "AI SCORE";
  document.querySelector("#score-player-name").textContent = isHuman ? "YOU" : "TRAINED DQN";
  document.querySelector("#move-guide-title").textContent = isHuman ? "HOW TO PLAY" : "HOW TO FOLLOW A MOVE";
  document.querySelector("#move-guide-text").textContent = isHuman
    ? "Select one of your orbs, then choose an empty cell connected by a clear path."
    : "Watch the selected orb travel one glowing cell at a time to its destination.";
  document.querySelector("#footer-mode-label").textContent = isHuman ? "PLAY AT YOUR OWN PACE" : "POWERED BY YOUR TRAINED DQN";
  document.querySelector("#play-again-label").textContent = isHuman ? "PLAY AGAIN" : "WATCH ANOTHER RUN";

  if (moveAnimation) {
    boardNote.textContent = `Moving ${COLORS[moveAnimation.color]} orb ${coordinate(moveAnimation.source)} → ${coordinate(moveAnimation.destination)} · one cell at a time`;
  } else if (active && game.lastMove) {
    const from = coordinate(game.lastMove.source);
    const to = coordinate(game.lastMove.destination);
    boardNote.textContent = game.lastMove.score
      ? `Line cleared: +${game.lastMove.score} points · ${game.lastMove.lineLength || game.bestLine} connected`
      : `${isHuman ? "You moved" : "AI moved"} ${from} → ${to} · glowing cells show the route`;
  } else if (isHuman) {
    boardNote.textContent = game.selected === null ? "Select an orb to make your move." : `Selected ${coordinate(game.selected)} · now choose an empty destination.`;
  } else {
    boardNote.textContent = "The AI’s move path will appear here.";
  }
  updateSummary();
}

function handleCellClick(index) {
  if (!game || game.mode !== "human" || game.gameOver || busy) return;
  const color = game.board[index];
  if (game.selected === null || color !== 0) {
    if (color) {
      game.selected = index;
      render();
    } else if (game.selected === null) {
      showToast("Choose an orb before choosing its destination.");
    }
    return;
  }

  const source = game.selected;
  const path = findPath(game.board, source, index);
  if (!path) {
    showToast("That cell is blocked. Choose an empty cell connected by a clear path.");
    return;
  }
  const result = playMove(game, source, index);
  if (!result.ok) {
    showToast(result.reason, true);
    return;
  }
  render();
  if (result.score) showToast(`You clear a line — +${result.score} points.`);
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
  if (playMode === "ai" && !dqn) {
    showToast("The trained DQN is still loading. Try again in a moment.", true);
    return;
  }
  stopScheduledMove();
  paused = false;
  game = createGame({ mode: playMode, difficulty, colorCount });
  document.querySelector("#setup-page").hidden = true;
  document.querySelector("#game-page").hidden = false;
  document.querySelector("#setup-link").classList.remove("active");
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (playMode === "ai") scheduleAIMove(650);
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

function updatePlayMode(mode) {
  playMode = mode;
  document.querySelectorAll("[data-mode]").forEach((button) => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  document.querySelector("#start-button").disabled = mode === "ai" && !dqn;
  document.querySelector("#start-button-label").textContent = mode === "human" ? "START HUMAN GAME" : "START AI GAME";
  document.querySelector("#mode-note").textContent = mode === "human"
    ? "Select an orb, then an empty reachable cell. Connect five or more matching orbs to score."
    : dqn
      ? `Trained ${dqn.meta.runId} · ${Number(dqn.meta.environmentSteps).toLocaleString()} training steps · runs locally in your browser.`
      : "Loading the trained model into your browser…";
  document.querySelector("#setup-note-text").textContent = mode === "human"
    ? "Move an orb along a clear path. Connect five or more same-color orbs to score."
    : "The DQN selects a piece, finds a clear path, and moves it. Connect five or more same-color orbs to score.";
}

document.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => updatePlayMode(button.dataset.mode));
});

cellButtons.forEach((cell, index) => {
  cell.addEventListener("click", () => handleCellClick(index));
});

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
  document.querySelector("#restart-button").disabled = false;
  updatePlayMode(playMode);
}).catch((error) => {
  statusDot.classList.add("error");
  statusDot.classList.remove("loading");
  modelStatus.textContent = "DQN UNAVAILABLE";
  document.querySelector("#mode-note").textContent = playMode === "human"
    ? "AI is unavailable, but human play is ready."
    : "Model load failed. Human play remains available.";
  document.querySelector("#start-button").disabled = playMode === "ai";
  showToast(error.message, true);
});
