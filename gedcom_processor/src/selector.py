"""Family selection logic."""

import random
from typing import Optional


def select_family_id(eligible_ids: list[str], last_id: Optional[str]) -> str:
    """Select a random family ID, avoiding the last one if possible.

    Args:
        eligible_ids: List of eligible person IDs to choose from.
        last_id: The ID selected last time, or None if first run.

    Returns:
        Selected person ID.

    Raises:
        ValueError: If eligible_ids is empty.
    """
    if not eligible_ids:
        raise ValueError("No eligible families to select from")

    if len(eligible_ids) == 1:
        return eligible_ids[0]

    # Filter out last_id if present
    candidates = [id for id in eligible_ids if id != last_id]

    # If somehow all were filtered (shouldn't happen with len > 1), use all
    if not candidates:
        candidates = eligible_ids

    return random.choice(candidates)
