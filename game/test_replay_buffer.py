import unittest

from .replay_buffer import ExperienceReplayBuffer


class ExperienceReplayBufferTests(unittest.TestCase):
    def test_transition_can_be_added_and_retrieved(self):
        buffer = ExperienceReplayBuffer(capacity=3)
        transition = {
            "state": [[0, 1], [2, 0]],
            "action": 17,
            "reward": 1.5,
            "next_state": [[0, 0], [2, 3]],
            "done": False,
            "next_legal_actions": [10, 11],
        }

        buffer.append(transition)

        self.assertEqual(len(buffer), 1)
        self.assertEqual(buffer.sample(1)[0]["action"], 17)
        self.assertEqual(buffer.sample(1)[0]["next_legal_actions"], [10, 11])

    def test_state_and_next_state_are_copied(self):
        buffer = ExperienceReplayBuffer(capacity=2)
        state = [[0, 1], [2, 3]]
        next_state = [[0, 0], [1, 1]]
        transition = {
            "state": state,
            "action": 5,
            "reward": 2.0,
            "next_state": next_state,
            "done": True,
            "next_legal_actions": [],
        }

        buffer.append(transition)
        state[0][0] = 9
        next_state[1][1] = 7

        stored = buffer.sample(1)[0]
        self.assertEqual(stored["state"], [[0, 1], [2, 3]])
        self.assertEqual(stored["next_state"], [[0, 0], [1, 1]])

    def test_next_action_list_is_copied(self):
        buffer = ExperienceReplayBuffer(capacity=2)
        actions = [1, 2, 3]
        transition = {
            "state": [[0, 0], [0, 0]],
            "action": 4,
            "reward": 0.0,
            "next_state": [[0, 0], [0, 0]],
            "done": False,
            "next_legal_actions": actions,
        }

        buffer.append(transition)
        actions.append(99)

        self.assertEqual(buffer.sample(1)[0]["next_legal_actions"], [1, 2, 3])

    def test_buffer_never_exceeds_capacity(self):
        buffer = ExperienceReplayBuffer(capacity=2)
        for index in range(5):
            buffer.append({
                "state": [[index]],
                "action": index,
                "reward": float(index),
                "next_state": [[index + 1]],
                "done": False,
                "next_legal_actions": [index],
            })

        self.assertEqual(len(buffer), 2)

    def test_oldest_transition_is_discarded_when_full(self):
        buffer = ExperienceReplayBuffer(capacity=2)
        buffer.append({
            "state": [[1]],
            "action": 1,
            "reward": 1.0,
            "next_state": [[2]],
            "done": False,
            "next_legal_actions": [1],
        })
        buffer.append({
            "state": [[2]],
            "action": 2,
            "reward": 2.0,
            "next_state": [[3]],
            "done": False,
            "next_legal_actions": [2],
        })
        buffer.append({
            "state": [[3]],
            "action": 3,
            "reward": 3.0,
            "next_state": [[4]],
            "done": False,
            "next_legal_actions": [3],
        })

        stored = buffer.sample(2)
        actions = {entry["action"] for entry in stored}
        self.assertEqual(actions, {2, 3})
        self.assertNotIn(1, actions)

    def test_sampled_experiences_are_from_buffer(self):
        buffer = ExperienceReplayBuffer(capacity=3)
        for action in (10, 20, 30):
            buffer.append({
                "state": [[action]],
                "action": action,
                "reward": float(action),
                "next_state": [[action + 1]],
                "done": False,
                "next_legal_actions": [action],
            })

        sample = buffer.sample(3)
        actions = sorted(item["action"] for item in sample)
        self.assertEqual(actions, [10, 20, 30])

    def test_sampling_is_without_replacement(self):
        buffer = ExperienceReplayBuffer(capacity=4, seed=2)
        for action in range(4):
            buffer.append({
                "state": [[action]],
                "action": action,
                "reward": 0.0,
                "next_state": [[action + 1]],
                "done": False,
                "next_legal_actions": [action],
            })

        sample = buffer.sample(4)
        self.assertEqual(len({item["action"] for item in sample}), 4)

    def test_sampling_smaller_batch_raises_error_when_insufficient_experiences(self):
        buffer = ExperienceReplayBuffer(capacity=2)
        buffer.append({
            "state": [[1]],
            "action": 1,
            "reward": 1.0,
            "next_state": [[2]],
            "done": False,
            "next_legal_actions": [1],
        })

        with self.assertRaises(ValueError):
            buffer.sample(2)

    def test_invalid_capacity_and_batch_size_raise_clear_errors(self):
        with self.assertRaises(ValueError):
            ExperienceReplayBuffer(capacity=0)
        with self.assertRaises(ValueError):
            ExperienceReplayBuffer(capacity=-1)
        with self.assertRaises(ValueError):
            ExperienceReplayBuffer(capacity=3).sample(0)
        with self.assertRaises(ValueError):
            ExperienceReplayBuffer(capacity=3).sample(-2)

    def test_sampling_empty_buffer_raises_value_error(self):
        with self.assertRaises(ValueError):
            ExperienceReplayBuffer(capacity=2).sample(1)

    def test_terminal_transition_and_empty_next_actions_are_preserved(self):
        buffer = ExperienceReplayBuffer(capacity=3)
        transition = {
            "state": [[1, 2], [3, 4]],
            "action": 42,
            "reward": -2.0,
            "next_state": [[0, 0], [0, 0]],
            "done": True,
            "next_legal_actions": [],
        }

        buffer.append(transition)
        stored = buffer.sample(1)[0]
        self.assertTrue(stored["done"])
        self.assertEqual(stored["next_legal_actions"], [])

    def test_fixed_seed_makes_sampling_deterministic(self):
        first_buffer = ExperienceReplayBuffer(capacity=4, seed=7)
        for action in range(4):
            first_buffer.append({
                "state": [[action]],
                "action": action,
                "reward": float(action),
                "next_state": [[action + 1]],
                "done": False,
                "next_legal_actions": [action],
            })

        second_buffer = ExperienceReplayBuffer(capacity=4, seed=7)
        for action in range(4):
            second_buffer.append({
                "state": [[action]],
                "action": action,
                "reward": float(action),
                "next_state": [[action + 1]],
                "done": False,
                "next_legal_actions": [action],
            })

        first = [item["action"] for item in first_buffer.sample(4)]
        second = [item["action"] for item in second_buffer.sample(4)]
        self.assertEqual(first, second)

    def test_buffer_does_not_require_cuda(self):
        buffer = ExperienceReplayBuffer(capacity=2)
        buffer.append({
            "state": [[0, 1]],
            "action": 3,
            "reward": 1.0,
            "next_state": [[1, 2]],
            "done": False,
            "next_legal_actions": [3],
        })
        self.assertEqual(buffer.sample(1)[0]["action"], 3)


if __name__ == "__main__":
    unittest.main()
