"""Tests for the families.json cache layer."""

import unittest
import sys
import json
import hashlib
import tempfile
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.cache import compute_file_hash, load_cache, save_cache, is_cache_valid


class TestComputeFileHash(unittest.TestCase):
    """Tests for compute_file_hash."""

    def test_compute_file_hash(self):
        """compute_file_hash returns SHA256 of file contents."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            f.flush()

            hash1 = compute_file_hash(Path(f.name))

            # Same content should give same hash
            self.assertEqual(len(hash1), 64)  # SHA256 hex length

            # Verify it's actually a hash of the content
            expected = hashlib.sha256(b"test content").hexdigest()
            self.assertEqual(hash1, expected)


class TestLoadCache(unittest.TestCase):
    """Tests for load_cache."""

    def test_load_cache_returns_none_if_missing(self):
        """load_cache returns None if file doesn't exist."""
        result = load_cache(Path("/nonexistent/families.json"))
        self.assertIsNone(result)


class TestSaveAndLoadCache(unittest.TestCase):
    """Tests for save_cache and load_cache together."""

    def test_save_and_load_cache(self):
        """save_cache and load_cache round-trip correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "families.json"

            families = [
                {"id": "@I001@", "subject": {"first_name": "John"}},
                {"id": "@I002@", "subject": {"first_name": "Jane"}}
            ]

            save_cache(cache_path, "abc123hash", families)

            loaded = load_cache(cache_path)

            self.assertEqual(loaded["gedcom_hash"], "abc123hash")
            self.assertEqual(len(loaded["families"]), 2)
            self.assertEqual(loaded["families"][0]["id"], "@I001@")


class TestIsCacheValid(unittest.TestCase):
    """Tests for is_cache_valid."""

    def test_is_cache_valid_true_when_hash_matches(self):
        """is_cache_valid returns True when GEDCOM hash matches."""
        cache = {"gedcom_hash": "abc123", "families": []}
        self.assertTrue(is_cache_valid(cache, "abc123"))

    def test_is_cache_valid_false_when_hash_differs(self):
        """is_cache_valid returns False when GEDCOM hash differs."""
        cache = {"gedcom_hash": "abc123", "families": []}
        self.assertFalse(is_cache_valid(cache, "different_hash"))

    def test_is_cache_valid_false_when_cache_none(self):
        """is_cache_valid returns False when cache is None."""
        self.assertFalse(is_cache_valid(None, "any_hash"))


if __name__ == "__main__":
    unittest.main()
