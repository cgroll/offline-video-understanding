# Design

## Context

See proposal.md for why and what. This was built and tested interactively against real footage rather than planned
upfront, so this document also records what was tried and rejected along the way, not just the final shape.

## Goals / Non-Goals

**Goals:**
- A fast, standalone way to get `summary.json` for a video, usable from another project via the CLI alone.
- Keep the existing full per-scene mode exactly as it was, for when it is actually wanted.

**Non-Goals:**
- Fixing the vision-language model's mirror/reflection blind spot (see Risks) - documented, not addressed here.
- A Python API between this project and callers - the interface is the CLI and the JSON files it writes, not an
  importable module (see Decisions).
- Feeding the transcript into the per-scene context captions (`describe_ctx`) - only the global summary uses it for
  now; per-scene use was not requested and not tried.

## Decisions

- **Transcript as additional prompt input, not a separate pipeline stage.** Alternative considered: a dedicated
  "merge transcript + vision" step producing its own intermediate file. Rejected as unnecessary complexity - the
  transcript is short enough (a few minutes of speech, at most a few hundred lines) to include directly in the
  summary prompt alongside the storyboard, with no separate processing needed. `transcript_block()` is a small,
  reusable formatting helper, not a new pipeline stage.
- **`repetition_penalty = 1.15`, found by direct experiment, not literature defaults.** Tried 1.3 first (a common
  "safe" value) - it stopped the repetition loop but then caused the model to end generation early, omitting
  required JSON fields (`plot` was missing entirely). 1.15 fixed the loop and produced complete, schema-valid JSON
  on repeated real runs. Applied to all `generate()` calls (not just the summary's), since the same degenerate-loop
  risk exists wherever a long/complex prompt could occur, not only here.
- **Validation is a warning, not a hard failure.** `summarize()`'s output is still written to `summary.json` even
  when it fails the `MIN_SUMMARY_FIELDS` check, so a broken result is visible and inspectable (matching how the rest
  of this project favours visible degradation over a hard stop - see `transcribe.py`'s existing error handling
  style) rather than losing the attempt entirely or crashing the whole `--vlm` run over one bad generation.
- **`summary_only` is a branch inside `caption.run()`, not a separate function or CLI subcommand.** It shares
  `summarize()`/`transcript_block()`/the validation logic with the full-context path, and reuses the existing
  `caption` subcommand's `--context` flag plus a new `--summary-only` flag rather than inventing a new verb,
  consistent with how other steps already compose (e.g. `caption --context` itself is a variant of plain `caption`).
- **Resumability bug caught before being relied on**: an early version of `summary_only` always regenerated
  `summary.json`, ignoring `force`. Caught while re-testing (second video showed `summary in Xs` instead of the
  expected "already done" skip message) and fixed to check `spath.exists()` like every other step in this project
  (`AGENTS.md`: "Steps must stay resumable").
- **No Python-level API for other projects.** `offline-video-understanding` and `family-media` are independent
  repos by design (see `family-media`'s own decisions log: "kept to three components on purpose"); the integration
  surface documented in `README.md` is the CLI plus reading `summary.json` directly, not an importable function.
  This matches how `ovu` is already used (a standalone tool with project directories under `data/projects/`), and
  avoids coupling two repos' Python environments together for one JSON file.

## Risks / Trade-offs

- [Mirror/reflection scenes get misread as two people] → Not fixed here (see proposal.md point 4); documented as a
  known limitation. Mitigation would need either a different prompt hint or a different model, neither tried.
- [`ovu new` copies the video file into `data/projects/<name>/`] → A caller with stricter original-file rules (e.g.
  `family-media`'s "never duplicate without hash verification") should be aware this is a plain filesystem copy with
  no verification step of its own; noted in the README usage section, not solved here (out of scope for this repo).
- [Transcript errors (bad diarization, misheard words) feed into the summary as if correct] → No new risk introduced
  by this change specifically; the transcript was already used elsewhere (search, captions) with the same trust
  level. The summary prompt does tell the model that speaker labels may be wrong for short lines.
- [`repetition_penalty` tuned against a small number of real examples, not a systematic sweep] → 1.15 worked on
  every real test run in this session (3 family videos, repeated regenerations); a more adversarial or much longer
  transcript could still find a value that breaks differently. Revisit if a future run produces an invalid/warned
  summary again.

## Migration Plan

Additive and backward compatible. Existing `summary.json` files from before this change are untouched unless
regenerated with `--force`; the per-scene full-context path is unchanged for existing or new projects that do not
pass `--summary-only`. No schema change to any output file.
