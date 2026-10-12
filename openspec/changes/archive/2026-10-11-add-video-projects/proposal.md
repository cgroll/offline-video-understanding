## Why

Results of a video are spread over `data/videos/`, `data/processed/<slug>/` and `eval/<slug>.json`, named after long
file-name slugs. Working with several videos (and reports, eval sets, language choices per video) needs one
self-contained, nameable unit per video.

## What Changes

- **BREAKING**: storage layout becomes one directory per video project: `data/projects/<name>/` holds the video
  file, `project.json` (title, video file, output language), all results, the eval set (`eval.json`) and reports.
  `data/videos/`, `data/processed/` and `eval/<slug>.json` are no longer used.
- New command `ovu new <name> <file-or-url>`: creates a project and copies (or downloads) the video into it.
- All commands take a project name (or unique prefix/substring) instead of a video path or slug.
- The output language is stored in `project.json`; setting a different language explicitly invalidates the generated
  texts of that project (descriptions, summary, chapters, their embeddings and reports) so they are regenerated.
- `ovu process` takes a project name; downloading moves to `ovu new`.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `video-library`: storage layout, video references, project creation, download target
- `output-language`: language stored per project; changing it invalidates generated texts
- `pipeline-cli`: `new` command, `process` and `list` work on projects
- `search-evaluation`: eval set read from the project directory

## Impact

- Code: `paths.py` (project resolution), `cli.py`, `download.py`, `language.py`, docs (README, PROJECT, AGENTS).
- Existing local results are moved by hand into the two new projects; no automatic migration.
- No effect on eval metrics (layout only); no VRAM/runtime impact.
