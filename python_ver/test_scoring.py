import unittest

from .scoring import ScoreCalculator


class ScoreCalculatorTests(unittest.TestCase):
    def setUp(self):
        self.calculator = ScoreCalculator()

    def test_lengths_below_five_score_zero(self):
        for line_length in range(5):
            with self.subTest(line_length=line_length):
                self.assertEqual(self.calculator.calculate_score(line_length), 0)

    def test_scoring_lengths_five_through_nine(self):
        expected_scores = {
            5: 10,
            6: 12,
            7: 14,
            8: 16,
            9: 18,
        }
        for line_length, expected_score in expected_scores.items():
            with self.subTest(line_length=line_length):
                self.assertEqual(
                    self.calculator.calculate_score(line_length),
                    expected_score,
                )

    def test_lengths_above_nine_score_zero(self):
        for line_length in (10, 11, 100):
            with self.subTest(line_length=line_length):
                self.assertEqual(self.calculator.calculate_score(line_length), 0)

    def test_invalid_line_lengths_raise_value_error(self):
        for line_length in (-1, -5, True, False, 5.0, "5", None):
            with self.subTest(line_length=line_length):
                with self.assertRaises(ValueError):
                    self.calculator.calculate_score(line_length)


if __name__ == "__main__":
    unittest.main()
