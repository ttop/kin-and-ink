"""Tests for the FamilySource abstract base class."""

import unittest
from abc import ABC

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.sources.base import FamilySource


class TestFamilySourceInterface(unittest.TestCase):
    """Tests for the FamilySource abstract base class."""

    def test_family_source_is_abstract(self):
        """FamilySource cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            FamilySource()

    def test_family_source_requires_get_eligible_ids(self):
        """Subclasses must implement get_eligible_ids."""
        class IncompleteSource(FamilySource):
            def get_family(self, person_id: str) -> dict:
                return {}

        with self.assertRaises(TypeError):
            IncompleteSource()

    def test_family_source_requires_get_family(self):
        """Subclasses must implement get_family."""
        class IncompleteSource(FamilySource):
            def get_eligible_ids(self) -> list[str]:
                return []

        with self.assertRaises(TypeError):
            IncompleteSource()

    def test_complete_subclass_can_be_instantiated(self):
        """A complete subclass can be instantiated."""
        class CompleteSource(FamilySource):
            def get_eligible_ids(self) -> list[str]:
                return ["I001"]

            def get_family(self, person_id: str) -> dict:
                return {"subject": {"first_name": "Test"}}

        source = CompleteSource()
        self.assertEqual(source.get_eligible_ids(), ["I001"])
        self.assertEqual(source.get_family("I001"), {"subject": {"first_name": "Test"}})


if __name__ == "__main__":
    unittest.main()
