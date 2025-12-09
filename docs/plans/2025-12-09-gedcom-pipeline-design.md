# GEDCOM Data Pipeline Design

**Date:** 2025-12-09
**Status:** Draft

## Overview

A GitHub repo template that users clone. Contains a GitHub Action that runs on a schedule, picks a random person from a GEDCOM file, extracts their family data into JSON, and publishes it to GitHub Pages for consumption by the TRMNL genealogy plugin.

**Goals:**
- Showcase project suitable for a blog post
- Reproducible by motivated technical users (comfortable with GitHub)
- No local tools required — entirely browser-based workflow
- Simple enough to actually maintain

**Non-goals:**
- Mass adoption or non-technical user support
- Bulletproof privacy protection (documented warnings instead)

## User Flow

1. User clones/forks the template repo
2. Adds their GEDCOM file via GitHub's web UI
3. Edits `config.yml` to point to their GEDCOM filename
4. Enables GitHub Pages for the repo
5. GitHub Action runs on schedule (or manual trigger)
6. `current.json` is published to GitHub Pages
7. User copies the Pages URL into TRMNL plugin settings

## Architecture

### Components

```
├── family.ged              # User's GEDCOM file
├── current.json            # Output (generated, committed by Action)
├── config.yml              # User settings
├── requirements.txt        # Python dependencies
├── src/
│   ├── main.py             # Entry point
│   ├── sources/
│   │   ├── base.py         # Abstract data source interface
│   │   └── gedcom.py       # GEDCOM implementation
│   ├── selector.py         # Random selection logic
│   └── schema.py           # Output JSON structure
├── .github/
│   └── workflows/
│       └── rotate.yml      # Scheduled Action
└── README.md               # Setup instructions + privacy warnings
```

### Data Source Abstraction

The system is designed to support multiple data sources. Each source implements:

```python
class FamilySource:
    def get_eligible_ids(self) -> list[str]
    def get_family(self, person_id: str) -> dict
```

**Current:** GEDCOM file adapter

**Future possibility:** WikiTree API adapter (user provides list of WikiTree IDs, system fetches from public API — no privacy concerns since WikiTree excludes living people by design)

### Data Flow

On each scheduled run:

1. Action triggers (cron or manual)
2. Script reads `config.yml` to determine source type and file location
3. Script reads GEDCOM file from repo
4. Script parses GEDCOM, builds list of all people
5. Script filters to "eligible" people (criteria below)
6. Script reads `current.json` to get `last_family_id`
7. Script picks random eligible person (excluding last one)
8. Script extracts that person's family data
9. Script outputs `current.json` with family data + `last_family_id`
10. Action commits and pushes
11. GitHub Pages deploys automatically

### Eligibility Criteria

A person is eligible for display if they have:

- A spouse
- At least one parent on either side (subject or spouse)
- At least one child

These criteria ensure every section of the TRMNL display has content. The criteria logic should be encapsulated for easy modification later (different views may have different requirements).

### Selection Logic

- Random selection from eligible pool
- `last_family_id` stored in `current.json` itself (no separate state file)
- If random selection matches last family, pick again

## Output Format

`current.json` matches the TRMNL plugin's expected structure:

```json
{
  "last_family_id": "I0042",
  "subject": {
    "first_name": "John",
    "last_name": "Smith",
    "birth": "1842",
    "death": "1901"
  },
  "spouse": {
    "first_name": "Mary",
    "last_name": "Jones",
    "birth": "1845",
    "death": "1912"
  },
  "subject_parents": {
    "father": { "first_name": "...", "last_name": "...", "birth": "...", "death": "..." },
    "mother": { "first_name": "...", "last_name": "...", "birth": "...", "death": "..." }
  },
  "spouse_parents": {
    "father": { "first_name": "...", "last_name": "...", "birth": "...", "death": "..." },
    "mother": { "first_name": "...", "last_name": "...", "birth": "...", "death": "..." }
  },
  "children": [
    {
      "first": { "first_name": "...", "last_name": "...", "birth": "...", "death": "...", "child": true },
      "second": { "first_name": "...", "last_name": "...", "birth": "...", "death": "..." }
    }
  ]
}
```

## Configuration

**`config.yml`:**

```yaml
# Path to your GEDCOM file
gedcom_file: family.ged

# Data source type (for future: "wikitree", etc.)
source: gedcom
```

## GitHub Action

**`.github/workflows/rotate.yml`:**

```yaml
name: Rotate Family

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6am UTC
  workflow_dispatch:      # Manual trigger

jobs:
  rotate:
    runs-on: ubuntu-latest
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
          git diff --quiet --cached || git commit -m "Rotate family"
          git push
```

**Notes:**
- `workflow_dispatch` enables manual "Run workflow" button in GitHub UI
- `git diff --quiet --cached ||` prevents empty commits
- Git user config required because Actions environment has no default identity

## Privacy Considerations

**The problem:** GEDCOM files often contain information about living people. If the repo is public (required for free GitHub Pages), this data is exposed.

**Mitigations:**

1. **Documentation** — README prominently warns users to remove living people before uploading. Include links to guides for doing this in common genealogy software (Ancestry, FamilySearch, Gramps, etc.)

2. **Future option: auto-anonymization** — Script could detect likely-living people (no death date) and anonymize them in output: replace name with "LIVING", show only birth year. This protects the `current.json` output even if the source GEDCOM contains living people. (The raw GEDCOM would still be exposed, but the plugin wouldn't surface the sensitive data.)

**Accepted limitation:** Users who ignore warnings and publish sensitive data are responsible for that choice. This tool is for technical users who read documentation.

## Known Limitations

- **GitHub Actions 60-day timeout:** Scheduled workflows pause after 60 days of repo inactivity. User needs to occasionally make a commit or manually trigger the action. Will be documented.

- **Public repo required:** Free GitHub Pages requires public repos. Users who want private repos need GitHub Pro ($4/mo).

## Future Considerations

- **WikiTree data source:** Alternative to GEDCOM that's inherently public and excludes living people. User would provide a list of WikiTree IDs in config. May be a better fit for the target audience (genealogy + tech nerd overlap).

- **Different views:** Smaller TRMNL views might show just one person or a compacted layout. Different views may have different eligibility criteria.

- **Dithering options:** TRMNL has multiple dithering algorithms. May want to explore which works best for the pedigree chart.

## Supersedes

This design supersedes the earlier brainstorm document (`2025-12-07-gedcom-data-pipeline-brainstorm.md`), which explored a more complex browser-only approach with separate processing and rotation actions.
