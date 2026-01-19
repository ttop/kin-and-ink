"""Cache layer for pre-extracted family data."""

import hashlib
import json
from pathlib import Path
from typing import Optional


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file's contents.

    Args:
        file_path: Path to file to hash.

    Returns:
        Hex string of SHA256 hash.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_cache(cache_path: Path) -> Optional[dict]:
    """Load the families cache if it exists.

    Args:
        cache_path: Path to families.json.

    Returns:
        Cache dict with 'gedcom_hash' and 'families' keys, or None.
    """
    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return None


def save_cache(cache_path: Path, gedcom_hash: str, families: list[dict]) -> None:
    """Save extracted families to cache.

    Args:
        cache_path: Path to write families.json.
        gedcom_hash: SHA256 hash of source GEDCOM file.
        families: List of family dicts in TRMNL-ready format.
    """
    cache = {
        "gedcom_hash": gedcom_hash,
        "families": families
    }
    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)


def is_cache_valid(cache: Optional[dict], current_hash: str) -> bool:
    """Check if cache is valid for the current GEDCOM file.

    Args:
        cache: Loaded cache dict, or None.
        current_hash: Hash of current GEDCOM file.

    Returns:
        True if cache exists and hash matches.
    """
    if cache is None:
        return False
    return cache.get("gedcom_hash") == current_hash
