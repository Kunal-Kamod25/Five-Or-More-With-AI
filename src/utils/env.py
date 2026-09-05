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


 # Step 3: Making a Move (step(action)).
    # step() runs every single turn when the AI makes aa move.
    def step(self, action):

        # 1. Decode the Action.
        # The AI doesn't give us (x,y) coordinates. It just spits out a single number between 0 & 6560
        # We have to do a tiny bit of math to figure out what that number means.
        # This math turns the single number back into a "Start Square" and an "End square".
        start_square = action // 81 # integer division
        end_square = action % 81 # remainder

        # Now we have to turn those square numbers into (x,y) coordinates.
        start_x = start_square // 9
        start_y = start_square % 9

        end_x = end_square // 9
        end_y = end_square % 9

        # 2. Execute The Move(Simplified for now)
        # we grab the color of the ball at the start square.
        color_moving = self.state[start_x][start_y]

        # We erase the ball from the start Square (set it to 0)
        self.state[start_x][start_y] = 0

        # We place the ball on the end square
        self.state[end_x][end_y] = color_moving

        # 3. Calculate Rewards 1 And Game Over (placeholders)
        # Did the AI do a good job? (we will hook this up to the Rust Game Engine later).
        # for now, let's just give it a reward of 0
        reward = 0.0 

        # Is the game over? (Did the board get completely full?)
        done = false

        # Did the game run out of time? (Gymnasium requires this, we usually just say false).
        truncated = false

        # 4. Return the results to the AI
        # We must return exactly this 5 things every time.
        info = {}
        return self.state, reward, done, truncated, info


# a Step 4: The Rule Enforcer (action_masks())
    # action_masks() runs before the AI makes a move, to tell it what moves are allowed.
    def action_masks(self):

        #We start by assuming All 6561 moves are Illegal (false).
        #We Create a giant list of 6561 "False".
        valid_actions = np.zeros(6561, dtype=np.int8)

        # Now we check every single possible start square (0 to 80)
        for start_square in range(81):
            # We turn the start square number into(x,y)Coordinates
            start_x = start_square // 9
            start_y = start_square % 9

            #Rule 1: You can't move an empty square!
            # if the start square is empty (0), we just skip it.
            if self.state[start_x][start_y] == 0:
                continue

            # If there Is a ball on the start square, we check every possible end square(0 to 80)
            for end_square in range(81):
                # We turn the end square number into (x,y) coordinates
                end_x = end_square // 9
                end_y = end_square % 9

            # Rule 2: You can't move a ball onto a square that already has a ball !
            # if the end square is empty (0)..
            if self.state[end_x][end_y] == 0:

                # (later: Rule 3: Ask Rust if there is a clear path to walk there!)
                # for now, we will say this move is Legal.

                # We Calculate the single action number(0 to  6560) 
                action_number = (start_square * 81) + end_square

                # We flip the specific action false to true! 
                valid_actions[action_nimber] = 1

        # we had this checklist of True / False to use AI.
        return valid_actions