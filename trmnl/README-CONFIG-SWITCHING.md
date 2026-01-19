# Configuration Switching for Testing

This directory contains multiple `.trmnlp.yml` configurations to easily test different family sizes and layouts.

## Quick Start

Switch between configurations using the shell script:

```bash
# Switch to small family (11 children, single column with spouses)
./switch-config.sh small

# Switch to large family (20 children, two-column layout)
./switch-config.sh large
```

The live reload should trigger automatically. If not, refresh http://localhost:4567/full

## Configuration Files

- **`.trmnlp.yml`** - Active configuration (used by Docker container)
- **`.trmnlp.small-family.yml`** - 11 children with spouses (single column layout)
- **`.trmnlp.large-family.yml`** - 20 children only (triggers two-column layout at >15 threshold)

## Layout Behavior

**Small family (≤15 children):**
- Single column layout
- Shows children with spouses
- Format: "**Child** (dates) m. Spouse (dates)"

**Large family (>15 children):**
- Two-column grid layout
- Shows children only (no spouses)
- Format: "**Child** (dates)"
- Alternates across columns then down

## Manual Switching

You can also manually copy configurations:

```bash
# Switch to small family
cp .trmnlp.small-family.yml .trmnlp.yml

# Switch to large family
cp .trmnlp.large-family.yml .trmnlp.yml
```

## Editing Configurations

Feel free to edit the preset files (`.trmnlp.small-family.yml` and `.trmnlp.large-family.yml`) to customize the test data. Your changes won't affect the active configuration until you run the switch script.
