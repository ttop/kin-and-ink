# TRMNL Plugin Project Setup

This guide describes how to set up a new TRMNL plugin project from scratch, intended for use by Claude Code. It assumes Docker and the `trmnl/trmnlp` image are already installed (see `trmnlp-setup-guide.md` for those steps).

---

## Prerequisites

- Docker installed and running
- `trmnl/trmnlp` image pulled (`docker pull trmnl/trmnlp`)
- GitHub CLI (`gh`) authenticated with repo/pages permissions
- TRMNL Developer account with API key

---

## Directory Structure

Each plugin project should be in its own directory:

```
~/projects/
├── trmnl-project-a/          # One plugin project
│   ├── plugin-name/          # Plugin scaffold (created by trmnlp init)
│   │   ├── .trmnlp.yml       # Local dev config & sample data
│   │   ├── bin/trmnlp
│   │   └── src/
│   │       ├── full.liquid
│   │       ├── half_horizontal.liquid
│   │       ├── half_vertical.liquid
│   │       ├── quadrant.liquid
│   │       ├── settings.yml  # Plugin settings (synced with TRMNL)
│   │       └── shared.liquid
│   ├── docs/
│   │   └── data.json         # Served via GitHub Pages
│   └── .gitignore
└── trmnl-project-b/          # Another plugin project
    └── ...
```

---

## Credential Persistence

The trmnlp CLI stores authentication in `/root/.config/trmnlp/config.yml` inside the container. To persist credentials between Docker invocations, mount a local config directory:

```bash
mkdir -p ~/.config/trmnlp
```

Then include this volume mount in all trmnlp commands:

```bash
--volume "$HOME/.config/trmnlp:/root/.config/trmnlp"
```

