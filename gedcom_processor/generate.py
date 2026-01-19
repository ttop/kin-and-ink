#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ged4py>=0.5.0",
#     "pyyaml>=6.0",
# ]
# ///
"""Generate TRMNL family JSON from a GEDCOM file.

Usage:
    uv run generate.py family.ged
    uv run generate.py family.ged -o output/
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cache import compute_file_hash, load_cache, save_cache, is_cache_valid
from src.schema import family_to_current
from src.selector import select_family_id
from src.sources.gedcom_source import GedcomSource


def main():
    parser = argparse.ArgumentParser(
        description="Generate TRMNL family JSON from a GEDCOM file."
    )
    parser.add_argument(
        "gedcom_file",
        type=Path,
        help="Path to the GEDCOM file"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: same as GEDCOM file)"
    )

    args = parser.parse_args()

    gedcom_path = args.gedcom_file.resolve()
    if not gedcom_path.exists():
        print(f"Error: GEDCOM file not found: {gedcom_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir.resolve() if args.output_dir else gedcom_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    cache_path = output_dir / "families.json"
    output_path = output_dir / "current.json"

    # Check if we need to regenerate the cache
    current_hash = compute_file_hash(gedcom_path)
    cache = load_cache(cache_path)

    if not is_cache_valid(cache, current_hash):
        print(f"Parsing GEDCOM file: {gedcom_path}")
        source = GedcomSource(gedcom_path)

        eligible_ids = source.get_eligible_ids()
        if not eligible_ids:
            print("Error: No eligible families found in GEDCOM file", file=sys.stderr)
            print("(Eligible = has spouse + children + at least one parent)", file=sys.stderr)
            sys.exit(1)

        families = [source.get_family(pid) for pid in eligible_ids]
        save_cache(cache_path, current_hash, families)
        print(f"Cached {len(families)} eligible families")
    else:
        families = cache["families"]
        print(f"Using cached data ({len(families)} families)")

    # Read last family ID if exists
    last_id = None
    if output_path.exists():
        try:
            with open(output_path) as f:
                last_id = json.load(f).get("last_family_id")
        except (json.JSONDecodeError, KeyError):
            pass

    # Select and write
    family_ids = [f["id"] for f in families]
    selected_id = select_family_id(family_ids, last_id)
    selected_family = next(f for f in families if f["id"] == selected_id)
    current_data = family_to_current(selected_family)

    with open(output_path, 'w') as f:
        json.dump(current_data, f, indent=2)

    print(f"Generated: {output_path}")
    print(f"  Subject: {current_data['subject']['first_name']} {current_data['subject']['last_name']}")
    if current_data.get('spouse'):
        print(f"  Spouse:  {current_data['spouse']['first_name']} {current_data['spouse']['last_name']}")


if __name__ == "__main__":
    main()
