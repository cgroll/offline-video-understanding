# AGENTS.md

Context for coding agents. Read [README.md](README.md) (usage) and [PROJECT.md](PROJECT.md) (pipeline, models,
GUI) first; behaviour is specified in `openspec/specs/<capability>/spec.md`.

## Map

| Path | What |
|---|---|
| `src/ovu/cli.py` | `ovu` command; `process` orchestrates all steps |
| `src/ovu/paths.py` | layout: `data/videos/`, `data/processed/<slug>/`, `eval/<slug>.json`; `resolve_video` |
| `src/ovu/media.py` | ffmpeg: audio, 1 fps frames, hard cuts, thumbnails |
| `src/ovu/segments.py` | windows, content segments (`shots`), `spans`, `to_seconds` (unit → per-second scores) |
| `src/ovu/embedder.py`, `vlm.py` | model loading: EmbeddingGemma 2, Qwen3-VL-4B (4-bit); `vlm.generate` |
| `src/ovu/transcribe.py`, `embed.py`, `caption.py`, `chapters.py` | pipeline steps, each with `run(video, ..., force)` |
| `src/ovu/language.py` | output language (user > `meta.json` > transcript > title > English) |
| `src/ovu/search.py` | per-second scoring, fusion, peaks, `ovu search`, `ovu eval` |
| `src/ovu/app/` | GUI: `server.py` (FastAPI) + `index.html` (vanilla JS, canvas timeline) |
| `openspec/` | `config.yaml` (constraints), `specs/` (current behaviour), `changes/` (proposals) |
| `eval/` | eval sets per video (git-ignored; format in `eval/README.md`) |

Result files per video: `transcript.json`, `meta.json`, `embeddings.npz` (all variants plus `starts/ends`,
`shot_starts/shot_ends`, `chapter_starts/chapter_ends`, `scene_cuts`), `captions.json`, `summary.json`,
`captions_ctx.json`, `chapters.json`, `thumbs/`.

## Rules

- **Local models only** at inference time. Target: 8 GB VRAM. The GUI server holds ~1-2 GB, the VLM up to ~4.5 GB;
  check `nvidia-smi` before GPU jobs.
- **Generic prompts.** Never put names, genres, examples or other knowledge about a specific video into pipeline
  prompts, even if you have seen the video. The title from the file name is the only allowed metadata. Grep prompts
  for video-specific words before VLM runs. Eval queries are for evaluation only.
- **Language.** Code, specs, docs, prompts and JSON keys are English; generated texts follow the per-video output
  language; the transcript is never translated.
- **Never commit** videos, `data/`, eval sets or anything else describing video content.
- **Specs first** for features: create an OpenSpec change (`/opsx:propose`), implement (`/opsx:apply`), archive
  (`/opsx:archive`). Keep `openspec validate --specs --strict` green.
- **Measure** retrieval changes with `uv run ovu eval <slug>` and compare with the current best variant; eval sets are
  small and written after watching the videos, so 1-2 query differences are tendencies, not results.
- Steps must stay resumable (skip finished work, `--force` recomputes). Long runs (scene descriptions ~7 s per
  segment) go to the background with a log file.
- Style: small modules, `run()` entry points, heavy imports (torch, transformers) inside functions so the CLI starts
  fast, lines ≤ 120 characters, comments only where the code is not obvious.

## Commands

```bash
uv sync
uv run ovu list
uv run ovu process <url|video> [--no-vlm] [--language de] [--force]
uv run ovu eval <video>
uv run ovu app <video> --port 7860
openspec validate --specs --strict
```
