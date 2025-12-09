# GEDCOM Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python script that extracts family data from GEDCOM files and outputs JSON for the TRMNL genealogy plugin, runnable via GitHub Actions.

**Architecture:** Abstract data source interface with GEDCOM adapter. On first run (or when GEDCOM changes), parses all eligible families into `families.json` cache. On subsequent runs, picks random family from cache (not same as last) and writes to `current.json`. GitHub Action commits both files to repo for Pages deployment.

**Tech Stack:** Python 3.12, ged4py library (GEDCOM 5.5.1 support), PyYAML, GitHub Actions

**Reference:** Design doc at `docs/plans/2025-12-09-gedcom-pipeline-design.md`

---

## Task 1: Project Scaffold

**Files:**
- Create: `gedcom_processor/requirements.txt`
- Create: `gedcom_processor/src/__init__.py`
- Create: `gedcom_processor/src/main.py`
- Create: `gedcom_processor/config.yml`

**Step 1: Create directory structure**

```bash
mkdir -p gedcom_processor/src/sources
mkdir -p gedcom_processor/tests
```

**Step 2: Create requirements.txt**

```
ged4py>=0.5.0
PyYAML>=6.0
```

**Step 3: Create empty __init__.py files**

Create empty files:
- `gedcom_processor/src/__init__.py`
- `gedcom_processor/src/sources/__init__.py`
- `gedcom_processor/tests/__init__.py`

**Step 4: Create minimal config.yml**

```yaml
# Path to your GEDCOM file
gedcom_file: family.ged

# Data source type (for future: "wikitree", etc.)
source: gedcom
```

**Step 5: Create minimal main.py**

```python
"""GEDCOM to TRMNL JSON processor."""


def main() -> None:
    print("GEDCOM processor starting...")


if __name__ == "__main__":
    main()
```

**Step 6: Verify structure**

```bash
ls -la gedcom_processor/
ls -la gedcom_processor/src/
python gedcom_processor/src/main.py
```

Expected: prints "GEDCOM processor starting..."

**Step 7: Commit**

```bash
git add gedcom_processor/
git commit -m "feat: add gedcom_processor project scaffold"
```

---

## Task 2: Data Source Interface

**Files:**
- Create: `gedcom_processor/src/sources/base.py`
- Create: `gedcom_processor/tests/test_sources_base.py`

**Step 1: Write test for abstract interface**

```python
# gedcom_processor/tests/test_sources_base.py
"""Tests for the FamilySource abstract base class."""

import pytest
from abc import ABC

from src.sources.base import FamilySource


def test_family_source_is_abstract():
    """FamilySource cannot be instantiated directly."""
    with pytest.raises(TypeError):
        FamilySource()


def test_family_source_requires_get_eligible_ids():
    """Subclasses must implement get_eligible_ids."""
    class IncompleteSource(FamilySource):
        def get_family(self, person_id: str) -> dict:
            return {}

    with pytest.raises(TypeError):
        IncompleteSource()


def test_family_source_requires_get_family():
    """Subclasses must implement get_family."""
    class IncompleteSource(FamilySource):
        def get_eligible_ids(self) -> list[str]:
            return []

    with pytest.raises(TypeError):
        IncompleteSource()


def test_complete_subclass_can_be_instantiated():
    """A complete subclass can be instantiated."""
    class CompleteSource(FamilySource):
        def get_eligible_ids(self) -> list[str]:
            return ["I001"]

        def get_family(self, person_id: str) -> dict:
            return {"subject": {"first_name": "Test"}}

    source = CompleteSource()
    assert source.get_eligible_ids() == ["I001"]
    assert source.get_family("I001") == {"subject": {"first_name": "Test"}}
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_sources_base.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.sources.base'"

**Step 3: Write the abstract base class**

```python
# gedcom_processor/src/sources/base.py
"""Abstract base class for family data sources."""

from abc import ABC, abstractmethod


class FamilySource(ABC):
    """Abstract interface for family data sources.

    Implementations provide access to genealogical data from various
    sources (GEDCOM files, WikiTree API, etc.).
    """

    @abstractmethod
    def get_eligible_ids(self) -> list[str]:
        """Return list of person IDs eligible for display.

        Eligibility criteria are source-specific but typically require
        the person to have: a spouse, at least one parent on either side,
        and at least one child.

        Returns:
            List of person ID strings.
        """
        pass

    @abstractmethod
    def get_family(self, person_id: str) -> dict:
        """Extract family data for a person.

        Args:
            person_id: The unique identifier for the person.

        Returns:
            Dictionary matching the TRMNL plugin schema:
            {
                "subject": {...},
                "spouse": {...},
                "subject_parents": {"father": {...}, "mother": {...}},
                "spouse_parents": {"father": {...}, "mother": {...}},
                "children": [{"first": {...}, "second": {...}}, ...]
            }
        """
        pass
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_sources_base.py -v
```

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/sources/base.py gedcom_processor/tests/test_sources_base.py
git commit -m "feat: add FamilySource abstract base class"
```

