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

### Config Switching for Testing

Two test configurations are available:
- `.trmnlp.small-family.yml` - 11 children with spouses (single-column layout)
- `.trmnlp.large-family.yml` - 20 children without spouses (two-column layout)

Use `./switch-config.sh small` or `./switch-config.sh large` to swap between them. See `README-CONFIG-SWITCHING.md` for details.

### Rendering Modes

The TRMNL simulator supports two rendering modes:
- **HTML mode**: Fast browser rendering for development
- **PNG mode**: More accurate representation using dithering, matches actual e-ink display behavior

**IMPORTANT**: Always test in PNG mode before deployment. The PNG renderer applies dithering that can expose rendering artifacts not visible in HTML mode (e.g., SVG path issues, anti-aliasing problems).

**Dithering Options**: The TRMNL platform has multiple dithering options available. User wants to explore these different dithering algorithms in the future to optimize the appearance of the pedigree chart on the e-ink display.

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
- Changed photo display from `object-fit: cover` to `object-fit: contain`
- Removed photo frame borders and backgrounds at user request
- Refactored children data format to support `first`/`second` person per entry with `child: true` flag
- Updated `kin-and-ink-requirements.md` to document new data format
- Added responsive children layout: 2-column grid for >15 children (children only, no spouses)
- Tested capacity limits: single-column max 16, two-column handles 30+ easily
- Created config switching system with `switch-config.sh` and two test configs
- Successfully deployed plugin to TRMNL (plugin ID: 192541) using Docker with config volume mounting
- Updated `genealogy-sample-data.json` to match the `first`/`second` schema

## Known Issues

**SVG Connector Lines in PNG Mode**: The connector lines have duplicate path segments (e.g., `L 206,47 L 206,47`) which cause thickness artifacts in PNG rendering mode where the dithering makes the overlapping paths visible. The lines need to be redrawn without duplicates while maintaining the correct bracket shape.

The current working SVG paths from commit d0c600c (these display correctly but have the duplicate issue):
```svg
<!-- Left bracket: connects subject's parents to subject -->
<path d="M 133,0 L 133,47 L 206,47" stroke="black" fill="none" stroke-width="1"/>
<path d="M 278,0 L 278,47 L 206,47 L 206,47 L 278,47 L 278,94" stroke="black" fill="none" stroke-width="1"/>

<!-- Right bracket: connects spouse's parents to spouse -->
<path d="M 455,0 L 455,47 L 528,47" stroke="black" fill="none" stroke-width="1"/>
<path d="M 600,0 L 600,47 L 528,47 L 528,47 L 455,47 L 455,94" stroke="black" fill="none" stroke-width="1"/>
```

The duplicates (`L 206,47 L 206,47` and `L 528,47 L 528,47`) need to be removed without breaking the visual appearance. Each bracket should create a shape that goes down from both grandparent boxes, meets at a horizontal line at y=47, then goes down to the subject/spouse box.
