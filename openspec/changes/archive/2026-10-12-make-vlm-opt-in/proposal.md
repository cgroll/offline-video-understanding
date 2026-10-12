## Why

The VLM steps (scene descriptions, chapters, report) take most of the runtime (~40 min for a 13-minute video vs.
~10 min for everything else), need the largest model download (~9 GB) and the most VRAM, and their texts are still
error-prone for story-level understanding. Search over transcript and visual embeddings works without them, so they
should not run unless asked for.

## What Changes

- **BREAKING**: `ovu process <project>` runs only transcription and the embeddings that need no VLM output
  (`frame`, `video_shots`, window variants). Scene descriptions, chapters, their embeddings and the report run only
  with the new flag `--vlm`; `--no-vlm` is removed.
- `--language` without `--vlm` only stores the output language for later VLM runs.
- The single VLM steps (`ovu caption`, `ovu chapters`, `ovu report`) stay available and unchanged.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `pipeline-cli`: VLM steps in `ovu process` become opt-in via `--vlm`

## Impact

- `cli.py`, README / PROJECT.md / AGENTS.md usage examples.
- Default runtime of `ovu process` drops to transcription + embeddings (~10 min for 13 min of video); no Qwen3-VL
  download needed for the default path. No VRAM above EmbeddingGemma 2 (~2 GB) by default.
- Eval metrics unchanged; variants that need VLM output (`caption`, `caption_ctx`, `chapter`) are simply absent unless
  `--vlm` was used, and search/GUI defaults already fall back to `text+frame` / `frame`.
