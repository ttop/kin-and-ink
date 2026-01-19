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

### Status: In Progress 🔄

**Goal:** Build a Python script that extracts family data from GEDCOM files and outputs JSON for the TRMNL plugin, runnable via GitHub Actions.

**Architecture:**
```
family.ged → [parse] → families.json (cache) → [select random] → current.json → TRMNL polls
```

### Completed Tasks (1-8)

| Task | Description | Files |
|------|-------------|-------|
| 1 | Project scaffold | `requirements.txt`, `config.yml`, `src/main.py` |
| 2 | FamilySource ABC | `src/sources/base.py` |
| 3 | Output schema helpers | `src/schema.py` (make_person, make_family_entry, family_to_current) |
| 4 | Selector logic | `src/selector.py` (random with last-ID avoidance) |
| 5 | Test GEDCOM fixture | `tests/fixtures/test_family.ged` |
| 6 | GedcomSource - parsing | `src/sources/gedcom_source.py` (uses ged4py) |
| 7 | GedcomSource - eligibility | Checks: has spouse + children + at least one parent |
| 8 | GedcomSource - get_family | Returns full family data in TRMNL-ready format |

**Test Status:** 23 tests passing

```bash
cd /workspace/gedcom_processor
source .venv/bin/activate
python3 -m unittest discover -v
```

### Next Tasks (9-11) - Creates current.json!

| Task | Description | Files to Create |
|------|-------------|-----------------|
| 9 | Config loading | `src/config.py`, `tests/test_config.py` |
| 10 | Cache layer | `src/cache.py`, `tests/test_cache.py` |
| 11 | Main entry point | Update `src/main.py`, `tests/test_main.py` |

### Remaining Tasks (12-14)

| Task | Description |
|------|-------------|
| 12 | GitHub Action workflow (`.github/workflows/rotate.yml`) |
| 13 | README documentation |
| 14 | Final integration test |

### Technical Notes

**ged4py quirks discovered:**
- `sub_tags()` follows references and returns the referenced record
- Use `sub_records` to get raw Pointer objects with actual xref values
- Name values are tuples: `(given, surname, suffix)`
- Date values are `DateValueSimple` objects (convert to string for parsing)

**Environment:**
```bash
cd /workspace/gedcom_processor
source .venv/bin/activate
python3 -m unittest discover -v  # Run tests
```

---

## Output Files (When Complete)

| File | Purpose |
|------|---------|
| `gedcom_processor/families.json` | Cache of all eligible families (regenerated when GEDCOM changes) |
| `gedcom_processor/current.json` | **TRMNL data source** - selected family in TRMNL-ready format |

---

## Key Documentation

- `CLAUDE.md` - Project context and current state
- `kin-and-ink-requirements.md` - Requirements doc
- `docs/plans/2025-12-09-gedcom-pipeline-implementation.md` - **Detailed implementation plan with code for all remaining tasks**

---

## To Continue

1. Read the implementation plan: `docs/plans/2025-12-09-gedcom-pipeline-implementation.md`
2. Start with Task 9 (Config Loading)
3. Use the executing-plans skill for step-by-step implementation

```
continue implementing the gedcom processor from task 9
```
