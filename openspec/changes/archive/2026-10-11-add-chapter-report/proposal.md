## Why

The pipeline produces chapters and summaries, but they are only visible in the GUI or as JSON. A shareable document
that tells the video chapter by chapter, with one picture and timestamps each, makes the result usable without
running the app and shows at a glance how good the local understanding is.

## What Changes

- New command `ovu report <project>` creates `report.pdf` in the project: a title page with the overall summary,
  then one entry per content chapter (the chapters from `chapters.json`, not pixel/embedding segments) with chapter
  number, start–end timestamps, title, one representative frame and the chapter summary.
- The representative frame of a chapter is chosen locally from the existing embeddings: the non-empty frame inside
  the chapter that best matches the chapter's text (title + summary).
- Fixed labels in the PDF follow the project's output language (German and English provided, others fall back to
  English); generated texts already are in that language.
- `ovu process` creates the report as its last step.

## Capabilities

### New Capabilities
- `chapter-report`: PDF document of a processed project, one representative frame, timestamps and summary per
  chapter

### Modified Capabilities
- `pipeline-cli`: `report` subcommand; `process` ends with the report
- `chapters`: two-pass chaptering (starts first, then one summary per chapter), minimum chapter length, salvaging
  truncated answers and failing instead of summarizing when no chapter was produced. The first German run on a
  13-minute test video produced a chapter for almost every segment; the answer was cut off and no chapter survived.

## Impact

- New module `report.py`, new dependency `reportlab` (pure Python PDF); uses a Unicode TTF font (DejaVu Sans) when
  installed.
- Uses existing `frame` and `chapter` embeddings and ffmpeg; no model is loaded, no VRAM needed, a few seconds per
  report.
- No effect on eval metrics (output only). Report quality is checked by reading the generated PDF.
- Depends on `add-video-projects` (project directory, `project.json` language).
