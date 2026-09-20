import unittest

from ledger.report import drawdown, pct_change, rolling_max, total


class TestTotal(unittest.TestCase):
    def test_sums(self):
        self.assertEqual(total([1, 2, 3]), 6)

    def test_empty(self):
        self.assertEqual(total([]), 0)


class TestPctChange(unittest.TestCase):
    def test_first_is_none(self):
        self.assertIsNone(pct_change([10, 20])[0])

    def test_doubling_is_100pct(self):
        self.assertAlmostEqual(pct_change([10, 20])[1], 100.0)

    def test_zero_base_is_none(self):
        self.assertIsNone(pct_change([0, 5])[1])


class TestRollingMax(unittest.TestCase):
    def test_rising_series(self):
        self.assertEqual(rolling_max([1, 2, 3, 4, 5], 3), [1, 2, 3, 4, 5])

    def test_flat_series(self):
        self.assertEqual(rolling_max([7, 7, 7], 2), [7, 7, 7])

    def test_window_one_on_rising_series(self):
        self.assertEqual(rolling_max([1, 2, 3], 1), [1, 2, 3])

    def test_rejects_zero_window(self):
        with self.assertRaises(ValueError):
            rolling_max([1, 2], 0)


class TestDrawdown(unittest.TestCase):
    def test_no_drawdown_on_rising_series(self):
        self.assertEqual(drawdown([1, 2, 3], 2), [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
