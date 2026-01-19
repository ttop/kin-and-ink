"""Tests for configuration loading."""

import unittest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.config import load_config


class TestLoadConfig(unittest.TestCase):
    """Tests for load_config function."""

    def test_load_config_reads_yaml(self):
        """load_config reads YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("gedcom_file: my_family.ged\nsource: gedcom\n")
            f.flush()

            config = load_config(Path(f.name))

            self.assertEqual(config["gedcom_file"], "my_family.ged")
            self.assertEqual(config["source"], "gedcom")

    def test_load_config_missing_file_raises(self):
        """load_config raises on missing file."""
        with self.assertRaises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yml"))


if __name__ == "__main__":
    unittest.main()
