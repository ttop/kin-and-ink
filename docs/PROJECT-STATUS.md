# Kin & Ink Project Status

**Last Updated:** 2026-01-18

---

## Project Overview

**Kin & Ink** is a TRMNL e-ink display plugin (800x480 pixels) for displaying genealogy/pedigree charts. The project has two main components:

1. **TRMNL Plugin** (`trmnl/`) - Liquid templates for rendering pedigree charts on e-ink
2. **GEDCOM Processor** (`gedcom_processor/`) - Python pipeline to extract family data from GEDCOM files

---

## Component 1: TRMNL Plugin

### Status: Complete ✅

**Deployed:** Plugin ID 192541

**Features:**
- Vertical layout with subject/spouse boxes in center
- Parents stacked vertically on left (subject's) and right (spouse's) sides
- SVG bracket-style connector lines
- Georgia serif typography optimized for e-ink (12px first names, 14px bold last names, 11px dates)
- Responsive children section:
  - ≤15 children: Single column with spouses
  - >15 children: Two-column grid, children only
- Photo frames (currently commented out)

**Key Files:**
- `trmnl/src/full.liquid` - Main template
- `trmnl/.trmnlp.yml` - Current data configuration
- `trmnl/.trmnlp.small-family.yml` / `.trmnlp.large-family.yml` - Test configs

**Local Development:**
```bash
# Start server (Docker)
cd trmnl && trmnlp serve

# Preview at http://localhost:4567/full

# Switch test configs
./switch-config.sh small  # or large
```

---

## Component 2: GEDCOM Processor

### Status: Nearly Complete ✅

**Goal:** Build a Python script that extracts family data from GEDCOM files and outputs JSON for the TRMNL plugin, runnable via GitHub Actions.

**Architecture:**
```
family.ged → [parse] → families.json (cache) → [select random] → current.json → TRMNL polls
```

### Completed Tasks (1-13)

| Task | Description | Files |
|------|-------------|-------|
| 1 | Project scaffold | `requirements.txt`, `config.yml`, `src/main.py` |
| 2 | FamilySource ABC | `src/sources/base.py` |
| 3 | Output schema helpers | `src/schema.py` |
| 4 | Selector logic | `src/selector.py` |
| 5 | Test GEDCOM fixture | `tests/fixtures/test_family.ged` |
| 6 | GedcomSource - parsing | `src/sources/gedcom_source.py` |
| 7 | GedcomSource - eligibility | Checks: has spouse + children + at least one parent |
| 8 | GedcomSource - get_family | Returns full family data in TRMNL-ready format |
| 9 | Config loading | `src/config.py` |
| 10 | Cache layer | `src/cache.py` |
| 11 | Main entry point | `src/main.py`, `generate.py` (CLI with PEP 723) |
| 12 | GitHub Action workflow | `.github/workflows/rotate.yml` |
| 13 | README documentation | `README.md` |

**Test Status:** 35 tests passing

### Remaining Task

| Task | Description |
|------|-------------|
| 14 | Final integration test with real GEDCOM + GitHub Pages setup |

### Usage

```bash
# Generate current.json from a GEDCOM file
uv run gedcom_processor/generate.py /path/to/family.ged

# Specify output directory
uv run gedcom_processor/generate.py /path/to/family.ged -o ./output/

# Run tests
cd gedcom_processor && uv run python -m unittest discover -v
```

### Technical Notes

**ged4py quirks discovered:**
- `sub_tags()` follows references and returns the referenced record
- Use `sub_records` to get raw Pointer objects with actual xref values
- Name values are tuples: `(given, surname, suffix)`
- Date values are `DateValueSimple` objects (convert to string for parsing)

---

## Output Files

| File | Purpose |
|------|---------|
| `families.json` | Cache of all eligible families (regenerated when GEDCOM changes) |
| `current.json` | **TRMNL data source** - selected family in TRMNL-ready format |

Note: Output files go in the same directory as the GEDCOM file by default, or in the directory specified with `-o`.

---

## Key Documentation

- `CLAUDE.md` - Project context and current state
- `gedcom_processor/README.md` - Setup and usage instructions
- `docs/plans/2025-12-09-gedcom-pipeline-design.md` - Architecture design doc
- `docs/plans/2025-12-09-gedcom-pipeline-implementation.md` - Implementation plan

---

## To Deploy

1. Push this repo to GitHub
2. Add your GEDCOM file as `family.ged` in the repo root
3. Enable GitHub Pages (Settings → Pages → Deploy from main branch)
4. Run the "Rotate Family" workflow manually (Actions tab)
5. Copy your GitHub Pages URL (`https://<user>.github.io/<repo>/current.json`) to TRMNL plugin settings
