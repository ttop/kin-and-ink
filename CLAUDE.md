# Kin & Ink - TRMNL Genealogy Plugin

## Project Context

This is a TRMNL e-ink display plugin (800x480 pixels) for displaying genealogy/pedigree charts. We're developing in a git worktree (`trmnlp-plugin-dev` branch) off the main `kin-and-ink` repo.

## Current State

The `full.liquid` template displays a pedigree chart with:
- **Vertical layout**: Three columns across the top
  - **Left column**: Subject's parents (father and mother stacked vertically)
  - **Center**: Subject and spouse boxes side-by-side
  - **Right column**: Spouse's parents (father and mother stacked vertically)
- **SVG connector lines**: Bracket-style lines connecting parent boxes to subject/spouse
  - Lines connect at center of rectangle sides
  - Left bracket: coordinates x=175/200/224, y=48/122/84
  - Right bracket: coordinates x=604/580/555, y=48/122/84
- **Typography optimized for e-ink**:
  - Georgia serif font for better e-ink rendering
  - 12px first names, 14px bold last names, 11px dates
  - Clear typographic hierarchy
- **Photo frames**: Absolutely positioned at device edges (left/right), 140x165px, only rendered if `photo_url` exists (currently commented out)
- **Children section**: Responsive layout based on family size
  - **≤15 children**: Single column with spouses, format: "Child (dates) m. Spouse (dates)"
  - **>15 children**: Two-column grid, children only (no spouses), format: "Child (dates)"
  - The actual child is marked with `child: true` and shown in bold

## Data Format

The data lives in `kin_and_ink/.trmnlp.yml` under `variables:`. Key structure:

```yaml
subject/spouse:
  first_name, last_name, birth, death, photo_url

subject_parents/spouse_parents:
  father: {first_name, last_name, birth, death}
  mother: {first_name, last_name, birth, death}

children: (array of couples)
  - first:
      first_name, last_name, birth, death
      child: true  # boolean flag - this person is the child of subject/spouse
    second:        # optional, for married children
      first_name, last_name, birth, death
      # child: true goes on whichever person is the actual child
```

The `child: true` flag determines which name gets bolded in the display - this allows putting names in any order (e.g., men first) while correctly identifying who is the descendant.

**Schema uses `first_name` and `last_name` fields** (not single `name` field) to enable typographic hierarchy with small first names and large bold last names.

## Development Setup

**Network Firewall:** This devcontainer has a firewall that blocks most external network access. If you need to reach a network resource (package registry, API, documentation site, etc.) and get connection errors like "No route to host", ask me to enable it. The allowlist is in `.devcontainer/init-firewall.sh`.

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

### Vertical Layout Implementation
- Redesigned layout from horizontal grandparent row to vertical stacked columns
- Left column: subject's parents stacked vertically
- Right column: spouse's parents stacked vertically
- Center: subject and spouse boxes side-by-side
- Reduced box width from 180px to 160px to fit vertical layout
- Tightened gaps to 12px horizontal, 8px vertical

### Typography and E-ink Optimization
- Implemented `first_name`/`last_name` schema (replacing single `name` field)
- Added Georgia serif font for better e-ink rendering
- Created typographic hierarchy: 12px first names, 14px bold last names, 11px dates
- Updated all data in `.trmnlp.yml` and `genealogy-sample-data.json` to new schema

### SVG Connector Lines
- Redesigned connector lines for vertical layout
- Lines connect at exact center of rectangle sides
- Left bracket connects subject's parents to subject (x=175/200/224, y=48/122/84)
- Right bracket connects spouse's parents to spouse (x=604/580/555, y=48/122/84)
- Eliminated duplicate path segments that caused PNG rendering artifacts
- SVG positioned absolutely at top:0, left:0

### Deployment
- Successfully deployed plugin to TRMNL (plugin ID: 192541)
- Current size: 2416 bytes
- Pulled latest settings from server to sync local configuration

## Next Steps / Future Work

- Explore different dithering algorithms for optimal e-ink appearance
- Consider re-enabling photo frames (currently commented out)
- Test with larger families (capacity testing for two-column layout)
