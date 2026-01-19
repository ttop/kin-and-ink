"""Tests for the GEDCOM data source."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.sources.gedcom_source import GedcomSource
from src.sources.base import FamilySource


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_family.ged"


class TestGedcomSourceBasic(unittest.TestCase):
    """Tests for basic GEDCOM loading."""

    def test_gedcom_source_implements_interface(self):
        """GedcomSource implements FamilySource interface."""
        source = GedcomSource(FIXTURE_PATH)
        self.assertIsInstance(source, FamilySource)

    def test_gedcom_source_loads_file(self):
        """GedcomSource can load a GEDCOM file."""
        source = GedcomSource(FIXTURE_PATH)
        # Should not raise
        self.assertIsNotNone(source)


class TestGetEligibleIds(unittest.TestCase):
    """Tests for get_eligible_ids."""

    def test_get_eligible_ids_returns_eligible_people(self):
        """get_eligible_ids returns people meeting criteria."""
        source = GedcomSource(FIXTURE_PATH)
        eligible = source.get_eligible_ids()

        # I001 (John Doe) should be eligible: has spouse, parents, children
        self.assertIn("@I001@", eligible)

    def test_get_eligible_ids_excludes_ineligible(self):
        """get_eligible_ids excludes people missing requirements."""
        source = GedcomSource(FIXTURE_PATH)
        eligible = source.get_eligible_ids()

        # I008 (Sarah Doe) has no spouse, should not be eligible
        self.assertNotIn("@I008@", eligible)


class TestGetFamily(unittest.TestCase):
    """Tests for get_family."""

    def test_get_family_returns_subject(self):
        """get_family includes subject data."""
        source = GedcomSource(FIXTURE_PATH)
        family = source.get_family("@I001@")

        self.assertEqual(family["subject"]["first_name"], "John")
        self.assertEqual(family["subject"]["last_name"], "Doe")
        self.assertEqual(family["subject"]["birth"], "1850")
        self.assertEqual(family["subject"]["death"], "1920")

    def test_get_family_returns_spouse(self):
        """get_family includes spouse data."""
        source = GedcomSource(FIXTURE_PATH)
        family = source.get_family("@I001@")

        self.assertEqual(family["spouse"]["first_name"], "Jane")
        self.assertEqual(family["spouse"]["last_name"], "Smith")

    def test_get_family_returns_subject_parents(self):
        """get_family includes subject's parents."""
        source = GedcomSource(FIXTURE_PATH)
        family = source.get_family("@I001@")

        self.assertEqual(family["subject_parents"]["father"]["first_name"], "William")
        self.assertEqual(family["subject_parents"]["mother"]["first_name"], "Mary")

    def test_get_family_returns_spouse_parents(self):
        """get_family includes spouse's parents."""
        source = GedcomSource(FIXTURE_PATH)
        family = source.get_family("@I001@")

        self.assertEqual(family["spouse_parents"]["father"]["first_name"], "Robert")
        self.assertEqual(family["spouse_parents"]["mother"]["first_name"], "Elizabeth")

    def test_get_family_returns_children(self):
        """get_family includes children with child flag."""
        source = GedcomSource(FIXTURE_PATH)
        family = source.get_family("@I001@")

        children = family["children"]
        self.assertEqual(len(children), 2)

        # Find James (who has a spouse)
        james_entry = next((c for c in children if c["first"]["first_name"] == "James"), None)
        self.assertIsNotNone(james_entry)
        self.assertTrue(james_entry["first"]["child"])
        self.assertEqual(james_entry["second"]["first_name"], "Alice")


if __name__ == "__main__":
    unittest.main()
