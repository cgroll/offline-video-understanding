# Proposal

## Why

The global summary (`summary.json`) was built from images alone, even though the video's own transcript often carries
information the frames cannot show on their own (a name said while filming, what is about to happen before it is
visible). Testing this on real family videos also showed the user does not want a full per-scene story for routine
use - just a fast, coarse "what is this video about". Retrospective: this proposal documents a change already
implemented and validated against real footage in this session.

## What Changes

- The global summary prompt now includes the video's own spoken transcript (chronological, with speaker labels)
  alongside the existing 40-frame storyboard and title, so a name or explanation said in speech can inform
  `characters`/`plot` even when the frames alone are ambiguous. Verified on a real children's-ski-lesson video: genre
  went from the generic "Schneelandschaft" (images only) to the specific "Skikurs für Kinder" (images + transcript).
- Fixed a generation robustness bug found while testing the above: greedy decoding with no repetition control could
  degenerate into repeating one token until the token budget ran out, leaving `summary.json` truncated mid-JSON.
  `repetition_penalty` is now applied to every VLM call (not just the summary).
- `summary.json` is now validated after being written (checked for the expected top-level keys); an incomplete or
  malformed result is still written for inspection, but with a printed warning instead of silent corruption.
- New `--summary-only` mode: generates/refreshes only `summary.json`, skipping plain captions, per-scene context
  captions, chapters and the report - all of which need or are built from per-scene descriptions this mode never
  computes. Available both as `ovu caption <project> --context --summary-only` and, now wired through,
  `ovu process <project> --vlm --summary-only`. The existing full per-scene mode (`--context` without
  `--summary-only`) is unchanged and still available for when a detailed, scene-by-scene story is wanted.
- Documented in `README.md` how another project can call this (as an external CLI tool, not a Python dependency) to
  get a quick "what is this video about" for one video file.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `scene-descriptions`: the global summary step now also takes the transcript as input, is validated after
  generation, and can run standalone without the per-scene steps.
- `pipeline-cli`: `ovu process --vlm` gains `--summary-only`, which changes what `--vlm` runs.

## Impact

- `src/ovu/caption.py`: `SUMMARY_PROMPT` extended; new `transcript_block()`; `summarize()` takes a `transcript`
  argument; `run()` gains `summary_only`; new `MIN_SUMMARY_FIELDS` validation.
- `src/ovu/vlm.py`: `generate()` gains `repetition_penalty` (default 1.15), applied to all callers.
- `src/ovu/cli.py`: `caption` subcommand gains `--summary-only`; `process` subcommand gains `--summary-only` and
  routes it through to `caption.run()`, skipping plain captions, chapters and the report when set.
- `README.md`: new usage section for calling this from another project/process.
- No schema change to `summary.json` itself (same fields); no change to `captions.json`/`captions_ctx.json`'s own
  format, generation logic or the chapters/report pipeline.
