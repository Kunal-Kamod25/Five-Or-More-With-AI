"""Unit tests for Ray-based distributed environment manager."""

import unittest
from game.rl.ray_env import RayEnvManager

try:
    import ray
except ImportError:
    ray = None


class RayEnvManagerTests(unittest.TestCase):
    def setUp(self):
        if ray is None:
            self.skipTest("Ray is not installed.")

    def tearDown(self):
        if ray is not None and ray.is_initialized():
            ray.shutdown()

    def test_ray_env_lifecycle(self):
        with RayEnvManager(num_workers=2, difficulty="Easy", base_seed=123) as manager:
            self.assertEqual(manager.num_workers, 2)
            states, legal_actions_list = manager.reset()
            self.assertEqual(len(states), 2)
            self.assertEqual(len(legal_actions_list), 2)
            self.assertTrue(len(legal_actions_list[0]) > 0)

            # Choose valid actions
            actions = [legal_actions_list[0][0], legal_actions_list[1][0]]
            results = manager.step(actions)

            self.assertEqual(len(results), 2)
            for res in results:
                self.assertIn("state", res)
                self.assertIn("action", res)
                self.assertIn("reward", res)
                self.assertIn("next_state", res)
                self.assertIn("done", res)

            # Test reset_workers
            manager.reset_workers([0])
            self.assertIsNotNone(manager.current_states[0])

    def test_node_workers_configuration(self):
        with RayEnvManager(
            node_workers="127.0.0.1:1",
            difficulty="Easy",
            base_seed=123,
        ) as manager:
            self.assertEqual(manager.num_workers, 1)
            states, legals = manager.reset()
            self.assertEqual(len(states), 1)


if __name__ == "__main__":
    unittest.main()

