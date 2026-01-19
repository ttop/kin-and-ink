"""GEDCOM to TRMNL JSON processor with caching."""

import json
from pathlib import Path

from src.cache import compute_file_hash, load_cache, save_cache, is_cache_valid
from src.config import load_config
from src.schema import family_to_current
from src.selector import select_family_id
from src.sources.gedcom_source import GedcomSource


def run(config_path: Path, output_dir: Path) -> None:
    """Run the GEDCOM processor.

    On first run or when GEDCOM changes:
    - Parses GEDCOM and extracts all eligible families to families.json

    On every run:
    - Picks a random family (not same as last) and writes to current.json

    Args:
        config_path: Path to config.yml.
        output_dir: Directory to write families.json and current.json.
    """
    # Load config
    config = load_config(config_path)

    # Paths
    gedcom_path = config_path.parent / config["gedcom_file"]
    cache_path = output_dir / "families.json"
    output_path = output_dir / "current.json"

    # Check if we need to regenerate the cache
    current_hash = compute_file_hash(gedcom_path)
    cache = load_cache(cache_path)

    if not is_cache_valid(cache, current_hash):
        # Parse GEDCOM and extract all eligible families
        print(f"Parsing GEDCOM file: {gedcom_path}")
        source = GedcomSource(gedcom_path)

        eligible_ids = source.get_eligible_ids()
        if not eligible_ids:
            raise ValueError("No eligible families found in GEDCOM file")

        # Extract all families in TRMNL-ready format
        families = [source.get_family(pid) for pid in eligible_ids]

        # Save cache
        save_cache(cache_path, current_hash, families)
        print(f"Cached {len(families)} families to {cache_path}")
    else:
        families = cache["families"]
        print(f"Using cached data ({len(families)} families)")

    if not families:
        raise ValueError("No families available")

    # Read last family ID from current.json if it exists
    last_id = None
    if output_path.exists():
        try:
            with open(output_path) as f:
                existing = json.load(f)
                last_id = existing.get("last_family_id")
        except (json.JSONDecodeError, KeyError):
            pass

    # Select next family
    family_ids = [f["id"] for f in families]
    selected_id = select_family_id(family_ids, last_id)

    # Find the selected family and convert to current.json format
    selected_family = next(f for f in families if f["id"] == selected_id)
    current_data = family_to_current(selected_family)

    # Write output
    with open(output_path, 'w') as f:
        json.dump(current_data, f, indent=2)

    print(f"Selected family {selected_id} -> {output_path}")


def main() -> None:
    """Main entry point using default paths."""
    base_path = Path(__file__).parent.parent
    config_path = base_path / "config.yml"

    run(config_path, base_path)


if __name__ == "__main__":
    main()
