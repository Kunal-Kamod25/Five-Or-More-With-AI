"""Root launcher to watch the trained DQN agent play visually in the Pygame window."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from game.rl.play_agent import main

if __name__ == "__main__":
    main()