---

## Task 3: Output Schema

**Files:**
- Create: `gedcom_processor/src/schema.py`
- Create: `gedcom_processor/tests/test_schema.py`

**Step 1: Write tests for schema helpers**

```python
# gedcom_processor/tests/test_schema.py
"""Tests for output schema helpers."""

from src.schema import make_person, make_family_entry, family_to_current


def test_make_person_with_all_fields():
    """make_person creates dict with all fields."""
    person = make_person(
        first_name="John",
        last_name="Doe",
        birth="1850",
        death="1920"
    )
    assert person == {
        "first_name": "John",
        "last_name": "Doe",
        "birth": "1850",
        "death": "1920"
    }


def test_make_person_with_none_values():
    """make_person handles None values."""
    person = make_person(
        first_name="John",
        last_name="Doe",
        birth="1850",
        death=None
    )
    assert person == {
        "first_name": "John",
        "last_name": "Doe",
        "birth": "1850",
        "death": None
    }


def test_make_person_with_child_flag():
    """make_person can include child flag."""
    person = make_person(
        first_name="John",
        last_name="Doe",
        birth="1850",
        death="1920",
        child=True
    )
    assert person["child"] is True


def test_make_family_entry_structure():
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

    assert entry["id"] == "I001"
    assert entry["subject"] == subject
    assert entry["spouse"] == spouse
    assert "last_family_id" not in entry


def test_family_to_current_transforms_id():
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

    assert current["last_family_id"] == "I001"
    assert "id" not in current
    assert current["subject"] == {"first_name": "John"}
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_schema.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement schema helpers**

```python
# gedcom_processor/src/schema.py
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
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_schema.py -v
```

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/schema.py gedcom_processor/tests/test_schema.py
git commit -m "feat: add output schema helpers"
```

---

## Task 4: Selector Logic

**Files:**
- Create: `gedcom_processor/src/selector.py`
- Create: `gedcom_processor/tests/test_selector.py`

**Step 1: Write tests for selector**

```python
# gedcom_processor/tests/test_selector.py
"""Tests for the family selector."""

import pytest
from src.selector import select_family_id


def test_select_from_single_option():
    """With one option, always returns it."""
    result = select_family_id(["I001"], last_id=None)
    assert result == "I001"


def test_select_from_single_option_even_if_same_as_last():
    """With one option, returns it even if same as last."""
    result = select_family_id(["I001"], last_id="I001")
    assert result == "I001"


def test_select_avoids_last_id():
    """With multiple options, avoids the last selected ID."""
    eligible = ["I001", "I002"]

    # Run many times to verify it never picks I001 when that was last
    for _ in range(50):
        result = select_family_id(eligible, last_id="I001")
        assert result == "I002"


def test_select_with_no_last_id():
    """With no last ID, can pick any option."""
    eligible = ["I001", "I002", "I003"]
    results = set()

    # Run enough times to likely hit all options
    for _ in range(100):
        result = select_family_id(eligible, last_id=None)
        results.add(result)

    # Should have picked multiple different IDs
    assert len(results) > 1


def test_select_empty_list_raises():
    """Empty eligible list raises ValueError."""
    with pytest.raises(ValueError, match="No eligible"):
        select_family_id([], last_id=None)
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_selector.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement selector**

```python
# gedcom_processor/src/selector.py
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
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_selector.py -v
```

Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/selector.py gedcom_processor/tests/test_selector.py
git commit -m "feat: add family selector with last-ID avoidance"
```

---

## Task 5: Test GEDCOM File

**Files:**
- Create: `gedcom_processor/tests/fixtures/test_family.ged`

**Step 1: Create a minimal test GEDCOM file**

This file contains a small family tree for testing: a couple (John and Jane Doe) with parents on both sides and two children.

