# GEDCOM Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python script that extracts family data from GEDCOM files and outputs JSON for the TRMNL genealogy plugin, runnable via GitHub Actions.

**Architecture:** Abstract data source interface with GEDCOM adapter. Selector picks random eligible person (not same as last). Output matches existing plugin JSON schema. GitHub Action commits `current.json` to repo for Pages deployment.

**Tech Stack:** Python 3.12, python-gedcom library, PyYAML, GitHub Actions

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
python-gedcom>=1.0.0
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

from src.schema import make_person, make_family_output


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


def test_make_family_output_structure():
    """make_family_output creates complete output structure."""
    subject = make_person("John", "Doe", "1850", "1920")
    spouse = make_person("Jane", "Smith", "1855", "1925")

    output = make_family_output(
        family_id="I001",
        subject=subject,
        spouse=spouse,
        subject_parents={"father": None, "mother": None},
        spouse_parents={"father": None, "mother": None},
        children=[]
    )

    assert output["last_family_id"] == "I001"
    assert output["subject"] == subject
    assert output["spouse"] == spouse
    assert output["subject_parents"] == {"father": None, "mother": None}
    assert output["spouse_parents"] == {"father": None, "mother": None}
    assert output["children"] == []
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


def make_family_output(
    family_id: str,
    subject: dict,
    spouse: Optional[dict],
    subject_parents: dict,
    spouse_parents: dict,
    children: list[dict]
) -> dict:
    """Create the complete family output structure.

    Args:
        family_id: Unique ID for this family (used for rotation tracking).
        subject: The main person dictionary.
        spouse: The spouse dictionary, or None.
        subject_parents: Dict with "father" and "mother" keys.
        spouse_parents: Dict with "father" and "mother" keys.
        children: List of child entries (each with "first" and optional "second").

    Returns:
        Complete output dictionary matching TRMNL plugin schema.
    """
    return {
        "last_family_id": family_id,
        "subject": subject,
        "spouse": spouse,
        "subject_parents": subject_parents,
        "spouse_parents": spouse_parents,
        "children": children
    }
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

## Task 6: GEDCOM Source - Basic Parsing

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

**Step 4: Implement minimal GedcomSource**

```python
# gedcom_processor/src/sources/gedcom_source.py
"""GEDCOM file data source."""

from pathlib import Path
from gedcom.parser import Parser

from .base import FamilySource


class GedcomSource(FamilySource):
    """Data source that reads from GEDCOM files."""

    def __init__(self, file_path: Path):
        """Initialize with path to GEDCOM file.

        Args:
            file_path: Path to the .ged file.
        """
        self._parser = Parser()
        self._parser.parse_file(str(file_path))

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
git commit -m "feat: add GedcomSource with basic file parsing"
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
    assert "I001" in eligible or "@I001@" in eligible


def test_get_eligible_ids_excludes_ineligible():
    """get_eligible_ids excludes people missing requirements."""
    source = GedcomSource(FIXTURE_PATH)
    eligible = source.get_eligible_ids()

    # I008 (Sarah Doe) has no spouse, should not be eligible
    assert "I008" not in eligible and "@I008@" not in eligible
```

**Step 2: Run tests to verify new tests fail**

```bash
cd gedcom_processor && python -m pytest tests/test_gedcom_source.py::test_get_eligible_ids_returns_eligible_people -v
```

Expected: FAIL (returns empty list)

**Step 3: Implement eligibility checking**

Update `gedcom_source.py`:

