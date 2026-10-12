## 1. Report

- [x] 1.1 add dependency `reportlab`
- [x] 1.2 `report.py`: load project, chapters, embeddings; representative second per chapter (similarity to the
  chapter text embedding, uniform frames excluded, middle fallback, medoid if no chapter embedding)
- [x] 1.3 extract frames with ffmpeg (≥ 1280 px width, no upscaling)
- [x] 1.4 build the PDF: title page (title, duration, language, plot, characters, themes), one entry per chapter
  (number, `m:ss–m:ss`, title, frame, summary); DejaVu Sans with Helvetica fallback; labels for en/de
- [x] 1.5 skip an existing report unless `--force` or `chapters.json` is newer

## 1b. Chapters

- [x] 1b.1 two passes: chapter starts + short titles, then title + summary per chapter from its descriptions
- [x] 1b.2 merge chapters shorter than 20 s, at most 20; salvage complete entries from truncated answers
- [x] 1b.4 split chapters longer than max(120 s, 1/8 of the video) by a second pass over their own descriptions
- [x] 1b.3 fail without writing anything when no chapter was produced; report refuses empty chapters

## 2. CLI and docs

- [x] 2.1 `ovu report <project> [--force]`; `ovu process` runs the report last (not with `--no-vlm`)
- [x] 2.2 README, PROJECT.md, AGENTS.md: report step and output

## 3. Check

- [x] 3.1 run the pipeline for a test video without speech with `--language de` and create the report
- [x] 3.2 read the PDF: chapters by content, correct timestamps, frames fit the summaries, umlauts render
