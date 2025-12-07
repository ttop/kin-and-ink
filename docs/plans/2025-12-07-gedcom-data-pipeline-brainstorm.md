# GEDCOM Data Pipeline Brainstorm

**Date:** 2025-12-07
**Status:** In Progress - paused mid-brainstorm

## Problem Statement

The TRMNL genealogy plugin currently uses static data. We want to build a system that:
1. Allows non-technical users to use their own GEDCOM genealogy files
2. Generates the JSON format the plugin consumes
3. Rotates through different families over time
4. Costs little to nothing to run
5. Respects user privacy (genealogy data is sensitive)

## Key Decisions Made

### Architecture: GitHub-based, user-owned
- User forks a template repository
- All processing happens in their own GitHub account
- GitHub Pages serves the data
- User owns and controls their data (privacy concern addressed)

### User flow (all browser-based, no CLI needed)
1. User forks template repo on GitHub
2. Uploads GEDCOM file via GitHub's web UI (drag and drop)
3. GitHub Action triggers, processes GEDCOM into JSON families
4. Scheduled Action (daily) rotates which family is "current"
5. GitHub Pages serves `current.json` at a stable URL
6. User copies that URL into TRMNL plugin settings

### Rotation mechanism
- **Approach:** Overwrite `current.json` with next family's data, commit it
- **Frequency:** Once every 24 hours (user-adjustable)
- **Tradeoff:** Creates ~365 commits/year of rotation noise, but simple and harmless

### Known limitation (accepted)
- GitHub Actions pauses scheduled workflows after 60 days of repo inactivity
- User needs to occasionally make a commit or manually trigger the action
- This is acceptable and will be documented

## Open Questions (where we paused)

### How to select which families to include from GEDCOM?

Options discussed:
- A) **All families** - Extract every family unit, full rotation through entire tree
- B) **Direct lineage only** - User specifies "root person", extract only ancestors/descendants
- C) **User-curated** - Generate all, user edits config to pick which to include
- D) **Smart default + override** - Include families with "complete" data, user can adjust

**No decision made yet** - need to resume discussion.

### Future questions to address
- GEDCOM parsing library/approach (JavaScript for Actions?)
- Mapping GEDCOM fields to plugin's JSON schema (first_name, last_name, birth, death, etc.)
- Handling incomplete data (missing dates, missing spouses, etc.)
- How to specify the "subject" vs "spouse" in each family unit
- Children extraction and the `child: true` flag logic
- Error handling for malformed GEDCOM files
- User documentation/guide for the fork-and-configure flow

## Alternatives Considered (and rejected)

### Client-side JavaScript only
- **Why rejected:** TRMNL polls URLs and receives raw HTML/JS - JavaScript doesn't execute. Need server-side selection.

### Cloudflare Workers + R2
- **Pros:** Generous free tier, simple deployment, handles upload/processing/serving
- **Why not chosen:** Privacy concerns with hosting user's genealogy data

### S3 + Lambda
- **Why rejected:** Too much operational complexity (API Gateway, IAM, CORS, deployment) for a fun side project

### Central hosted service
- **Why rejected:** Privacy liability, user trust issues with sensitive genealogy data

## Plugin Data Format Reference

From `.trmnlp.yml`:

```yaml
subject/spouse:
  first_name, last_name, birth, death, photo_url

subject_parents/spouse_parents:
  father: {first_name, last_name, birth, death}
  mother: {first_name, last_name, birth, death}

children: (array of couples)
  - first:
      first_name, last_name, birth, death
      child: true  # marks actual child of subject/spouse
    second:        # optional spouse
      first_name, last_name, birth, death
```

## Next Steps (when resuming)

1. Decide on family selection approach (A/B/C/D above)
2. Research GEDCOM parsing options for GitHub Actions
3. Design the JSON output structure (array of families)
4. Sketch the Action workflow files
5. Consider user configuration options (rotation frequency, family filters)
6. Write up user-facing documentation outline
