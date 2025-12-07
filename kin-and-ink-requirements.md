# Kin & Ink — Requirements Document

## Overview

**Product Name:** Kin & Ink  
**Repository Name:** `kin-and-ink`  
**Platform:** TRMNL e-ink display  
**Purpose:** Display genealogy/family history information on a TRMNL device

---

## Goals

1. Create a visually appealing genealogy display optimized for e-ink
2. Demonstrate Claude Code's ability to build a project from scratch
3. Keep scope small enough for a single demo session
4. Make something personally useful (not just a throwaway demo)

---

## Display Specifications

- **Resolution:** 800×480 pixels
- **Color depth:** 2-bit grayscale (black, white, two grays)
- **PPI:** ~124
- **Refresh rate:** Configurable (15 min minimum on free tier)

---

## Primary Display: Pedigree Chart

Based on the provided mockup, the main view shows:

### Layout Elements

1. **Grandparents Row** (top)
   - Subject's parents (father, mother) — left side
   - Spouse's parents (father, mother) — right side
   - Each person in a bordered box with name and birth-death years

2. **Connector Lines**
   - Brackets connecting parents to their child
   - Horizontal line connecting subject to spouse

3. **Main Row** (center)
   - Subject's photo — far left
   - Subject's info box — center left
   - Spouse's info box — center right
   - Spouse's photo — far right

4. **Children Section** (bottom)
   - List of children with birth-death years
   - Spouse names where applicable (format: "m. [spouse name]")

### Data Requirements

For each pedigree display:

```
subject
├── name
├── birth year
├── death year (nullable)
└── photo_url (optional)

spouse
├── name
├── birth year
├── death year (nullable)
└── photo_url (optional)

subject_parents
├── father
│   ├── name
│   ├── birth year
│   └── death year (nullable)
└── mother
    ├── name
    ├── birth year
    └── death year (nullable)

spouse_parents
├── father
│   ├── name
│   ├── birth year
│   └── death year (nullable)
└── mother
    ├── name
    ├── birth year
    └── death year (nullable)

children[] (array)
├── name
├── birth year
├── death year (nullable)
└── spouse (string, nullable)
```

---

## Architecture

### Two-Repository Setup

**Private Repository:** `kin-and-ink`
- GitHub Actions workflow (generates JSON)
- Data generation script (Python)
- Source genealogy data
- Liquid templates (for local development with trmnlp)
- Documentation

**Public Repository:** `kin-and-ink-data`
- `data.json` only (served via GitHub Pages)
- Keeps implementation private while exposing data endpoint

### Data Flow

```
[Source Data] 
    → [GitHub Action runs generation script]
    → [JSON pushed to public repo]
    → [GitHub Pages serves JSON]
    → [TRMNL polls JSON endpoint]
    → [TRMNL renders Liquid template with data]
    → [Device displays rendered image]
```

### Refresh Strategy

- **GitHub Action:** Runs daily (cron) + manual trigger for demos
- **TRMNL Polling:** 15–60 minutes (TBD based on testing)
- **Data selection:** Generation script selects which family to display

---

## Data Selection Logic

The source dataset may contain many families. The generation script should select one to display. Options:

1. **Random selection** — Different family each generation
2. **"On this day"** — Family with anniversary/birthday matching today
3. **Rotating schedule** — Cycle through families in order
4. **Manual override** — Specify family via workflow input

**MVP:** Random selection  
**Future:** "On this day" matching

---

## Photo Handling

- Photos hosted in public repo or external service (Google Drive, etc.)
- URLs included in JSON data
- Template uses `image-dither` class for e-ink optimization
- Ideal dimensions: TBD (roughly 100×130 based on layout)
- Fallback: Display placeholder or hide photo div if URL missing

---

## Edge Cases & Data Quality

Handle gracefully:
- Missing death year → Display "?" or birth year only
- Missing photo → Hide photo area or show placeholder
- Missing spouse → Adjust layout (single-person display?)
- Too many children → Limit display count, use overflow indicator
- Long names → Truncate or reduce font size
- Missing parents → Show "Unknown" or hide box

---

## Technical Implementation

### Local Development

- Docker with `trmnl/trmnlp` image
- Volume mount for live editing
- Sample data in `.trmnlp.yml` for preview
- Push to TRMNL via `trmnlp push`

### Template Structure

```
src/
├── full.liquid              # Main pedigree layout (800×480)
├── half_horizontal.liquid   # Future: simplified view
├── half_vertical.liquid     # Future: simplified view
├── quadrant.liquid          # Future: minimal view
├── shared.liquid            # Reusable components (SVG icons, etc.)
└── settings.yml             # Plugin configuration
```

### Styling Approach

- Use TRMNL Framework classes where possible
- Custom CSS for pedigree-specific elements (boxes, connectors)
- SVG for connector lines (or CSS borders if simpler)
- Inline styles acceptable for MVP, refactor later

---

## MVP Scope

For the initial demo:

- [x] Architecture defined
- [ ] Private repo created with GitHub Action
- [ ] Public repo created with GitHub Pages
- [ ] Generation script (hardcoded sample data initially)
- [ ] Liquid template matching mockup layout
- [ ] Photos hosted and displaying
- [ ] End-to-end flow working (push data → TRMNL displays)

**Out of scope for MVP:**
- Multiple layout sizes (half, quadrant)
- "On this day" logic
- GEDCOM file parsing
- FamilySearch API integration
- Recipe publication

---

## Future Enhancements

1. **Additional views**
   - Ancestor fan chart
   - Descendant tree
   - Individual biography view

2. **Data sources**
   - GEDCOM file import
   - FamilySearch API
   - Ancestry API

3. **Smart selection**
   - Birthday/anniversary matching ("On this day")
   - Weighted random (favor less-seen families)
   - User-defined rotation schedule

4. **Polish**
   - All TRMNL layout sizes (mashup support)
   - Recipe publication for community
   - Dark mode support

---

## Open Questions

1. **Source data format:** Start with hardcoded JSON? GEDCOM? 
2. **Photo storage:** Include in public repo or use external hosting?
3. **Children overflow:** Max count to display? Two columns?
4. **Connector lines:** SVG vs CSS borders — which is more maintainable?
5. **Font sizes:** Need to test readability at 11-12px on actual device

---

## References

- [Architecture Summary](./trmnl-genealogy-architecture.md)
- [trmnlp Setup Guide](./trmnlp-setup-guide.md)
- [Project Setup Guide](./trmnl-project-setup.md)
- [TRMNL Framework Docs](https://usetrmnl.com/framework)
- [Liquid Documentation](https://shopify.github.io/liquid/)
