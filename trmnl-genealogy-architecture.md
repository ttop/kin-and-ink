# TRMNL Genealogy Plugin - Architecture Summary

## Overview

This document captures the architectural decisions for a genealogy-themed TRMNL e-ink display plugin. The project serves dual purposes: creating a useful genealogy display and demonstrating Claude Code's capabilities for building an app from scratch.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Repository                                              │
│                                                                 │
│  ├── .github/workflows/generate.yml   ← Cron + manual trigger  │
│  ├── scripts/generate_data.py         ← Builds the JSON        │
│  └── docs/data.json                   ← Served via GitHub Pages│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼  TRMNL polls this URL
                https://[username].github.io/[repo]/data.json
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TRMNL Private Plugin (configured via web UI)                   │
│                                                                 │
│  - Strategy: Polling                                            │
│  - Polling URL: GitHub Pages JSON endpoint                      │
│  - Markup: Liquid templates referencing JSON keys               │
│  - Refresh Rate: 15 min minimum (free tier)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   TRMNL Device   │
                    │   (e-ink display)│
                    └──────────────────┘
```

---

## Component Breakdown

### 1. Data Generation (GitHub Actions)

**Purpose:** Generate fresh JSON data on a schedule or on-demand.

**Location:** `.github/workflows/generate.yml`

**Triggers:**
- `schedule` (cron) — e.g., daily at midnight
- `workflow_dispatch` — manual trigger for demos

**What it does:**
1. Runs a Python (or Node) script
2. Generates JSON with genealogy data
3. Commits the JSON to the `docs/` folder
4. GitHub Pages serves it automatically

**Demo benefit:** Manual trigger allows instant updates during live demos without waiting for the 15-minute poll cycle.

---

### 2. Data Hosting (GitHub Pages)

**Purpose:** Serve static JSON over HTTPS with zero infrastructure.

**Setup:**
- Enable GitHub Pages on the repo (Settings → Pages)
- Point it at the `docs/` folder on `main` branch
- JSON becomes available at `https://[username].github.io/[repo]/data.json`

**Why this approach:**
- Free
- No server to manage
- Familiar to most developers
- Version-controlled data history

**Repository Strategy (Two-Repo Architecture):**

For the production project, use a private + public repo setup:

```
┌─────────────────────────────────────────┐
│  PRIVATE REPO: trmnl-genealogy          │
│                                         │
│  ├── .github/workflows/generate.yml     │
│  ├── scripts/generate_data.py           │
│  ├── data/                (source data) │
│  └── src/                 (liquid templates for local dev) │
└─────────────────────────────────────────┘
                    │
                    │ GitHub Action pushes data.json
                    ▼
┌─────────────────────────────────────────┐
│  PUBLIC REPO: trmnl-genealogy-data      │
│                                         │
│  └── data.json            (GitHub Pages)│
└─────────────────────────────────────────┘
```

- **Private repo** contains generation scripts, source data, and Liquid templates
- **Public repo** only contains the generated `data.json`, served via GitHub Pages
- GitHub Action in private repo uses a deploy key or PAT to push to the public repo
- Keeps implementation details private while exposing only the data endpoint

---

### 3. TRMNL Private Plugin

**Purpose:** Define how the data is displayed on the e-ink screen.

**Strategy:** Polling (TRMNL fetches JSON from your URL)

**Configuration (done in TRMNL web UI):**
- Polling URL: your GitHub Pages endpoint
- Polling Verb: GET
- Refresh Rate: configurable (15 min minimum on free tier)

**Markup:** HTML + Liquid templates stored in TRMNL
- Developed locally using `trmnlp` dev server
- Pushed to TRMNL via `trmnlp push` command

---

### 4. Local Development (trmnlp)

**Purpose:** Iterate on plugin markup locally with hot reload.

**Features:**
- Full TRMNL Framework CSS/JS
- Custom Liquid filters (via `trmnl-liquid` gem)
- Live preview in browser
- Direct push to TRMNL account

**Workflow:**
```bash
trmnlp init my_plugin    # scaffold
cd my_plugin
trmnlp serve             # local dev server at localhost:4567
# ... edit .liquid files, see changes instantly ...
trmnlp login             # authenticate
trmnlp push              # upload to TRMNL
```

---

## Data Flow Summary

| Step | Who | What |
|------|-----|------|
| 1 | GitHub Action | Runs script, generates JSON, commits to repo |
| 2 | GitHub Pages | Serves JSON at public URL |
| 3 | TRMNL Server | Polls URL every N minutes, fetches JSON |
| 4 | TRMNL Server | Merges JSON into Liquid template, renders image |
| 5 | TRMNL Device | Wakes up, fetches rendered image, displays it |

---

## Key Technical Details

### TRMNL Display Specs
- Resolution: 800×480 pixels
- Color: Black and white, 2-bit grayscale
- Refresh: Device wakes periodically (configurable)

### Liquid Templating
- Standard Liquid (Shopify's open-source engine)
- TRMNL custom filters: `l_date`, `l_word`, `number_to_currency`, `parse_json`, etc.
- Global variables available: `{{ trmnl.user.first_name }}`, `{{ trmnl.user.utc_offset }}`, etc.

### Rate Limits (Free Tier)
- Plugin refresh: minimum 15 minutes
- Webhook pushes: 12/hour (if using webhook strategy instead)
- Data payload: max 2KB

---

## Genealogy Feature Ideas (Future)

These are potential features to implement; scope TBD:

1. **"On This Day"** — Show ancestors with birthdays/death dates matching today
2. **Random Ancestor Spotlight** — Display a random person with name, dates, photo
3. **Family Tree Snippet** — Visual representation of a branch
4. **Research Tasks** — List of genealogy to-dos
5. **Anniversary Reminders** — Upcoming family milestones

---

## Demo Flow

For the Claude Code demonstration:

1. **Pre-demo prep:**
   - Docker installed
   - `trmnlp` environment ready
   - GitHub repo created with Pages enabled
   - TRMNL Private Plugin created (Polling strategy, pointed at repo)

2. **Live demo:**
   - Use Claude Code to generate the data script
   - Use Claude Code to create the GitHub Action workflow
   - Use Claude Code to build the Liquid markup
   - Push everything, trigger the action, force-refresh TRMNL
   - Watch content appear on the physical device

---

## Open Questions

- **Data source:** Hardcoded sample data? GEDCOM file? FamilySearch API?
- **Feature scope:** Start with one feature (e.g., "On This Day") or multiple?
- **Mashup support:** Build all layout sizes (full, half, quadrant) or just full?
