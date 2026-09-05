#The Setup (__init__)
import gymnasium as gym
from gymnasium import spaces
import numpy as np

# we create our custom Environment class and tell it to inherit the rules of gymnasium.Env
class FiveOrMoreEnv(gym.Env):
    # __init__ is the setup Function. it runs once when the game starts.gym
    def __init__(self):
        super().__init__()

        # The Observation Space (What the AI Sees)
        # we tell the AI: "You will see a 9X9 grid. the number in the grid."
        # will only ever be between 0 (empty) and 7 (the 7 colors).
        self.observation_space = spaces.Box(
            low=0,
            high=7,
            shape=(9,9),
            dtype=np.int32
        )

        # The Action Space(What AI can do )
        # The board has 81 squares(9X9).
        # To make a move, Ai picks a "start" squares(81 choices) and an "end" square (81 choices).
        # 81 * 81 = 6561 total possible moves it could ever try.
        self.action_space = spaces.Discrete(6561)

        # Later, we will connect our Rust game engine right here!)
        print("Five-or-More Environment Initialized..")



# Step 2: Starting a New Game (reset()). This function wipes the board completely clean, drops 3 new random colored balls onto it, and hands the fresh board back to the AI so the game can begin.
    def reset(self,seed=None,options=None): # reset() is called every time a new game starts.
        super().reset(seed=seed) # Important for keeping track of random patterns
        
        # 1.Wipe the board clean
        # We create a 9*9 matrix filled entirely with 0's(empty spaces).
        # We save this as "self.state" so the environment remembers the board.
        self.state = np.zeros((9,9), dtype=np.int32)

        # 2.Drop 3 random balls
        #we loop 3 times to place 3 starting balls.
        for _ in range(3):
            # Pick a random X and Y coordinate between 0 and 8.range
            x = self.np_random.integers(0,9)
            y = self.np_random.integers(0,9)

            # Pick a random color (1 to 7)
            color = self.np_random.integers(1,8)

            #place the clocored ball on our board matrix
            self.state[x][y] = color
        
        # 3. Return the starting board to the AI
        # Gymnasium always requires us to return two things:
        # - The observation (our 9*9 matrix)
        # - An "Info" dictionary (we leave this empty for now)
        info = {}
        return self.state,info 