```
0 HEAD
1 SOUR Test
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I001@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 1850
1 DEAT
2 DATE 1920
1 FAMS @F001@
1 FAMC @F003@
0 @I002@ INDI
1 NAME Jane /Smith/
1 SEX F
1 BIRT
2 DATE 1855
1 DEAT
2 DATE 1925
1 FAMS @F001@
1 FAMC @F004@
0 @I003@ INDI
1 NAME William /Doe/
1 SEX M
1 BIRT
2 DATE 1820
1 DEAT
2 DATE 1890
1 FAMS @F003@
0 @I004@ INDI
1 NAME Mary /Johnson/
1 SEX F
1 BIRT
2 DATE 1825
1 DEAT
2 DATE 1895
1 FAMS @F003@
0 @I005@ INDI
1 NAME Robert /Smith/
1 SEX M
1 BIRT
2 DATE 1822
1 DEAT
2 DATE 1888
1 FAMS @F004@
0 @I006@ INDI
1 NAME Elizabeth /Brown/
1 SEX F
1 BIRT
2 DATE 1828
1 DEAT
2 DATE 1900
1 FAMS @F004@
0 @I007@ INDI
1 NAME James /Doe/
1 SEX M
1 BIRT
2 DATE 1875
1 DEAT
2 DATE 1950
1 FAMC @F001@
1 FAMS @F002@
0 @I008@ INDI
1 NAME Sarah /Doe/
1 SEX F
1 BIRT
2 DATE 1878
1 DEAT
2 DATE 1960
1 FAMC @F001@
0 @I009@ INDI
1 NAME Alice /Williams/
1 SEX F
1 BIRT
2 DATE 1880
1 DEAT
2 DATE 1955
1 FAMS @F002@
0 @F001@ FAM
1 HUSB @I001@
1 WIFE @I002@
1 CHIL @I007@
1 CHIL @I008@
0 @F002@ FAM
1 HUSB @I007@
1 WIFE @I009@
0 @F003@ FAM
1 HUSB @I003@
1 WIFE @I004@
1 CHIL @I001@
0 @F004@ FAM
1 HUSB @I005@
1 WIFE @I006@
1 CHIL @I002@
0 TRLR
```

**Step 2: Create fixtures directory and save file**

```bash
mkdir -p gedcom_processor/tests/fixtures
```

Then write the GEDCOM content above to `gedcom_processor/tests/fixtures/test_family.ged`.

**Step 3: Commit**

```bash
git add gedcom_processor/tests/fixtures/test_family.ged
git commit -m "test: add test GEDCOM fixture file"
```

---

## Task 6: GEDCOM Source - Basic Parsing (using ged4py)

**Files:**
- Create: `gedcom_processor/src/sources/gedcom_source.py`
- Create: `gedcom_processor/tests/test_gedcom_source.py`

**Step 1: Install dependencies for testing**

```bash
cd gedcom_processor && pip install -r requirements.txt pytest
```

**Step 2: Write test for GEDCOM loading**

```python
# gedcom_processor/tests/test_gedcom_source.py
"""Tests for the GEDCOM data source."""

import pytest
from pathlib import Path

from src.sources.gedcom_source import GedcomSource
from src.sources.base import FamilySource


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_family.ged"


def test_gedcom_source_implements_interface():
    """GedcomSource implements FamilySource interface."""
    source = GedcomSource(FIXTURE_PATH)
    assert isinstance(source, FamilySource)


def test_gedcom_source_loads_file():
    """GedcomSource can load a GEDCOM file."""
    source = GedcomSource(FIXTURE_PATH)
    # Should not raise
    assert source is not None
```

**Step 3: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 4: Implement minimal GedcomSource using ged4py**

```python
# gedcom_processor/src/sources/gedcom_source.py
"""GEDCOM file data source using ged4py library."""

from pathlib import Path
from ged4py import GedcomReader

from .base import FamilySource


class GedcomSource(FamilySource):
    """Data source that reads from GEDCOM files.

    Uses ged4py library which supports GEDCOM 5.5.1 format.
    GEDCOM 5.5 files are also supported as 5.5.1 is backward compatible.
    """

    def __init__(self, file_path: Path):
        """Initialize with path to GEDCOM file.

        Args:
            file_path: Path to the .ged file.
        """
        self._file_path = file_path
        with GedcomReader(file_path) as reader:
            # Build lookup dictionaries
            self._individuals = {}
            self._families = {}

            for record in reader.records0("INDI"):
                self._individuals[record.xref_id] = record

            for record in reader.records0("FAM"):
                self._families[record.xref_id] = record

    def get_eligible_ids(self) -> list[str]:
        """Return list of eligible person IDs."""
        # Placeholder - will implement eligibility filtering
        return []

    def get_family(self, person_id: str) -> dict:
        """Extract family data for a person."""
        # Placeholder - will implement extraction
        return {}
```

