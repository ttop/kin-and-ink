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
