# GEDCOM Processor

Generates TRMNL-ready JSON from GEDCOM genealogy files for the Kin & Ink e-ink display plugin.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter the directory
cd gedcom_processor
```

That's it - `uv` handles dependencies automatically on first run.

## Usage

```bash
# Basic usage - outputs next to the GEDCOM file
uv run gedcom_processor/generate.py /path/to/family.ged

# Specify output directory
uv run gedcom_processor/generate.py /path/to/family.ged -o ./output/

# Show help
uv run gedcom_processor/generate.py --help
```

The script can be run from anywhere - dependencies are declared inline (PEP 723).

### Example

```bash
$ uv run ./generate.py ~/Documents/reyman-family.ged

Parsing GEDCOM file: /Users/you/Documents/reyman-family.ged
Cached 47 eligible families
Generated: /Users/you/Documents/current.json
  Subject: John Reyman
  Spouse:  Mary Smith
```

## Output Files

| File | Description |
|------|-------------|
| `current.json` | Selected family in TRMNL-ready format |
| `families.json` | Cache of all eligible families (regenerates if GEDCOM changes) |

### Sample `current.json`

```json
{
  "subject": {
    "first_name": "John",
    "last_name": "Reyman",
    "birth": "1850",
    "death": "1920"
  },
  "spouse": {
    "first_name": "Mary",
    "last_name": "Smith",
    "birth": "1855",
    "death": "1925"
  },
  "subject_parents": {
    "father": {"first_name": "William", "last_name": "Reyman", ...},
    "mother": {"first_name": "Elizabeth", "last_name": "Jones", ...}
  },
  "spouse_parents": {
    "father": {...},
    "mother": {...}
  },
  "children": [
    {
      "first": {"first_name": "James", "last_name": "Reyman", "child": true, ...},
      "second": {"first_name": "Alice", "last_name": "Williams", ...}
    }
  ],
  "last_family_id": "@I001@"
}
```

## How It Works

1. **Parses** the GEDCOM file using [ged4py](https://github.com/andy-z/ged4py)
2. **Finds eligible families** - people who have:
   - A spouse
   - At least one child
   - At least one parent (on either side)
3. **Caches** all eligible families to `families.json`
4. **Selects** a random family (different from last time)
5. **Outputs** the selected family to `current.json`

On subsequent runs, the cache is reused unless the GEDCOM file changes (detected via SHA256 hash).

## GitHub Actions (Automated Daily Rotation)

This repo includes a GitHub Action that automatically rotates the displayed family daily.

### Setup

1. **Add your GEDCOM file** to the repo root as `family.ged`

2. **Enable GitHub Pages**
   - Go to Settings → Pages
   - Set source to "Deploy from a branch"
   - Select `main` branch and `/ (root)` folder
   - Save

3. **Run the workflow**
   - Go to Actions → "Rotate Family"
   - Click "Run workflow"

4. **Configure TRMNL**
   - Copy your GitHub Pages URL: `https://<username>.github.io/<repo>/current.json`
   - Paste into your TRMNL genealogy plugin settings

The workflow runs daily at 6am UTC. Edit `.github/workflows/rotate.yml` to change the schedule.

### Privacy Warning

**Your GEDCOM file will be publicly visible** if your repository is public (required for free GitHub Pages).

Before uploading:
- **Remove living people** from your GEDCOM export
- Most genealogy software has an option to exclude living individuals
- Review the file for sensitive information

## Running Tests

```bash
uv run python -m unittest discover -v
```