**Step 5: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py -v
```

Expected: Both tests PASS

**Step 6: Commit**

```bash
git add gedcom_processor/src/sources/gedcom_source.py gedcom_processor/tests/test_gedcom_source.py
git commit -m "feat: add GedcomSource with ged4py file parsing"
```

---

## Task 7: GEDCOM Source - Get Eligible IDs

**Files:**
- Modify: `gedcom_processor/src/sources/gedcom_source.py`
- Modify: `gedcom_processor/tests/test_gedcom_source.py`

**Step 1: Add tests for get_eligible_ids**

Add to `test_gedcom_source.py`:

```python
def test_get_eligible_ids_returns_eligible_people():
    """get_eligible_ids returns people meeting criteria."""
    source = GedcomSource(FIXTURE_PATH)
    eligible = source.get_eligible_ids()

    # I001 (John Doe) should be eligible: has spouse, parents, children
    assert "@I001@" in eligible


def test_get_eligible_ids_excludes_ineligible():
    """get_eligible_ids excludes people missing requirements."""
    source = GedcomSource(FIXTURE_PATH)
    eligible = source.get_eligible_ids()

    # I008 (Sarah Doe) has no spouse, should not be eligible
    assert "@I008@" not in eligible
```

**Step 2: Run tests to verify new tests fail**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py::test_get_eligible_ids_returns_eligible_people -v
```

Expected: FAIL (returns empty list)

**Step 3: Implement eligibility checking with ged4py**

Update `gedcom_source.py`:

```python
# gedcom_processor/src/sources/gedcom_source.py
"""GEDCOM file data source using ged4py library."""

from pathlib import Path
from ged4py import GedcomReader
from ged4py.model import Individual, Family

from .base import FamilySource


class GedcomSource(FamilySource):
    """Data source that reads from GEDCOM files.

    Uses ged4py library which supports GEDCOM 5.5.1 format.
    GEDCOM 5.5 files are also supported as 5.5.1 is backward compatible.
    """

    def __init__(self, file_path: Path):
        """Initialize with path to GEDCOM file.

        Args:
            file_path: Path to the .ged file.
        """
        self._file_path = file_path
        self._individuals: dict[str, Individual] = {}
        self._families: dict[str, Family] = {}

        with GedcomReader(file_path) as reader:
            for record in reader.records0("INDI"):
                self._individuals[record.xref_id] = record

            for record in reader.records0("FAM"):
                self._families[record.xref_id] = record

    def get_eligible_ids(self) -> list[str]:
        """Return list of eligible person IDs.

        Eligibility requires:
        - Has a spouse
        - Has at least one parent (on subject or spouse side)
        - Has at least one child
        """
        eligible = []

        for person_id, person in self._individuals.items():
            if self._is_eligible(person):
                eligible.append(person_id)

        return eligible

    def _is_eligible(self, person: Individual) -> bool:
        """Check if a person meets eligibility criteria."""
        # Must have a spouse (be in a family as spouse)
        spouse_families = self._get_families_as_spouse(person)
        if not spouse_families:
            return False

        # Check first spouse family for children
        family = spouse_families[0]
        children = self._get_children_of_family(family)
        if not children:
            return False

        # Must have at least one parent (on either side)
        person_parents = self._get_parents(person)
        spouse = self._get_spouse(person, family)
        spouse_parents = self._get_parents(spouse) if spouse else (None, None)

        has_any_parent = (
            person_parents[0] is not None or
            person_parents[1] is not None or
            spouse_parents[0] is not None or
            spouse_parents[1] is not None
        )

        return has_any_parent

    def _get_families_as_spouse(self, person: Individual) -> list[Family]:
        """Get families where this person is a spouse."""
        families = []
        # ged4py: person.sub_tag("FAMS") returns family references where person is spouse
        for fams in person.sub_tags("FAMS"):
            fam_ref = fams.value
            if fam_ref and fam_ref in self._families:
                families.append(self._families[fam_ref])
        return families

    def _get_children_of_family(self, family: Family) -> list[Individual]:
        """Get children of a family."""
        children = []
        for chil in family.sub_tags("CHIL"):
            child_ref = chil.value
            if child_ref and child_ref in self._individuals:
                children.append(self._individuals[child_ref])
        return children

    def _get_spouse(self, person: Individual, family: Family) -> Individual | None:
        """Get the spouse of a person in a family."""
        husb = family.sub_tag("HUSB")
        wife = family.sub_tag("WIFE")

        husb_id = husb.value if husb else None
        wife_id = wife.value if wife else None

        person_id = person.xref_id

        if person_id == husb_id and wife_id:
            return self._individuals.get(wife_id)
        elif person_id == wife_id and husb_id:
            return self._individuals.get(husb_id)

        return None

    def _get_parents(self, person: Individual | None) -> tuple[Individual | None, Individual | None]:
        """Get (father, mother) for a person."""
        if person is None:
            return (None, None)

        # ged4py: person.sub_tag("FAMC") returns family reference where person is child
        famc = person.sub_tag("FAMC")
        if not famc or not famc.value:
            return (None, None)

        family = self._families.get(famc.value)
        if not family:
            return (None, None)

        husb = family.sub_tag("HUSB")
        wife = family.sub_tag("WIFE")

        father_id = husb.value if husb else None
        mother_id = wife.value if wife else None

        father = self._individuals.get(father_id) if father_id else None
        mother = self._individuals.get(mother_id) if mother_id else None

        return (father, mother)

    def get_family(self, person_id: str) -> dict:
        """Extract family data for a person."""
        # Placeholder - will implement in next task
        return {}
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py -v
```

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/sources/gedcom_source.py gedcom_processor/tests/test_gedcom_source.py
git commit -m "feat: implement eligibility checking for GEDCOM source"
```

---

## Task 8: GEDCOM Source - Get Family Data

**Files:**
- Modify: `gedcom_processor/src/sources/gedcom_source.py`
- Modify: `gedcom_processor/tests/test_gedcom_source.py`

**Step 1: Add tests for get_family**

Add to `test_gedcom_source.py`:

```python
def test_get_family_returns_subject():
    """get_family includes subject data."""
    source = GedcomSource(FIXTURE_PATH)
    family = source.get_family("@I001@")

    assert family["subject"]["first_name"] == "John"
    assert family["subject"]["last_name"] == "Doe"
    assert family["subject"]["birth"] == "1850"
    assert family["subject"]["death"] == "1920"


