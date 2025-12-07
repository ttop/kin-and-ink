# Kin & Ink - TRMNL Genealogy Plugin

## Project Context

This is a TRMNL e-ink display plugin (800x480 pixels) for displaying genealogy/pedigree charts. We're developing in a git worktree (`trmnlp-plugin-dev` branch) off the main `kin-and-ink` repo.

## Current State

The `full.liquid` template displays a pedigree chart with:
- **Grandparents row** (top): Subject's parents on left, spouse's parents on right
- **SVG connector lines**: Bracket-style lines connecting grandparents to parents, with 90-degree turns at 50% vertical distance
- **Main row** (center): Subject and spouse info boxes
- **Photo frames**: Absolutely positioned at device edges (left/right), 180x210px, only rendered if `photo_url` exists
- **Children section**: Responsive layout based on family size
  - **≤15 children**: Single column with spouses, format: "Child (dates) m. Spouse (dates)"
  - **>15 children**: Two-column grid, children only (no spouses), format: "Child (dates)"
  - The actual child is marked with `child: true` and shown in bold

## Data Format

The data lives in `kin_and_ink/.trmnlp.yml` under `variables:`. Key structure:

```yaml
subject/spouse:
  name, birth, death, photo_url

subject_parents/spouse_parents:
  father: {name, birth, death}
  mother: {name, birth, death}

children: (array of couples)
  - first:
      name, birth, death
      child: true  # boolean flag - this person is the child of subject/spouse
    second:        # optional, for married children
      name, birth, death
      # child: true goes on whichever person is the actual child
```

The `child: true` flag determines which name gets bolded in the display - this allows putting names in any order (e.g., men first) while correctly identifying who is the descendant.

## Development Setup

Docker container running `trmnl/trmnlp serve` mounted to `kin_and_ink/` directory. Preview at http://localhost:4567/full

Use Playwright MCP tools to interact with the preview:
- `mcp__playwright__browser_navigate` to load the page
- `mcp__playwright__browser_take_screenshot` to capture current state
- `mcp__playwright__browser_snapshot` for accessibility tree
- `mcp__playwright__browser_run_code` to run JS (e.g., measure element positions for SVG coordinates)

The SVG connector lines require precise x-coordinates. To recalculate them after layout changes, use Playwright to measure box positions and compute SVG-relative coordinates by subtracting the SVG's left position.

## Documentation

- `kin-and-ink-requirements.md` - Requirements doc with data format, layout elements, and architecture
- `trmnl-genealogy-architecture.md` - High-level architecture and data flow diagrams
- `trmnl-project-setup.md` - Project setup steps, Docker commands, settings.yml configuration
- `trmnlp-setup-guide.md` - trmnlp local dev setup, Hello World walkthrough

## Children Capacity Testing Results

**Single-column layout (with spouses):**
- ✅ 11-14 children: Comfortable fit
- ✅ 15-16 children: Very tight, barely fits
- ❌ 17+ children: Text overflow/cutoff

**Two-column layout (children only, >15 threshold):**
- ✅ 17-30 children: Fits well with plenty of room
- Estimated capacity: 35-40 children before overflow

**Implementation:** Template automatically switches to 2-column layout when `children.size > 15`, showing only the children (filtering by `child: true` flag) without spouses.

## Recent Work

- Fixed SVG connector line coordinates to align with box centers
- Repositioned photos to device edges with absolute positioning
- Made photos conditionally render (hidden when no `photo_url`)
- Refactored children data format to support `first`/`second` person per entry with `child: true` flag
- Updated `kin-and-ink-requirements.md` to document new data format
- Added responsive children layout: 2-column grid for >15 children (children only, no spouses)
- Tested capacity limits: single-column max 16, two-column handles 30+ easily
