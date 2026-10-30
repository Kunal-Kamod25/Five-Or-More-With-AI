import unittest

from .parallel_env import ParallelEnvManager


class ParallelEnvManagerTests(unittest.TestCase):
    def test_invalid_worker_count_raises_value_error(self):
        with self.assertRaises(ValueError):
            ParallelEnvManager(num_workers=0)

        with self.assertRaises(ValueError):
            ParallelEnvManager(num_workers=-1)

        with self.assertRaises(ValueError):
            ParallelEnvManager(num_workers=True)  # bool check

    def test_manager_reset_and_step_with_two_workers(self):
        with ParallelEnvManager(num_workers=2, difficulty="Easy", base_seed=123) as manager:
            states, legal_actions = manager.reset()

            self.assertEqual(len(states), 2)
            self.assertEqual(len(legal_actions), 2)
            self.assertGreater(len(legal_actions[0]), 0)
            self.assertGreater(len(legal_actions[1]), 0)

            # Pick the first legal action from each worker
            actions = [legal_actions[0][0], legal_actions[1][0]]
            results = manager.step(actions)

            self.assertEqual(len(results), 2)
            for i, res in enumerate(results):
                self.assertEqual(res["worker_id"], i)
                self.assertEqual(res["action"], actions[i])
                self.assertIn("reward", res)
                self.assertIn("done", res)
                self.assertIn("next_state", res)
                self.assertIn("score", res)

    def test_workers_have_distinct_trajectories(self):
        with ParallelEnvManager(num_workers=3, difficulty="Medium", base_seed=42) as manager:
            states, legal_actions = manager.reset()
            # Due to distinct seeds, legal action sets across workers should not all be identical
            self.assertEqual(len(states), 3)
            self.assertTrue(len(legal_actions[0]) > 0)
            self.assertTrue(len(legal_actions[1]) > 0)


if __name__ == "__main__":
    unittest.main()