def test_get_family_returns_spouse():
    """get_family includes spouse data."""
    source = GedcomSource(FIXTURE_PATH)
    family = source.get_family("@I001@")

    assert family["spouse"]["first_name"] == "Jane"
    assert family["spouse"]["last_name"] == "Smith"


def test_get_family_returns_subject_parents():
    """get_family includes subject's parents."""
    source = GedcomSource(FIXTURE_PATH)
    family = source.get_family("@I001@")

    assert family["subject_parents"]["father"]["first_name"] == "William"
    assert family["subject_parents"]["mother"]["first_name"] == "Mary"


def test_get_family_returns_spouse_parents():
    """get_family includes spouse's parents."""
    source = GedcomSource(FIXTURE_PATH)
    family = source.get_family("@I001@")

    assert family["spouse_parents"]["father"]["first_name"] == "Robert"
    assert family["spouse_parents"]["mother"]["first_name"] == "Elizabeth"


def test_get_family_returns_children():
    """get_family includes children with child flag."""
    source = GedcomSource(FIXTURE_PATH)
    family = source.get_family("@I001@")

    children = family["children"]
    assert len(children) == 2

    # Find James (who has a spouse)
    james_entry = next((c for c in children if c["first"]["first_name"] == "James"), None)
    assert james_entry is not None
    assert james_entry["first"]["child"] is True
    assert james_entry["second"]["first_name"] == "Alice"
```

**Step 2: Run tests to verify new tests fail**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py::test_get_family_returns_subject -v
```

Expected: FAIL (returns empty dict)

**Step 3: Implement get_family with ged4py**

Add to `gedcom_source.py` (import schema helpers at top, then add methods):

Add import at top:
```python
from src.schema import make_person, make_family_entry
```

Add these methods to the class:

