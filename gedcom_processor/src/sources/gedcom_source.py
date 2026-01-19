"""GEDCOM file data source using ged4py library."""

import re
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
        # Store extracted data, not ged4py records (which require open file)
        self._individuals = {}  # id -> {name, sex, birth, death, fams, famc}
        self._families = {}     # id -> {husb, wife, children}

        with GedcomReader(str(file_path)) as reader:
            # Extract individual data
            for record in reader.records0("INDI"):
                indi_data = self._extract_individual(record)
                self._individuals[record.xref_id] = indi_data

            # Extract family data
            for record in reader.records0("FAM"):
                fam_data = self._extract_family(record)
                self._families[record.xref_id] = fam_data

    def _extract_individual(self, record) -> dict:
        """Extract data from an INDI record."""
        # Name - ged4py returns tuple (given, surname, suffix)
        name_rec = record.sub_tag("NAME")
        first_name = ""
        last_name = ""
        if name_rec and name_rec.value:
            name_val = name_rec.value
            if isinstance(name_val, tuple):
                first_name = name_val[0] or ""
                last_name = name_val[1] or ""
            elif isinstance(name_val, str):
                # Fallback for string format "First /Last/"
                if "/" in name_val:
                    parts = name_val.split("/")
                    first_name = parts[0].strip()
                    last_name = parts[1].strip() if len(parts) > 1 else ""
                else:
                    first_name = name_val.strip()

        # Sex
        sex_rec = record.sub_tag("SEX")
        sex = sex_rec.value if sex_rec else None

        # Birth
        birth = None
        birt_rec = record.sub_tag("BIRT")
        if birt_rec:
            date_rec = birt_rec.sub_tag("DATE")
            if date_rec and date_rec.value:
                birth = self._extract_year(date_rec.value)

        # Death
        death = None
        deat_rec = record.sub_tag("DEAT")
        if deat_rec:
            date_rec = deat_rec.sub_tag("DATE")
            if date_rec and date_rec.value:
                death = self._extract_year(date_rec.value)

        # Families as spouse (FAMS) - use sub_records to get Pointer values
        fams = []
        for rec in record.sub_records:
            if rec.tag == "FAMS" and rec.value:
                fams.append(rec.value)

        # Family as child (FAMC) - use sub_records to get Pointer value
        famc = None
        for rec in record.sub_records:
            if rec.tag == "FAMC" and rec.value:
                famc = rec.value
                break

        return {
            "first_name": first_name,
            "last_name": last_name,
            "sex": sex,
            "birth": birth,
            "death": death,
            "fams": fams,
            "famc": famc
        }

    def _extract_family(self, record) -> dict:
        """Extract data from a FAM record."""
        husb = None
        wife = None
        children = []

        for rec in record.sub_records:
            if rec.tag == "HUSB" and rec.value:
                husb = rec.value
            elif rec.tag == "WIFE" and rec.value:
                wife = rec.value
            elif rec.tag == "CHIL" and rec.value:
                children.append(rec.value)

        return {
            "husb": husb,
            "wife": wife,
            "children": children
        }

    def _extract_year(self, date_value) -> str | None:
        """Extract year from a GEDCOM date value.

        ged4py returns DateValueSimple objects, not strings.
        """
        if date_value is None:
            return None
        # Convert to string and extract 4-digit year
        date_str = str(date_value)
        match = re.search(r'\b(\d{4})\b', date_str)
        return match.group(1) if match else None

    def get_eligible_ids(self) -> list[str]:
        """Return list of eligible person IDs.

        Eligibility requires:
        - Has a spouse
        - Has at least one parent (on subject or spouse side)
        - Has at least one child
        """
        eligible = []

        for person_id, person in self._individuals.items():
            if self._is_eligible(person_id, person):
                eligible.append(person_id)

        return eligible

    def _is_eligible(self, person_id: str, person: dict) -> bool:
        """Check if a person meets eligibility criteria."""
        # Must have a spouse (be in a family as spouse)
        if not person["fams"]:
            return False

        # Check first spouse family for children
        family_id = person["fams"][0]
        family = self._families.get(family_id)
        if not family or not family["children"]:
            return False

        # Must have an actual spouse in the family (not just be listed in a FAM record)
        spouse_id = self._get_spouse_id(person_id, family)
        spouse = self._individuals.get(spouse_id) if spouse_id else None
        if spouse is None:
            return False

        # Must have at least one parent (on either side)
        person_parents = self._get_parents(person)
        spouse_parents = self._get_parents(spouse)

        has_any_parent = (
            person_parents[0] is not None or
            person_parents[1] is not None or
            spouse_parents[0] is not None or
            spouse_parents[1] is not None
        )

        return has_any_parent

    def _get_spouse_id(self, person_id: str, family: dict) -> str | None:
        """Get the spouse ID of a person in a family."""
        if person_id == family["husb"]:
            return family["wife"]
        elif person_id == family["wife"]:
            return family["husb"]
        return None

    def _get_parents(self, person: dict | None) -> tuple:
        """Get (father_id, mother_id) for a person."""
        if person is None or not person["famc"]:
            return (None, None)

        family = self._families.get(person["famc"])
        if not family:
            return (None, None)

        return (family["husb"], family["wife"])

    def get_family(self, person_id: str) -> dict:
        """Extract family data for a person in TRMNL-ready format."""
        from src.schema import make_person, make_family_entry

        person = self._individuals.get(person_id)
        if person is None:
            raise ValueError(f"Person {person_id} not found")

        # Get spouse and family
        family = None
        spouse = None
        spouse_id = None
        if person["fams"]:
            family_id = person["fams"][0]
            family = self._families.get(family_id)
            if family:
                spouse_id = self._get_spouse_id(person_id, family)
                spouse = self._individuals.get(spouse_id) if spouse_id else None

        # Get parents
        subject_father_id, subject_mother_id = self._get_parents(person)
        subject_father = self._individuals.get(subject_father_id) if subject_father_id else None
        subject_mother = self._individuals.get(subject_mother_id) if subject_mother_id else None

        spouse_father_id, spouse_mother_id = self._get_parents(spouse) if spouse else (None, None)
        spouse_father = self._individuals.get(spouse_father_id) if spouse_father_id else None
        spouse_mother = self._individuals.get(spouse_mother_id) if spouse_mother_id else None

        # Get children with their spouses
        children_data = []
        if family:
            for child_id in family["children"]:
                child = self._individuals.get(child_id)
                if child:
                    child_entry = self._make_child_entry(child_id, child)
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

    def _person_to_dict(self, person: dict | None) -> dict | None:
        """Convert internal person dict to output schema format."""
        from src.schema import make_person

        if person is None:
            return None

        return make_person(
            first_name=person["first_name"],
            last_name=person["last_name"],
            birth=person["birth"],
            death=person["death"]
        )

    def _make_child_entry(self, child_id: str, child: dict) -> dict:
        """Create a child entry with optional spouse."""
        from src.schema import make_person

        child_dict = make_person(
            first_name=child["first_name"],
            last_name=child["last_name"],
            birth=child["birth"],
            death=child["death"],
            child=True
        )

        # Check if child has a spouse
        if child["fams"]:
            child_family_id = child["fams"][0]
            child_family = self._families.get(child_family_id)
            if child_family:
                child_spouse_id = self._get_spouse_id(child_id, child_family)
                child_spouse = self._individuals.get(child_spouse_id) if child_spouse_id else None
                if child_spouse:
                    return {
                        "first": child_dict,
                        "second": self._person_to_dict(child_spouse)
                    }

        return {"first": child_dict}