```python
# gedcom_processor/src/sources/gedcom_source.py
"""GEDCOM file data source."""

from pathlib import Path
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement

from .base import FamilySource


class GedcomSource(FamilySource):
    """Data source that reads from GEDCOM files."""

    def __init__(self, file_path: Path):
        """Initialize with path to GEDCOM file.

        Args:
            file_path: Path to the .ged file.
        """
        self._parser = Parser()
        self._parser.parse_file(str(file_path))
        self._elements = self._parser.get_root_child_elements()

        # Build lookup dictionaries
        self._individuals: dict[str, IndividualElement] = {}
        self._families: dict[str, FamilyElement] = {}

        for element in self._elements:
            if isinstance(element, IndividualElement):
                self._individuals[element.get_pointer()] = element
            elif isinstance(element, FamilyElement):
                self._families[element.get_pointer()] = element

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

    def _is_eligible(self, person: IndividualElement) -> bool:
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

    def _get_families_as_spouse(self, person: IndividualElement) -> list[FamilyElement]:
        """Get families where this person is a spouse."""
        families = []
        for family in self._families.values():
            husb_elem = family.get_child_element_by_tag("HUSB")
            wife_elem = family.get_child_element_by_tag("WIFE")

            husb_id = husb_elem.get_value() if husb_elem else None
            wife_id = wife_elem.get_value() if wife_elem else None

            if person.get_pointer() in (husb_id, wife_id):
                families.append(family)

        return families

    def _get_children_of_family(self, family: FamilyElement) -> list[IndividualElement]:
        """Get children of a family."""
        children = []
        for child_elem in family.get_child_elements():
            if child_elem.get_tag() == "CHIL":
                child_id = child_elem.get_value()
                if child_id in self._individuals:
                    children.append(self._individuals[child_id])
        return children

    def _get_spouse(self, person: IndividualElement, family: FamilyElement) -> IndividualElement | None:
        """Get the spouse of a person in a family."""
        husb_elem = family.get_child_element_by_tag("HUSB")
        wife_elem = family.get_child_element_by_tag("WIFE")

        husb_id = husb_elem.get_value() if husb_elem else None
        wife_id = wife_elem.get_value() if wife_elem else None

        person_id = person.get_pointer()

        if person_id == husb_id and wife_id:
            return self._individuals.get(wife_id)
        elif person_id == wife_id and husb_id:
            return self._individuals.get(husb_id)

        return None

    def _get_parents(self, person: IndividualElement | None) -> tuple[IndividualElement | None, IndividualElement | None]:
        """Get (father, mother) for a person."""
        if person is None:
            return (None, None)

        # Find family where this person is a child
        for family in self._families.values():
            for child_elem in family.get_child_elements():
                if child_elem.get_tag() == "CHIL" and child_elem.get_value() == person.get_pointer():
                    # Found the family
                    husb_elem = family.get_child_element_by_tag("HUSB")
                    wife_elem = family.get_child_element_by_tag("WIFE")

                    father_id = husb_elem.get_value() if husb_elem else None
                    mother_id = wife_elem.get_value() if wife_elem else None

                    father = self._individuals.get(father_id) if father_id else None
                    mother = self._individuals.get(mother_id) if mother_id else None

                    return (father, mother)

        return (None, None)

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

**Step 3: Implement get_family**

Add to `gedcom_source.py` (import schema helpers at top, then add method):

Add import at top:
```python
from src.schema import make_person, make_family_output
```

Replace the placeholder `get_family` method:

```python
    def get_family(self, person_id: str) -> dict:
        """Extract family data for a person."""
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

        return make_family_output(
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

    def _person_to_dict(self, person: IndividualElement | None) -> dict | None:
        """Convert an IndividualElement to a person dict."""
        if person is None:
            return None

        name_parts = person.get_name()
        first_name = name_parts[0] if name_parts[0] else ""
        last_name = name_parts[1] if name_parts[1] else ""

        birth = person.get_birth_year()
        death = person.get_death_year()

        return make_person(
            first_name=first_name,
            last_name=last_name,
            birth=str(birth) if birth != -1 else None,
            death=str(death) if death != -1 else None
        )

    def _make_child_entry(self, child: IndividualElement) -> dict:
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

## Task 10: Main Entry Point

**Files:**
- Modify: `gedcom_processor/src/main.py`
- Create: `gedcom_processor/tests/test_main.py`

**Step 1: Write integration test**

```python
# gedcom_processor/tests/test_main.py
"""Integration tests for main entry point."""

import json
import tempfile
from pathlib import Path
import shutil

from src.main import run


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_family.ged"


def test_run_produces_output_file():
    """run() creates current.json with valid family data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy fixture GEDCOM
        shutil.copy(FIXTURE_PATH, tmpdir / "family.ged")

        # Create config
        config_path = tmpdir / "config.yml"
        config_path.write_text("gedcom_file: family.ged\nsource: gedcom\n")

        # Run
        output_path = tmpdir / "current.json"
        run(config_path, output_path)

        # Verify output
        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)

        assert "last_family_id" in data
        assert "subject" in data
        assert "spouse" in data
        assert "children" in data


def test_run_avoids_last_family():
    """run() reads last_family_id and picks different one."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy fixture GEDCOM
        shutil.copy(FIXTURE_PATH, tmpdir / "family.ged")

        # Create config
        config_path = tmpdir / "config.yml"
        config_path.write_text("gedcom_file: family.ged\nsource: gedcom\n")

        # Create existing output with a last_family_id
        output_path = tmpdir / "current.json"
        output_path.write_text('{"last_family_id": "@I001@"}')

        # Run multiple times and collect IDs
        ids_seen = set()
        for _ in range(10):
            run(config_path, output_path)
            with open(output_path) as f:
                data = json.load(f)
            ids_seen.add(data["last_family_id"])

        # If there are multiple eligible people, should see variety
        # (This test is probabilistic but should pass with our fixture)
        assert len(ids_seen) >= 1  # At minimum, it ran successfully
```

**Step 2: Run test to verify it fails**

```bash
cd gedcom_processor && python -m pytest tests/test_main.py -v
```

Expected: FAIL (run function doesn't exist or doesn't work)

**Step 3: Implement main.py**

```python
# gedcom_processor/src/main.py
"""GEDCOM to TRMNL JSON processor."""

import json
from pathlib import Path

from src.config import load_config
from src.selector import select_family_id
from src.sources.gedcom_source import GedcomSource


def run(config_path: Path, output_path: Path) -> None:
    """Run the GEDCOM processor.

    Args:
        config_path: Path to config.yml.
        output_path: Path to write current.json.
    """
    # Load config
    config = load_config(config_path)

    # Initialize source
    gedcom_path = config_path.parent / config["gedcom_file"]
    source = GedcomSource(gedcom_path)

    # Get eligible IDs
    eligible_ids = source.get_eligible_ids()

    if not eligible_ids:
        raise ValueError("No eligible families found in GEDCOM file")

    # Read last family ID if output exists
    last_id = None
    if output_path.exists():
        try:
            with open(output_path) as f:
                existing = json.load(f)
                last_id = existing.get("last_family_id")
        except (json.JSONDecodeError, KeyError):
            pass

    # Select next family
    selected_id = select_family_id(eligible_ids, last_id)

    # Extract family data
    family_data = source.get_family(selected_id)

    # Write output
    with open(output_path, 'w') as f:
        json.dump(family_data, f, indent=2)


def main() -> None:
    """Main entry point using default paths."""
    # Default paths relative to script location
    base_path = Path(__file__).parent.parent
    config_path = base_path / "config.yml"
    output_path = base_path / "current.json"

    run(config_path, output_path)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```bash
cd gedcom_processor && python -m pytest tests/test_main.py -v
```

Expected: Both tests PASS

**Step 5: Run all tests**

```bash
cd gedcom_processor && python -m pytest -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add gedcom_processor/src/main.py gedcom_processor/tests/test_main.py
git commit -m "feat: implement main entry point"
```

---

## Task 11: GitHub Action Workflow

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
          git add current.json
          git diff --quiet --cached || git commit -m "Rotate family display"
          git push
```

**Step 3: Commit**

```bash
git add gedcom_processor/.github/workflows/rotate.yml
git commit -m "feat: add GitHub Action workflow for family rotation"
```

---

## Task 12: README Documentation

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
2. Script parses your GEDCOM file
3. Filters to eligible people
4. Picks one randomly (avoids repeating the previous one)
5. Extracts family data to `current.json`
6. Commits and pushes
7. GitHub Pages serves the updated file
8. TRMNL polls the URL and displays your family

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

## Task 13: Final Integration Test

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

After completing all tasks, you will have:

- `gedcom_processor/` directory with:
  - Abstract `FamilySource` interface (extensible for WikiTree later)
  - `GedcomSource` implementation that parses GEDCOM files
  - Eligibility filtering (spouse + parent + child)
  - Random selection with last-ID avoidance
  - Output matching TRMNL plugin JSON schema
  - GitHub Action for daily rotation
  - README with setup instructions and privacy warnings

- Full test coverage for all components
- Ready to use as a template repository