```python
    def get_family(self, person_id: str) -> dict:
        """Extract family data for a person in TRMNL-ready format."""
        person = self._individuals.get(person_id)
        if person is None:
            raise ValueError(f"Person {person_id} not found")

        # Get spouse and family
        spouse_families = self._get_families_as_spouse(person)
        family = spouse_families[0] if spouse_families else None
        spouse = self._get_spouse(person, family) if family else None

        # Get parents
        subject_father, subject_mother = self._get_parents(person)
        spouse_father, spouse_mother = self._get_parents(spouse)

        # Get children with their spouses
        children_data = []
        if family:
            children = self._get_children_of_family(family)
            for child in children:
                child_entry = self._make_child_entry(child)
                children_data.append(child_entry)

        return make_family_entry(
            family_id=person_id,
            subject=self._person_to_dict(person),
            spouse=self._person_to_dict(spouse) if spouse else None,
            subject_parents={
                "father": self._person_to_dict(subject_father),
                "mother": self._person_to_dict(subject_mother)
            },
            spouse_parents={
                "father": self._person_to_dict(spouse_father),
                "mother": self._person_to_dict(spouse_mother)
            },
            children=children_data
        )

    def _person_to_dict(self, person: Individual | None) -> dict | None:
        """Convert a ged4py Individual to a person dict."""
        if person is None:
            return None

        # ged4py name handling
        name_rec = person.sub_tag("NAME")
        if name_rec:
            # NAME value is like "John /Doe/"
            name_val = name_rec.value or ""
            # Extract parts - surname is between slashes
            if "/" in name_val:
                parts = name_val.split("/")
                first_name = parts[0].strip()
                last_name = parts[1].strip() if len(parts) > 1 else ""
            else:
                first_name = name_val.strip()
                last_name = ""
        else:
            first_name = ""
            last_name = ""

        # Get birth year
        birth = None
        birt = person.sub_tag("BIRT")
        if birt:
            date_rec = birt.sub_tag("DATE")
            if date_rec and date_rec.value:
                birth = self._extract_year(date_rec.value)

        # Get death year
        death = None
        deat = person.sub_tag("DEAT")
        if deat:
            date_rec = deat.sub_tag("DATE")
            if date_rec and date_rec.value:
                death = self._extract_year(date_rec.value)

        return make_person(
            first_name=first_name,
            last_name=last_name,
            birth=birth,
            death=death
        )

    def _extract_year(self, date_str: str) -> str | None:
        """Extract year from a GEDCOM date string."""
        # Simple extraction - just get the 4-digit year
        import re
        match = re.search(r'\b(\d{4})\b', date_str)
        return match.group(1) if match else None

    def _make_child_entry(self, child: Individual) -> dict:
        """Create a child entry with optional spouse."""
        child_dict = self._person_to_dict(child)
        child_dict["child"] = True

        # Check if child has a spouse
        child_families = self._get_families_as_spouse(child)
        if child_families:
            child_spouse = self._get_spouse(child, child_families[0])
            if child_spouse:
                return {
                    "first": child_dict,
                    "second": self._person_to_dict(child_spouse)
                }

        return {"first": child_dict}
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py -v
```

Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/sources/gedcom_source.py gedcom_processor/tests/test_gedcom_source.py
git commit -m "feat: implement get_family for GEDCOM source"
```

---

## Task 9: Config Loading

**Files:**
- Create: `gedcom_processor/src/config.py`
- Create: `gedcom_processor/tests/test_config.py`

**Step 1: Write tests for config loading**

```python
# gedcom_processor/tests/test_config.py
"""Tests for configuration loading."""

import pytest
from pathlib import Path
import tempfile

from src.config import load_config


def test_load_config_reads_yaml():
    """load_config reads YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("gedcom_file: my_family.ged\nsource: gedcom\n")
        f.flush()

        config = load_config(Path(f.name))

        assert config["gedcom_file"] == "my_family.ged"
        assert config["source"] == "gedcom"


def test_load_config_missing_file_raises():
    """load_config raises on missing file."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/config.yml"))
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement config loading**

```python
# gedcom_processor/src/config.py
"""Configuration loading."""

from pathlib import Path
import yaml


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yml file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_config.py -v
```

Expected: Both tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/config.py gedcom_processor/tests/test_config.py
git commit -m "feat: add config loading"
```

---

## Task 10: Cache Layer (families.json)

**Files:**
- Create: `gedcom_processor/src/cache.py`
- Create: `gedcom_processor/tests/test_cache.py`

**Step 1: Write tests for cache operations**

```python
# gedcom_processor/tests/test_cache.py
"""Tests for the families.json cache layer."""

import json
import hashlib
import tempfile
from pathlib import Path

from src.cache import compute_file_hash, load_cache, save_cache, is_cache_valid


def test_compute_file_hash():
    """compute_file_hash returns SHA256 of file contents."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        f.flush()

        hash1 = compute_file_hash(Path(f.name))

        # Same content should give same hash
        assert len(hash1) == 64  # SHA256 hex length

        # Verify it's actually a hash of the content
        expected = hashlib.sha256(b"test content").hexdigest()
        assert hash1 == expected


def test_load_cache_returns_none_if_missing():
    """load_cache returns None if file doesn't exist."""
    result = load_cache(Path("/nonexistent/families.json"))
    assert result is None


