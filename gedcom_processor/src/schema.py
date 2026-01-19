"""Output schema helpers for TRMNL plugin JSON format."""

from typing import Optional


def make_person(
    first_name: str,
    last_name: str,
    birth: Optional[str],
    death: Optional[str],
    child: Optional[bool] = None
) -> dict:
    """Create a person dictionary for the output schema.

    Args:
        first_name: Person's first name(s).
        last_name: Person's surname.
        birth: Birth year/date as string, or None.
        death: Death year/date as string, or None.
        child: If True, marks this person as a child of the subject/spouse.

    Returns:
        Dictionary with person data.
    """
    person = {
        "first_name": first_name,
        "last_name": last_name,
        "birth": birth,
        "death": death
    }
    if child is not None:
        person["child"] = child
    return person


def make_family_entry(
    family_id: str,
    subject: dict,
    spouse: Optional[dict],
    subject_parents: dict,
    spouse_parents: dict,
    children: list[dict]
) -> dict:
    """Create a family entry for the families.json cache.

    The entry is stored in TRMNL-ready format with an 'id' field.
    When selected for display, the 'id' becomes 'last_family_id'.

    Args:
        family_id: Unique ID for this family (used for rotation tracking).
        subject: The main person dictionary.
        spouse: The spouse dictionary, or None.
        subject_parents: Dict with "father" and "mother" keys.
        spouse_parents: Dict with "father" and "mother" keys.
        children: List of child entries (each with "first" and optional "second").

    Returns:
        Family entry dictionary for caching.
    """
    return {
        "id": family_id,
        "subject": subject,
        "spouse": spouse,
        "subject_parents": subject_parents,
        "spouse_parents": spouse_parents,
        "children": children
    }


def family_to_current(family: dict) -> dict:
    """Convert a cached family entry to current.json format.

    Removes 'id' and adds 'last_family_id' with the same value.

    Args:
        family: Family entry from families.json cache.

    Returns:
        Dictionary ready for current.json output.
    """
    result = {k: v for k, v in family.items() if k != "id"}
    result["last_family_id"] = family["id"]
    return result
