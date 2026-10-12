## Context

Chapters (`chapters.json`) come from the text-only VLM step and have start/end seconds snapped to segment
boundaries. `embeddings.npz` holds one `frame` vector per second and one `chapter` vector per chapter (title +
summary as text), both in the same EmbeddingGemma 2 space.

## Goals / Non-Goals

**Goals:** a readable PDF per project, generated offline in seconds, without loading any model.

**Non-Goals:** editing chapters, HTML export, choosing several frames per chapter, re-ranking chapters.

## Decisions

- **Frame choice by cross-modal similarity** (frame vector · chapter text vector) instead of the visual medoid of the
  chapter: the picture should show what the summary talks about, not just the most common look of the chapter.
  Near-uniform frames (grey-level std < 12 at 640x360, same rule as the empty-scene check in captioning) are
  excluded. Fallback: middle second. If the `chapter` embedding is missing, the medoid of the chapter's frame vectors
  is used.
- **Frame extraction** with `ffmpeg -ss <t+0.5> -frames:v 1`, scaled to 1280 px width (no upscaling), JPEG in a
  temporary directory; the PDF embeds the images.
- **reportlab** (pure Python, no system libraries) over HTML-to-PDF tools that need WeasyPrint/Chromium. A4 portrait,
  title page, then two chapter entries per page (frame at text width, 16:9).
- **Font**: DejaVu Sans if installed (full Unicode), else Helvetica (Latin-1 only).
- **Labels**: a small dict per language (`en`, `de`), English fallback.
- **Freshness**: `ovu process` regenerates the report when `chapters.json` is newer than `report.pdf`; the language
  switch already deletes reports.

## Risks / Trade-offs

- [The chapter text embedding may favour title cards or text-heavy frames] → excluded uniform frames; check visually
  on both projects; switch to a mix with the medoid if needed.
- [Chapter summaries can contain VLM errors] → the report shows them as generated; it is a view of the pipeline
  output, not a curated document.
- [Fonts missing on other systems] → Helvetica fallback keeps the report working for Latin-1 languages.