def test_save_and_load_cache():
    """save_cache and load_cache round-trip correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "families.json"

        families = [
            {"id": "@I001@", "subject": {"first_name": "John"}},
            {"id": "@I002@", "subject": {"first_name": "Jane"}}
        ]

        save_cache(cache_path, "abc123hash", families)

        loaded = load_cache(cache_path)

        assert loaded["gedcom_hash"] == "abc123hash"
        assert len(loaded["families"]) == 2
        assert loaded["families"][0]["id"] == "@I001@"


def test_is_cache_valid_true_when_hash_matches():
    """is_cache_valid returns True when GEDCOM hash matches."""
    cache = {"gedcom_hash": "abc123", "families": []}
    assert is_cache_valid(cache, "abc123") is True


def test_is_cache_valid_false_when_hash_differs():
    """is_cache_valid returns False when GEDCOM hash differs."""
    cache = {"gedcom_hash": "abc123", "families": []}
    assert is_cache_valid(cache, "different_hash") is False


def test_is_cache_valid_false_when_cache_none():
    """is_cache_valid returns False when cache is None."""
    assert is_cache_valid(None, "any_hash") is False
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_cache.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement cache module**

```python
# gedcom_processor/src/cache.py
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
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_cache.py -v
```

Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add gedcom_processor/src/cache.py gedcom_processor/tests/test_cache.py
git commit -m "feat: add cache layer for pre-extracted families"
```

---

## Task 11: Main Entry Point (with caching)

**Files:**
- Modify: `gedcom_processor/src/main.py`
- Create: `gedcom_processor/tests/test_main.py`

**Step 1: Write integration tests**

```python
# gedcom_processor/tests/test_main.py
"""Integration tests for main entry point."""

import json
import tempfile
from pathlib import Path
import shutil

from src.main import run


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_family.ged"


def test_run_creates_cache_and_output():
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
        assert cache_path.exists()

        with open(cache_path) as f:
            cache = json.load(f)
        assert "gedcom_hash" in cache
        assert "families" in cache
        assert len(cache["families"]) > 0

        # Verify output created
        output_path = tmpdir / "current.json"
        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)
        assert "last_family_id" in data
        assert "subject" in data


def test_run_uses_cache_on_second_run():
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
        with open(cache_path) as f:
            original_cache = json.load(f)
        original_mtime = cache_path.stat().st_mtime

        # Second run - should use cache (not modify it)
        import time
        time.sleep(0.1)  # Ensure mtime would differ if rewritten
        run(config_path, tmpdir)

        # Cache should be unchanged
        assert cache_path.stat().st_mtime == original_mtime


def test_run_regenerates_cache_when_gedcom_changes():
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

        # Modify GEDCOM (append a comment)
        with open(gedcom_path, 'a') as f:
            f.write("\n0 NOTE Modified\n")

        # Second run - should regenerate cache
        run(config_path, tmpdir)

        with open(cache_path) as f:
            new_hash = json.load(f)["gedcom_hash"]

        assert new_hash != original_hash


def test_run_avoids_last_family():
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
        assert len(ids_seen) >= 1  # At minimum, it ran successfully
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_main.py -v
```

Expected: FAIL (run function doesn't exist or doesn't work)

**Step 3: Implement main.py with caching**

```python
# gedcom_processor/src/main.py
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
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_main.py -v
```

Expected: All 4 tests PASS

**Step 5: Run all tests**

```bash
cd gedcom_processor && python -m pytest -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add gedcom_processor/src/main.py gedcom_processor/tests/test_main.py
git commit -m "feat: implement main entry point with cache layer"
```

---

## Task 12: GitHub Action Workflow

**Files:**
- Create: `gedcom_processor/.github/workflows/rotate.yml`

**Step 1: Create workflow directory**

```bash
mkdir -p gedcom_processor/.github/workflows
```

**Step 2: Create workflow file**

```yaml
# gedcom_processor/.github/workflows/rotate.yml
name: Rotate Family

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6am UTC
  workflow_dispatch:      # Manual trigger

jobs:
  rotate:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate family JSON
        run: python src/main.py

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add current.json families.json
          git diff --quiet --cached || git commit -m "Rotate family display"
          git push
```

**Step 3: Commit**

```bash
git add gedcom_processor/.github/workflows/rotate.yml
git commit -m "feat: add GitHub Action workflow for family rotation"
```

---

## Task 13: README Documentation

**Files:**
- Create: `gedcom_processor/README.md`

**Step 1: Write README**

```markdown
# GEDCOM Family Rotator for TRMNL

Automatically rotates through your family tree on a TRMNL e-ink display.

## Quick Start

1. **Fork this repository** to your GitHub account

2. **Add your GEDCOM file**
   - Export from your genealogy software (Ancestry, FamilySearch, Gramps, etc.)
   - Upload to the repository root via GitHub's web interface
   - Name it `family.ged` (or update `config.yml`)

3. **Update config.yml** (if needed)
   ```yaml
   gedcom_file: family.ged
   source: gedcom
   ```

4. **Enable GitHub Pages**
   - Go to Settings → Pages
   - Set source to "Deploy from a branch"
   - Select `main` branch and `/ (root)` folder
   - Save

5. **Run the workflow**
   - Go to Actions → "Rotate Family"
   - Click "Run workflow"

6. **Configure TRMNL plugin**
   - Copy your GitHub Pages URL: `https://yourusername.github.io/repo-name/current.json`
   - Paste into your TRMNL genealogy plugin settings

The workflow runs daily at 6am UTC by default. Edit `.github/workflows/rotate.yml` to change the schedule.

## ⚠️ Privacy Warning

**Your GEDCOM file will be publicly visible** if your repository is public (required for free GitHub Pages).

Before uploading:
- **Remove living people** from your GEDCOM export
- Most genealogy software has an option to exclude living individuals
- Review the file for sensitive information (addresses, SSNs, etc.)

If privacy is critical, GitHub Pro ($4/mo) allows GitHub Pages on private repositories.

## Eligibility Criteria

Not everyone in your GEDCOM will be displayed. A person must have:
- A spouse
- At least one parent (on either side)
- At least one child

This ensures the display has content in all sections.

## How It Works

1. GitHub Action runs on schedule (or manual trigger)
2. On first run: parses GEDCOM, extracts all eligible families to `families.json` cache
3. On subsequent runs: uses cached data (skips parsing if GEDCOM unchanged)
4. Picks one family randomly (avoids repeating the previous one)
5. Writes selected family to `current.json`
6. Commits and pushes
7. GitHub Pages serves the updated file
8. TRMNL polls the URL and displays your family

## GEDCOM Compatibility

This tool uses the [ged4py](https://ged4py.readthedocs.io/) library which supports:

- **GEDCOM 5.5.1** (fully supported)
- **GEDCOM 5.5** (backward compatible, works fine)
- **GEDCOM 7.0** (not supported)

Most genealogy software (Ancestry, FamilySearch, Gramps, RootsMagic, etc.) exports GEDCOM 5.5.1 by default, so this should work with your files. If your software exports GEDCOM 7.0, you may need to export in 5.5.1 compatibility mode.

## Local Development

```bash
pip install -r requirements.txt
python src/main.py
```

## License

MIT
```

**Step 2: Commit**

```bash
git add gedcom_processor/README.md
git commit -m "docs: add README with setup instructions"
```

---

## Task 14: Final Integration Test

**Files:** None (testing only)

**Step 1: Run full test suite**

```bash
cd gedcom_processor && python -m pytest -v --tb=short
```

Expected: All tests pass

**Step 2: Test manual execution**

```bash
cd gedcom_processor
cp tests/fixtures/test_family.ged family.ged
python src/main.py
cat current.json
```

Expected: `current.json` contains valid family data

**Step 3: Clean up test file**

```bash
rm gedcom_processor/family.ged gedcom_processor/current.json
```

**Step 4: Final commit**

```bash
git add -A
git status
# If any uncommitted changes:
git commit -m "chore: final cleanup"
```

---

## Summary

After completing all 14 tasks, you will have:

- `gedcom_processor/` directory with:
  - Abstract `FamilySource` interface (extensible for WikiTree later)
  - `GedcomSource` implementation using ged4py (GEDCOM 5.5.1 support)
  - Eligibility filtering (spouse + parent + child)
  - Cache layer (`families.json`) - parse once, rotate many times
  - Random selection with last-ID avoidance
  - Output matching TRMNL plugin JSON schema
  - GitHub Action for daily rotation
  - README with setup instructions, privacy warnings, and GEDCOM compatibility notes

- Full test coverage for all components
- Ready to use as a template repository
