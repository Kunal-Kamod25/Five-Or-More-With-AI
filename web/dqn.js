const SIZE = 9;
const CELLS = SIZE * SIZE;

function relu(values) {
  for (let i = 0; i < values.length; i += 1) values[i] = Math.max(0, values[i]);
  return values;
}

function conv2d(input, inputChannels, weights, bias, outputChannels) {
  const output = new Float32Array(outputChannels * CELLS);
  for (let oc = 0; oc < outputChannels; oc += 1) {
    for (let y = 0; y < SIZE; y += 1) {
      for (let x = 0; x < SIZE; x += 1) {
        let value = bias[oc];
        for (let ic = 0; ic < inputChannels; ic += 1) {
          for (let ky = 0; ky < 3; ky += 1) {
            const iy = y + ky - 1;
            if (iy < 0 || iy >= SIZE) continue;
            for (let kx = 0; kx < 3; kx += 1) {
              const ix = x + kx - 1;
              if (ix < 0 || ix >= SIZE) continue;
              const wi = (((oc * inputChannels + ic) * 3 + ky) * 3) + kx;
              value = Math.fround(value + Math.fround(input[ic * CELLS + iy * SIZE + ix] * weights[wi]));
            }
          }
        }
        output[oc * CELLS + y * SIZE + x] = Math.max(0, value);
      }
    }
  }
  return output;
}

function dense(input, weights, bias, outputSize) {
  const inputSize = input.length;
  const output = new Float32Array(outputSize);
  for (let o = 0; o < outputSize; o += 1) {
    let value = bias[o];
    const offset = o * inputSize;
    for (let i = 0; i < inputSize; i += 1) {
      value = Math.fround(value + Math.fround(input[i] * weights[offset + i]));
    }
    output[o] = value;
  }
  return output;
}

export class BrowserDQN {
  constructor(model) {
    if (model.format !== "five-or-more-dqn-v1") throw new Error("Unsupported DQN model format.");
    this.meta = model.meta;
    this.weights = Object.fromEntries(
      Object.entries(model.weights).map(([name, layer]) => [
        name,
        Object.fromEntries(Object.entries(layer).map(([key, values]) => [key, new Float32Array(values)])),
      ]),
    );
    if (this.meta.boardSize !== SIZE || this.meta.colorChannels !== 7) {
      throw new Error("The DQN model architecture does not match this game.");
    }
  }

  scoreActions(state, actions) {
    if (!Array.isArray(state) || state.length !== CELLS) throw new TypeError("DQN state must contain 81 cells.");
    if (!actions.length) return [];
    const input = new Float32Array(7 * CELLS);
    for (let cell = 0; cell < CELLS; cell += 1) {
      const color = state[cell];
      if (color > 0) input[(color - 1) * CELLS + cell] = 1;
    }

    const conv1 = this.weights.conv1;
    const feature1 = conv2d(input, 7, conv1.weight, conv1.bias, 2);
    const conv2 = this.weights.conv2;
    const featureMaps = conv2d(feature1, 2, conv2.weight, conv2.bias, 4);
    const summaryLayer = this.weights.board_summary_layer;
    const summary = relu(dense(featureMaps, summaryLayer.weight, summaryLayer.bias, 32));
    const hiddenLayer = this.weights.action_scorer_0;
    const outputLayer = this.weights.action_scorer_2;

    return actions.map((action) => {
      const source = Math.floor(action / CELLS);
      const destination = action % CELLS;
      const actionFeatures = new Float32Array(40);
      for (let channel = 0; channel < 4; channel += 1) {
        actionFeatures[channel] = featureMaps[channel * CELLS + source];
        actionFeatures[4 + channel] = featureMaps[channel * CELLS + destination];
      }
      actionFeatures.set(summary, 8);
      const hidden = relu(dense(actionFeatures, hiddenLayer.weight, hiddenLayer.bias, 64));
      return dense(hidden, outputLayer.weight, outputLayer.bias, 1)[0];
    });
  }

  chooseAction(state, actions, avoidActions = []) {
    if (!actions.length) return null;
    const avoided = new Set(avoidActions);
    const candidates = actions.filter((action) => !avoided.has(action));
    const pool = candidates.length ? candidates : actions;
    const scores = this.scoreActions(state, pool);
    let bestIndex = 0;
    for (let i = 1; i < scores.length; i += 1) {
      if (scores[i] > scores[bestIndex]) bestIndex = i;
    }
    return pool[bestIndex];
  }
}

export async function loadBrowserDQN() {
  const response = await fetch("./model.json", { cache: "force-cache" });
  if (!response.ok) throw new Error(`Could not load the trained model (HTTP ${response.status}).`);
  return new BrowserDQN(await response.json());
}
