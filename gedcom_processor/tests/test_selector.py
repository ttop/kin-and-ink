"""Tests for the family selector."""

import unittest
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.selector import select_family_id


class TestSelectFamilyId(unittest.TestCase):
    """Tests for select_family_id."""

    def test_select_from_single_option(self):
        """With one option, always returns it."""
        result = select_family_id(["I001"], last_id=None)
        self.assertEqual(result, "I001")

    def test_select_from_single_option_even_if_same_as_last(self):
        """With one option, returns it even if same as last."""
        result = select_family_id(["I001"], last_id="I001")
        self.assertEqual(result, "I001")

    def test_select_avoids_last_id(self):
        """With multiple options, avoids the last selected ID."""
        eligible = ["I001", "I002"]

        # Run many times to verify it never picks I001 when that was last
        for _ in range(50):
            result = select_family_id(eligible, last_id="I001")
            self.assertEqual(result, "I002")

    def test_select_with_no_last_id(self):
        """With no last ID, can pick any option."""
        eligible = ["I001", "I002", "I003"]
        results = set()

        # Run enough times to likely hit all options
        for _ in range(100):
            result = select_family_id(eligible, last_id=None)
            results.add(result)

        # Should have picked multiple different IDs
        self.assertGreater(len(results), 1)

    def test_select_empty_list_raises(self):
        """Empty eligible list raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            select_family_id([], last_id=None)
        self.assertIn("No eligible", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
