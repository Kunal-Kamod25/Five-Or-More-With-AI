import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from config.config_loader import load_config, validate_config
from experiment_manager import ExperimentManager


class ConfigLoaderTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.valid_config_path = self.repo_root / "config" / "config.json"
        self.default_config = load_config(self.valid_config_path)

    def test_valid_config_loads_successfully(self):
        config = load_config(self.valid_config_path)
        self.assertIn("training", config)
        self.assertIn("dqn", config)
        self.assertIn("exploration", config)
        self.assertIn("network", config)
        self.assertIn("environment", config)
        self.assertIn("reward", config)

    def test_missing_config_file_is_handled_correctly(self):
        missing = self.repo_root / "config" / "does_not_exist.json"
        with self.assertRaises(FileNotFoundError):
            load_config(missing)

    def test_invalid_json_is_handled_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text("{not valid json}", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_missing_required_configuration_section_is_detected(self):
        config = self.default_config.copy()
        config.pop("exploration")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exploration"):
                load_config(path)

    def test_invalid_parameter_type_is_detected(self):
        config = self.default_config.copy()
        config["training"]["episodes"] = "bad"
        with self.assertRaisesRegex(ValueError, "episodes"):
            validate_config(config)

    def test_invalid_gamma_is_detected(self):
        config = self.default_config.copy()
        config["dqn"]["gamma"] = 1.5
        with self.assertRaisesRegex(ValueError, "gamma"):
            validate_config(config)

    def test_invalid_learning_rate_is_detected(self):
        config = self.default_config.copy()
        config["dqn"]["learning_rate"] = 0
        with self.assertRaisesRegex(ValueError, "learning_rate"):
            validate_config(config)

    def test_invalid_episode_count_is_detected(self):
        config = self.default_config.copy()
        config["training"]["episodes"] = 0
        with self.assertRaisesRegex(ValueError, "episodes"):
            validate_config(config)

    def test_invalid_difficulty_is_detected(self):
        config = self.default_config.copy()
        config["environment"]["difficulty"] = "Impossible"
        with self.assertRaisesRegex(ValueError, "difficulty"):
            validate_config(config)


class ExperimentManagerTests(unittest.TestCase):
    def setUp(self):
        self.base_config = load_config(Path(__file__).resolve().parents[1] / "config" / "config.json")

    def test_experiment_directory_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            manager = ExperimentManager(config=self.base_config, base_dir=base_dir)
            self.assertTrue(manager.run_dir.exists())
            self.assertTrue(manager.config_path.exists())
            self.assertTrue(manager.results_path.exists())
            self.assertTrue(manager.metrics_path.exists())
            self.assertTrue(manager.run_id.startswith("run_"))

    def test_run_ids_are_unique(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            first = ExperimentManager(config=self.base_config, base_dir=base_dir)
            second = ExperimentManager(config=self.base_config, base_dir=base_dir)
            self.assertNotEqual(first.run_id, second.run_id)
            self.assertEqual(first.run_id, "run_001")
            self.assertEqual(second.run_id, "run_002")

    def test_existing_experiment_directories_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            existing = base_dir / "run_001"
            existing.mkdir(parents=True)
            marker = existing / "marker.txt"
            marker.write_text("keep me", encoding="utf-8")

            manager = ExperimentManager(config=self.base_config, base_dir=base_dir)
            self.assertEqual(manager.run_id, "run_002")
            self.assertTrue(marker.exists())

    def test_configuration_snapshot_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            manager = ExperimentManager(config=self.base_config, base_dir=base_dir)
            snapshot = json.loads(manager.config_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot, self.base_config)
            self.assertTrue(snapshot["training"]["episodes"] > 0)

    def test_changing_main_config_does_not_modify_old_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            config = json.loads(json.dumps(self.base_config))
            manager = ExperimentManager(config=config, base_dir=base_dir)
            config["training"]["episodes"] = 999

            snapshot = json.loads(manager.config_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["training"]["episodes"], 10000)
            self.assertNotEqual(snapshot["training"]["episodes"], config["training"]["episodes"])

    def test_results_can_be_saved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            manager = ExperimentManager(config=self.base_config, base_dir=base_dir)
            manager.save_results(
                status="completed",
                final_score=250,
                average_score=12.5,
                best_score=250,
            )
            results = json.loads(manager.results_path.read_text(encoding="utf-8"))
            self.assertEqual(results["status"], "completed")
            self.assertEqual(results["final_score"], 250)
            self.assertEqual(results["average_score"], 12.5)

    def test_metrics_can_be_recorded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            manager = ExperimentManager(config=self.base_config, base_dir=base_dir)
            manager.log_episode(
                episode=1,
                score=10,
                reward=2.5,
                steps=15,
                done=True,
                epsilon=0.9,
                loss=0.25,
                average_score=10.0,
                average_reward=2.5,
            )
            with manager.metrics_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["episode"], "1")
            self.assertEqual(rows[0]["score"], "10")
            self.assertEqual(rows[0]["reward"], "2.5")
            self.assertEqual(rows[0]["epsilon"], "0.9")

    def test_metrics_are_written_correctly_to_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "experiments"
            manager = ExperimentManager(config=self.base_config, base_dir=base_dir)
            manager.log_episode(episode=1, score=10, reward=2.0, steps=12, done=False, epsilon=0.8, loss=0.4)
            manager.log_episode(episode=2, score=20, reward=3.0, steps=18, done=True, epsilon=0.7, loss=0.3)
            with manager.metrics_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["episode"], "1")
            self.assertEqual(rows[1]["episode"], "2")
            self.assertEqual(rows[1]["done"], "True")

    def test_no_pygame_dependency_is_required(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import config; import experiment_manager; "
                    "import sys; assert 'pygame' not in sys.modules"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
