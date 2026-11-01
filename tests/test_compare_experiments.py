import csv
import json
import tempfile
import unittest
from pathlib import Path

from game.rl.compare_experiments import collect_experiments, write_comparison


class CompareExperimentsTests(unittest.TestCase):
    def test_run_config_and_metrics_are_compared(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run = Path(tmpdir) / "run_001"
            run.mkdir()
            (run / "config.json").write_text(
                json.dumps(
                    {
                        "environment": {"difficulty": "Easy"},
                        "training": {"num_workers": 2},
                        "reward": {"score_per_point": 0.2},
                    }
                ),
                encoding="utf-8",
            )
            (run / "results.json").write_text(
                json.dumps(
                    {
                        "run_id": "run_001",
                        "status": "completed",
                        "config_hash": "abc123",
                        "episodes": 10,
                        "average_score": 20,
                        "best_score": 42,
                        "average_reward": 2,
                        "best_evaluation": {"average_score": 25},
                        "random_baseline": {"average_score": 12},
                        "evaluation_score_delta": 13,
                    }
                ),
                encoding="utf-8",
            )

            rows = collect_experiments(tmpdir)
            output = write_comparison(rows, Path(tmpdir) / "comparison.csv")

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["difficulty"], "Easy")
            self.assertEqual(rows[0]["evaluation_score_delta"], 13)
            self.assertIn('"score_per_point":0.2', rows[0]["config_json"])
            with output.open(encoding="utf-8", newline="") as handle:
                saved_rows = list(csv.DictReader(handle))
            self.assertEqual(saved_rows[0]["average_score"], "20")


if __name__ == "__main__":
    unittest.main()
