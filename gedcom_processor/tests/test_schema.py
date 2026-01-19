"""Tests for output schema helpers."""

import unittest
import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.schema import make_person, make_family_entry, family_to_current


class TestMakePerson(unittest.TestCase):
    """Tests for make_person helper."""

    def test_make_person_with_all_fields(self):
        """make_person creates dict with all fields."""
        person = make_person(
            first_name="John",
            last_name="Doe",
            birth="1850",
            death="1920"
        )
        self.assertEqual(person, {
            "first_name": "John",
            "last_name": "Doe",
            "birth": "1850",
            "death": "1920"
        })

    def test_make_person_with_none_values(self):
        """make_person handles None values."""
        person = make_person(
            first_name="John",
            last_name="Doe",
            birth="1850",
            death=None
        )
        self.assertEqual(person, {
            "first_name": "John",
            "last_name": "Doe",
            "birth": "1850",
            "death": None
        })

    def test_make_person_with_child_flag(self):
        """make_person can include child flag."""
        person = make_person(
            first_name="John",
            last_name="Doe",
            birth="1850",
            death="1920",
            child=True
        )
        self.assertTrue(person["child"])


class TestMakeFamilyEntry(unittest.TestCase):
    """Tests for make_family_entry helper."""

    def test_make_family_entry_structure(self):
        """make_family_entry creates cache entry with id field."""
        subject = make_person("John", "Doe", "1850", "1920")
        spouse = make_person("Jane", "Smith", "1855", "1925")

        entry = make_family_entry(
            family_id="I001",
            subject=subject,
            spouse=spouse,
            subject_parents={"father": None, "mother": None},
            spouse_parents={"father": None, "mother": None},
            children=[]
        )

        self.assertEqual(entry["id"], "I001")
        self.assertEqual(entry["subject"], subject)
        self.assertEqual(entry["spouse"], spouse)
        self.assertNotIn("last_family_id", entry)


class TestFamilyToCurrent(unittest.TestCase):
    """Tests for family_to_current helper."""

    def test_family_to_current_transforms_id(self):
        """family_to_current converts id to last_family_id."""
        entry = {
            "id": "I001",
            "subject": {"first_name": "John"},
            "spouse": {"first_name": "Jane"},
            "subject_parents": {},
            "spouse_parents": {},
            "children": []
        }

        current = family_to_current(entry)

        self.assertEqual(current["last_family_id"], "I001")
        self.assertNotIn("id", current)
        self.assertEqual(current["subject"], {"first_name": "John"})


if __name__ == "__main__":
    unittest.main()
