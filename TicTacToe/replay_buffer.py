import random


class ReplayBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = []

    def add(self, state, action, reward, next_state, done):
        experience = (
            state,
            action,
            reward,
            next_state,
            done
        )

        self.buffer.append(experience)

        # Remove the oldest experience if the buffer is full
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def can_sample(self, batch_size):
        return len(self.buffer) >= batch_size

    def __len__(self):
        return len(self.buffer)


if __name__ == "__main__":
    buffer = ReplayBuffer(10)

    buffer.add(
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        4,
        0,
        [0, 0, 0, 0, 1, 0, 2, 0, 0],
        False
    )

    buffer.add(
        [1, 0, 2, 0, 1, 0, 2, 0, 0],
        8,
        1,
        [1, 0, 2, 0, 1, 0, 2, 0, 1],
        True
    )

    print("Buffer size:", len(buffer))

    print("Can sample 2:", buffer.can_sample(2))
    print("Can sample 32:", buffer.can_sample(32))

    samples = buffer.sample(2)

    print("Sampled experiences:")

    for experience in samples:
        print(experience)