This config is shared across all projects (it's just the API key).

---

## Setup Steps

### 1. Create Project Directory

```bash
mkdir -p ~/projects/my-trmnl-project
cd ~/projects/my-trmnl-project
git init
```

### 2. Scaffold the Plugin

```bash
docker run --volume "$(pwd):/plugin" trmnl/trmnlp init my_plugin_name
cd my_plugin_name
```

This creates the plugin scaffold with default templates.

### 3. Configure Plugin Settings

Edit `src/settings.yml` with the plugin configuration:

```yaml
---
strategy: polling
no_screen_padding: 'no'
dark_mode: 'no'
static_data: ''
polling_verb: get
polling_url: 'https://USERNAME.github.io/REPO_NAME/data.json'
polling_headers: ''
name: My Plugin Name
refresh_interval: 1440
```

**Key settings:**

| Setting | Description |
|---------|-------------|
| `strategy` | `polling` (TRMNL fetches your URL), `static` (data embedded), or `webhook` (you push to TRMNL) |
| `polling_url` | Your GitHub Pages JSON endpoint |
| `polling_verb` | HTTP method: `get` or `post` |
| `polling_headers` | Optional HTTP headers (for authenticated endpoints) |
| `name` | Display name in TRMNL dashboard |
| `refresh_interval` | Minutes between refreshes (minimum 15 on free tier) |
| `dark_mode` | `'yes'` or `'no'` |
| `no_screen_padding` | `'yes'` for edge-to-edge display |

**Note:** After first `trmnlp push`, an `id` field is added automatically. This links the local project to the TRMNL plugin. Do not manually edit the `id`.

### 4. Configure Local Development Data

Edit `.trmnlp.yml` in the plugin directory with sample data for local preview:

```yaml
watch:
  - src
  - .trmnlp.yml

variables:
  # Add variables that match your data.json structure
  key_name: "sample value"
  another_key: "another value"
```

These variables are used when running the local dev server (`trmnlp serve`).

### 5. Create GitHub Repository and Pages

```bash
cd ~/projects/my-trmnl-project  # Back to project root

# Create docs folder with initial data.json
mkdir -p docs
cat > docs/data.json << 'EOF'
{
  "key_name": "value from GitHub Pages",
  "another_key": "another value"
}
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
.claude/
EOF

# Create GitHub repo
gh repo create REPO_NAME --public --source=. --remote=origin --description "TRMNL plugin"

# Commit and push
git add -A
git commit -m "Initial commit"
git push -u origin main

# Enable GitHub Pages on docs folder
gh api repos/USERNAME/REPO_NAME/pages -X POST --input - << 'EOF'
{
  "build_type": "legacy",
  "source": {
    "branch": "main",
    "path": "/docs"
  }
}
EOF
```

Wait ~30 seconds for Pages to build, then verify:

```bash
curl https://USERNAME.github.io/REPO_NAME/data.json
```

### 6. Login to TRMNL (One-Time)

If not already authenticated:

```bash
cd my_plugin_name
docker run -it \
  --volume "$(pwd):/plugin" \
  --volume "$HOME/.config/trmnlp:/root/.config/trmnlp" \
  trmnl/trmnlp login
```

Enter your API key when prompted (from https://usetrmnl.com/account).

### 7. Push Plugin to TRMNL

```bash
docker run \
  --volume "$(pwd):/plugin" \
  --volume "$HOME/.config/trmnlp:/root/.config/trmnlp" \
  trmnl/trmnlp push
```

This creates the plugin on TRMNL and writes the `id` back to `src/settings.yml`.

### 8. Add to Playlist

After pushing, add the plugin to your device playlist at https://usetrmnl.com/playlists.

---

## Common Docker Commands Reference

All commands assume you're in the plugin directory (where `.trmnlp.yml` lives).

**Start local dev server:**
```bash
docker run \
  --publish 4567:4567 \
  --volume "$(pwd):/plugin" \
  trmnl/trmnlp serve
```
Preview at http://localhost:4567

**Push changes to TRMNL:**
```bash
docker run \
  --volume "$(pwd):/plugin" \
  --volume "$HOME/.config/trmnlp:/root/.config/trmnlp" \
  trmnl/trmnlp push
```

**Note:** The push command prompts for confirmation ("Are you sure? y/n"). For non-interactive use (scripts, Claude Code), pipe "y" and use the `-i` flag with absolute paths (shell variables don't expand when piping):

```bash
echo "y" | docker run -i \
  --volume "/full/path/to/plugin:/plugin" \
  --volume "/Users/username/.config/trmnlp:/root/.config/trmnlp" \
  trmnl/trmnlp push
```

**Pull latest settings from TRMNL:**
```bash
docker run \
  --volume "$(pwd):/plugin" \
  --volume "$HOME/.config/trmnlp:/root/.config/trmnlp" \
  trmnl/trmnlp pull
```

---

## Updating Data (Polling Strategy)

To update the JSON data served to TRMNL:

1. Edit `docs/data.json`
2. Commit and push to GitHub
3. GitHub Pages rebuilds automatically (~30 seconds)
4. TRMNL fetches new data on next refresh cycle

To force immediate refresh: Use TRMNL web UI or press button on device.

---

## Alternative: Static Data Strategy

Instead of hosting data externally with GitHub Pages, you can embed data directly in the plugin using the **static** strategy. This eliminates the need for GitHub Pages.

### Configuration

In `src/settings.yml`:

```yaml
---
strategy: static
static_data: '{"greeting": "Hello", "message": "This is embedded data"}'
no_screen_padding: 'no'
dark_mode: 'no'
name: My Plugin Name
refresh_interval: 1440
```

**Key differences from polling:**
- `strategy: static` instead of `polling`
- `static_data` contains the JSON as a string (entire JSON in quotes)
- No `polling_url` needed
- No GitHub Pages setup required

### Updating Static Data

1. Edit `static_data` in `src/settings.yml`
2. Run `trmnlp push`

### When to Use Static vs Polling

| Static | Polling |
|--------|---------|
| Data and templates bundled together | Data hosted separately |
| Update requires `trmnlp push` | Update data.json, TRMNL fetches it |
| Simpler setup (no GitHub Pages) | Decoupled architecture |
| Good for: generated data via CI/CD | Good for: frequently changing external data |

---

## Template Development

Edit the `.liquid` files in `src/` to customize the display:

- `full.liquid` — Full screen (800×480)
- `half_horizontal.liquid` — Top or bottom half
- `half_vertical.liquid` — Left or right half
- `quadrant.liquid` — Quarter screen
- `shared.liquid` — Reusable components (use `{% render 'shared' %}`)

After editing templates, push to TRMNL:

```bash
docker run \
  --volume "$(pwd):/plugin" \
  --volume "$HOME/.config/trmnlp:/root/.config/trmnlp" \
  trmnl/trmnlp push
```

See the "Push changes to TRMNL" section above for non-interactive usage.

---

## Available Template Variables

In addition to your JSON data, TRMNL provides device context:

```liquid
{{ trmnl.user.name }}
{{ trmnl.user.first_name }}
{{ trmnl.user.time_zone }}
{{ trmnl.device.percent_charged }}
{{ trmnl.device.wifi_strength }}
{{ trmnl.device.width }}
{{ trmnl.device.height }}
{{ trmnl.system.timestamp_utc }}
{{ trmnl.plugin_settings.instance_name }}
{{ trmnl.plugin_settings.dark_mode }}
```
