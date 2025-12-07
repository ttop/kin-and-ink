# trmnlp Local Development Setup Guide

This guide walks through setting up the TRMNL local development environment using Docker, and creating a simple "Hello World" plugin from scratch.

---

## Table of Contents

1. [Installing Docker](#1-installing-docker)
2. [Understanding the Docker Volume Mount](#2-understanding-the-docker-volume-mount)
3. [trmnlp Quick Reference](#3-trmnlp-quick-reference)
4. [Hello World Walkthrough](#4-hello-world-walkthrough)
5. [Deploying to Real TRMNL](#5-deploying-to-real-trmnl)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Installing Docker

### macOS

**Option A: Docker Desktop (GUI)**
1. Download from https://www.docker.com/products/docker-desktop/
2. Open the `.dmg` file and drag Docker to Applications
3. Launch Docker from Applications
4. Wait for the whale icon to appear in your menu bar (indicates Docker is running)

**Option B: Homebrew**
```bash
brew install --cask docker
```
Then launch Docker.app from Applications.

### Verify Installation

```bash
docker --version
# Should output something like: Docker version 24.x.x

docker run hello-world
# Should pull and run a test container successfully
```

### Important: Docker Must Be Running

Docker Desktop must be running (whale icon in menu bar) before you can use any `docker` commands. It doesn't start automatically on boot by default.

### Pull the trmnlp Image

Once Docker Desktop is running, pull the TRMNL preview image:

```bash
docker pull trmnl/trmnlp
```

This downloads the image from Docker Hub. You'll see progress output as layers download. Once complete, verify it's available:

```bash
docker images | grep trmnl
# Should show: trmnl/trmnlp   latest   ...
```

Note: If you skip this step, Docker will automatically pull the image the first time you run a `docker run trmnl/trmnlp` command — but doing it explicitly now confirms everything is working before you're in the middle of a demo.

---

## 2. Understanding the Docker Volume Mount

When you run `trmnlp` via Docker, you need to share your local files with the container. This is done via a **volume mount**.

### The Key Command

```bash
docker run \
    --publish 4567:4567 \
    --volume "$(pwd):/plugin" \
    trmnl/trmnlp serve
```

Breaking this down:

| Flag | Purpose |
|------|---------|
| `--publish 4567:4567` | Maps container port 4567 to your localhost:4567 |
| `--volume "$(pwd):/plugin"` | Mounts your current directory into `/plugin` inside the container |
| `trmnl/trmnlp` | The official TRMNL preview Docker image |
| `serve` | The command to run the dev server |

### How File Sharing Works

```
Your Machine                    Docker Container
─────────────                   ────────────────
~/projects/my_plugin/     ←→    /plugin/
├── .trmnlp.yml                 ├── .trmnlp.yml
├── src/                        ├── src/
│   ├── full.liquid             │   ├── full.liquid
│   └── ...                     │   └── ...
```

**Changes sync both ways:**
- Edit `full.liquid` on your Mac → instantly available in container
- Container writes a file → appears in your local folder

**Hot reload:** The dev server watches for file changes. Edit a `.liquid` file in your editor, save it, and the browser preview updates automatically.

### Working Directory Matters

Always `cd` into your plugin folder before running the Docker command:

```bash
cd ~/projects/my_plugin
docker run --publish 4567:4567 --volume "$(pwd):/plugin" trmnl/trmnlp serve
```

If you run it from the wrong directory, the container won't see your plugin files.

---

## 3. trmnlp Quick Reference

### Commands

| Command | Purpose |
|---------|---------|
| `trmnlp init [name]` | Scaffold a new plugin project |
| `trmnlp serve` | Start local dev server (port 4567) |
| `trmnlp login` | Authenticate with your TRMNL account |
| `trmnlp push` | Upload plugin to TRMNL |
| `trmnlp clone [name] [id]` | Download existing plugin from TRMNL |

### Running Commands via Docker

For `init`, `login`, `push`, and `clone`, you run them the same way but swap the command:

```bash
# Initialize a new plugin
docker run --volume "$(pwd):/plugin" trmnl/trmnlp init my_plugin

# Login (will prompt for API key)
docker run -it --volume "$(pwd):/plugin" trmnl/trmnlp login

# Push to TRMNL
docker run --volume "$(pwd):/plugin" trmnl/trmnlp push
```

Note: `login` needs `-it` flag for interactive input.

### Project Structure

After `trmnlp init`, you get:

```
my_plugin/
├── .trmnlp.yml           # Local dev config (sample data, env vars)
├── bin/
│   └── dev               # Convenience script
└── src/
    ├── full.liquid           # Full-screen layout (800×480)
    ├── half_horizontal.liquid # Top/bottom half
    ├── half_vertical.liquid   # Left/right half  
    ├── quadrant.liquid        # Quarter screen
    ├── shared.liquid          # Reusable components
    └── settings.yml           # Plugin metadata
```

### Key Files

**`.trmnlp.yml`** — Configure sample data for local preview:
```yaml
variables:
  ancestor_name: "Martha Washington"
  birth_year: 1731
  death_year: 1802
```

**`src/full.liquid`** — Your main template:
```html
<div class="layout">
  <div class="title">{{ ancestor_name }}</div>
  <div class="description">{{ birth_year }} – {{ death_year }}</div>
</div>
```

---

## 4. Hello World Walkthrough

Let's create the simplest possible plugin: a polling-based display that shows "Hello World" from a JSON endpoint.

### Step 1: Create Plugin Scaffold

```bash
# Create a working directory
mkdir -p ~/trmnl-dev
cd ~/trmnl-dev

# Initialize a new plugin via Docker
docker run --volume "$(pwd):/plugin" trmnl/trmnlp init hello_world

# Enter the plugin directory
cd hello_world
```

You should now have:
```
hello_world/
├── .trmnlp.yml
├── bin/
│   └── dev
└── src/
    ├── full.liquid
    ├── half_horizontal.liquid
    ├── half_vertical.liquid
    ├── quadrant.liquid
    ├── shared.liquid
    └── settings.yml
```

### Step 2: Edit the Template

Open `src/full.liquid` in your editor and replace its contents with:

```html
<div class="view view--full">
  <div class="layout layout--col">
    <div class="columns">
      <div class="column">
        <span class="title title--large">{{ greeting }}</span>
        <span class="description">{{ message }}</span>
      </div>
    </div>
  </div>

  <div class="title_bar">
    <span class="title">Hello World Plugin</span>
    <span class="instance">Demo</span>
  </div>
</div>
```

### Step 3: Add Sample Data for Local Preview

Edit `.trmnlp.yml` to provide sample variables:

```yaml
watch:
  - src
  - .trmnlp.yml

variables:
  greeting: "Hello, World!"
  message: "This is my first TRMNL plugin."
```

### Step 4: Start the Dev Server

```bash
# Make sure you're in the hello_world directory
cd ~/trmnl-dev/hello_world

# Start the server
docker run --publish 4567:4567 --volume "$(pwd):/plugin" trmnl/trmnlp serve
```

You should see output like:
```
[2024-xx-xx] trmnlp vX.X.X
[2024-xx-xx] Listening on http://0.0.0.0:4567
[2024-xx-xx] Watching: src, .trmnlp.yml
```

### Step 5: Preview in Browser

Open http://localhost:4567 in your browser.

You should see a preview of your plugin with "Hello, World!" displayed.

**Try hot reload:** Edit `src/full.liquid`, change the text, save. The browser preview updates without refreshing.

### Step 6: Iterate

Experiment with the TRMNL Framework classes:

```html
<!-- Try different title sizes -->
<span class="title title--xlarge">Big Title</span>
<span class="title title--small">Small Title</span>

<!-- Add a label -->
<span class="label">Some Label</span>

<!-- Use the value component for numbers -->
<span class="value value--xlarge">42</span>
```

Reference the Framework docs at https://usetrmnl.com/framework for all available components.

---

## 5. Deploying to Real TRMNL

Once you're happy with your local preview, there are two paths to get it onto your actual device.

### Option A: Push via trmnlp (Recommended)

This uploads your markup directly to a Private Plugin in your TRMNL account.

```bash
# Authenticate (one-time setup)
docker run -it --volume "$(pwd):/plugin" trmnl/trmnlp login
# Enter your API key when prompted (find it in TRMNL account settings)

# Push the plugin
docker run --volume "$(pwd):/plugin" trmnl/trmnlp push
```

### Option B: Manual Copy-Paste

If you prefer, you can manually copy your markup into the TRMNL web editor:

1. **Create a Private Plugin:**
   - Log into https://usetrmnl.com
   - Go to Plugins → search "Private Plugin" → Add
   - Set Strategy to "Polling"
   - Set Polling URL to your JSON endpoint (for testing, use: `https://usetrmnl.com/custom_plugin_example_data.json`)
   - Save

2. **Edit Markup:**
   - From the plugin settings page, click "Edit Markup"
   - Select the "Full" tab
   - Paste your `full.liquid` contents
   - Click Save

3. **Test:**
   - Click "Force Refresh" to trigger a new render
   - Check the preview in the web UI
   - Your device will pick it up on its next refresh cycle

### Setting Up the Real Polling URL

For the demo to be complete, you need a real JSON endpoint. For now, you can use TRMNL's example endpoint:

```
https://usetrmnl.com/custom_plugin_example_data.json
```

This returns:
```json
{
  "text": "You can do it!",
  "author": "Rob Schneider"
}
```

Update your template to use these keys:
```html
<span class="title">{{ text }}</span>
<span class="label">— {{ author }}</span>
```

Later, you'll replace this with your GitHub Pages URL.

---

## 6. Troubleshooting

### "Cannot connect to the Docker daemon"

Docker Desktop isn't running. Launch it from Applications and wait for the whale icon.

### "Port 4567 is already in use"

Another process is using that port. Either:
- Stop the other process, or
- Use a different port: `--publish 8080:4567` then visit http://localhost:8080

### Changes not showing in preview

1. Make sure you saved the file
2. Check that you're editing the file inside the mounted directory
3. Look at the terminal — the server logs when it detects changes

### "No such file or directory" when running Docker

You're probably not in the right directory. `cd` into your plugin folder first.

### Preview looks different from actual device

The HTML preview is an approximation. For pixel-accurate rendering, the dev server can generate PNGs, but this requires Firefox and ImageMagick (easier with native Ruby install than Docker).

---

## Quick Reference: Common Workflows

### Start fresh each day
```bash
cd ~/trmnl-dev/hello_world
docker run --publish 4567:4567 --volume "$(pwd):/plugin" trmnl/trmnlp serve
```

### Create a new plugin
```bash
cd ~/trmnl-dev
docker run --volume "$(pwd):/plugin" trmnl/trmnlp init new_plugin_name
cd new_plugin_name
```

### Push changes to TRMNL
```bash
docker run --volume "$(pwd):/plugin" trmnl/trmnlp push
```

### Force refresh on device
1. Go to TRMNL web UI → your plugin settings
2. Click "Force Refresh"
3. Wait for device's next wake cycle (or press button on back of device)
