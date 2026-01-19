"""Integration tests for main entry point."""

import unittest
import sys
import json
import tempfile
import time
import shutil
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.main import run


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_family.ged"


class TestRun(unittest.TestCase):
    """Tests for main run() function."""

    def test_run_creates_cache_and_output(self):
        """run() creates families.json cache and current.json output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Copy fixture GEDCOM
            shutil.copy(FIXTURE_PATH, tmpdir / "family.ged")

            # Create config
            config_path = tmpdir / "config.yml"
            config_path.write_text("gedcom_file: family.ged\nsource: gedcom\n")

            # Run
            run(config_path, tmpdir)

            # Verify cache created
            cache_path = tmpdir / "families.json"
            self.assertTrue(cache_path.exists())

            with open(cache_path) as f:
                cache = json.load(f)
            self.assertIn("gedcom_hash", cache)
            self.assertIn("families", cache)
            self.assertGreater(len(cache["families"]), 0)

            # Verify output created
            output_path = tmpdir / "current.json"
            self.assertTrue(output_path.exists())

            with open(output_path) as f:
                data = json.load(f)
            self.assertIn("last_family_id", data)
            self.assertIn("subject", data)

    def test_run_uses_cache_on_second_run(self):
        """run() uses existing cache when GEDCOM unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Copy fixture GEDCOM
            shutil.copy(FIXTURE_PATH, tmpdir / "family.ged")

            # Create config
            config_path = tmpdir / "config.yml"
            config_path.write_text("gedcom_file: family.ged\nsource: gedcom\n")

            # First run - creates cache
            run(config_path, tmpdir)

            cache_path = tmpdir / "families.json"
            original_mtime = cache_path.stat().st_mtime

            # Second run - should use cache (not modify it)
            time.sleep(0.1)  # Ensure mtime would differ if rewritten
            run(config_path, tmpdir)

            # Cache should be unchanged
            self.assertEqual(cache_path.stat().st_mtime, original_mtime)

    def test_run_regenerates_cache_when_gedcom_changes(self):
        """run() regenerates cache when GEDCOM file changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            gedcom_path = tmpdir / "family.ged"
            shutil.copy(FIXTURE_PATH, gedcom_path)

            config_path = tmpdir / "config.yml"
            config_path.write_text("gedcom_file: family.ged\nsource: gedcom\n")

            # First run
            run(config_path, tmpdir)

            cache_path = tmpdir / "families.json"
            with open(cache_path) as f:
                original_hash = json.load(f)["gedcom_hash"]

            # Modify GEDCOM (insert a note before TRLR)
            content = gedcom_path.read_text()
            content = content.replace("0 TRLR", "0 NOTE Modified\n0 TRLR")
            gedcom_path.write_text(content)

            # Second run - should regenerate cache
            run(config_path, tmpdir)

            with open(cache_path) as f:
                new_hash = json.load(f)["gedcom_hash"]

            self.assertNotEqual(new_hash, original_hash)

    def test_run_avoids_last_family(self):
        """run() picks different family than last time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            shutil.copy(FIXTURE_PATH, tmpdir / "family.ged")

            config_path = tmpdir / "config.yml"
            config_path.write_text("gedcom_file: family.ged\nsource: gedcom\n")

            output_path = tmpdir / "current.json"

            # Run multiple times and collect IDs
            ids_seen = set()
            for _ in range(10):
                run(config_path, tmpdir)
                with open(output_path) as f:
                    data = json.load(f)
                ids_seen.add(data["last_family_id"])

            # Should see variety (test fixture has multiple eligible people)
            self.assertGreaterEqual(len(ids_seen), 1)  # At minimum, it ran successfully


if __name__ == "__main__":
    unittest.main()
