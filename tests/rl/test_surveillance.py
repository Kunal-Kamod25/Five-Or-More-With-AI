"""Unit tests for TrainingSurveillance and resource telemetry."""

import json
import tempfile
import unittest
from pathlib import Path

from game.rl.surveillance import (
    TrainingSurveillance,
    format_duration,
    get_cpu_percent,
    get_process_memory_mb,
)


class SurveillanceTests(unittest.TestCase):
    def test_format_duration(self):
        self.assertEqual(format_duration(0), "00s")
        self.assertEqual(format_duration(45), "45s")
        self.assertEqual(format_duration(125), "02m 05s")
        self.assertEqual(format_duration(3665), "1h 01m 05s")
        self.assertEqual(format_duration(90065), "1d 1h 01m 05s")
        self.assertEqual(format_duration(-10), "0s")

    def test_resource_reading_helpers(self):
        ram = get_process_memory_mb()
        self.assertIsInstance(ram, float)
        self.assertGreater(ram, 0.0)

        cpu = get_cpu_percent()
        self.assertIsInstance(cpu, float)
        self.assertGreaterEqual(cpu, 0.0)

    def test_invalid_parameters_raise_error(self):
        with self.assertRaises(ValueError):
            TrainingSurveillance(total_episodes=0)
        with self.assertRaises(ValueError):
            TrainingSurveillance(total_episodes=10, interval=0)

    def test_surveillance_interval_and_final_reporting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "surveillance.jsonl"
            surveillance = TrainingSurveillance(
                total_episodes=4,
                interval=2,
                log_path=log_path,
                verbose=False,
            )

            # Episode 1: not interval -> None
            r1 = surveillance.record_episode(
                episode=1,
                steps=20,
                score=10.0,
                reward=9.0,
                loss=0.05,
                epsilon=0.99,
            )
            self.assertIsNone(r1)

            # Episode 2: interval -> returns report dict
            r2 = surveillance.record_episode(
                episode=2,
                steps=25,
                score=12.0,
                reward=11.0,
                loss=0.04,
                epsilon=0.98,
            )
            self.assertIsNotNone(r2)
            self.assertEqual(r2["episode"], 2)
            self.assertEqual(r2["total_episodes"], 4)
            self.assertEqual(r2["progress_percent"], 50.0)
            self.assertIn("eta_formatted", r2)
            self.assertIn("time_per_100_formatted", r2)
            self.assertIn("time_per_1000_formatted", r2)
            self.assertGreater(r2["ram_rss_mb"], 0.0)
            self.assertEqual(r2["best_score"], 12.0)
            self.assertEqual(r2["rolling_average_score"], 11.0)

            # Episode 3: not interval -> None
            r3 = surveillance.record_episode(
                episode=3,
                steps=15,
                score=0.0,
                reward=-0.015,
                loss=0.03,
                epsilon=0.97,
            )
            self.assertIsNone(r3)

            # Episode 4: final -> returns report dict
            r4 = surveillance.record_episode(
                episode=4,
                steps=30,
                score=10.0,
                reward=9.5,
                loss=0.02,
                epsilon=0.96,
            )
            self.assertIsNotNone(r4)
            self.assertEqual(r4["episode"], 4)
            self.assertEqual(r4["progress_percent"], 100.0)

            # Verify file was written
            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            parsed1 = json.loads(lines[0])
            parsed2 = json.loads(lines[1])
            self.assertEqual(parsed1["episode"], 2)
            self.assertEqual(parsed2["episode"], 4)


if __name__ == "__main__":
    unittest.main()
