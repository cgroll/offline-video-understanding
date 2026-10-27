# Tasks

Retrospective: implemented and tested interactively before this document was written. Each task is checked off with
the evidence from that testing, not re-run for this write-up.

## 1. Transcript-aware summary

- [x] 1.1 Add `transcript_block(video)` to `caption.py` (chronological `[start-end s] SPEAKER_NN: text` lines from
      `transcribe.load_transcript()`, or a "(no speech detected)" placeholder) and extend `SUMMARY_PROMPT` /
      `summarize()` to take it as an input alongside the storyboard and title. Verified: real run on `family-test-3`
      (children's ski lesson) - genre changed from "Schneelandschaft" (images-only baseline) to "Skikurs für Kinder"
      (images + transcript), characters correctly identified as a child group plus accompanying adults.
- [x] 1.2 Add `MIN_SUMMARY_FIELDS` validation after writing `summary.json`: print a warning (not an error) if the
      parsed JSON is missing an expected top-level key. Verified: triggered for real on a malformed response during
      testing (see 2.1), printed the warning and still wrote the file.

## 2. Repetition-safety fix

- [x] 2.1 Diagnose and fix: `vlm.py::generate()` had no repetition control, so a longer prompt (summary + transcript)
      could make the model repeat one token until `max_new_tokens` cut it off mid-JSON. Verified: reproduced for
      real (700 tokens of "Schneeschuhe", unterminated JSON string), fixed by adding `repetition_penalty` to
      `model.generate()`.
- [x] 2.2 Tune the penalty value against real output, not a literature default. Verified: 1.3 stopped the repetition
      loop but caused early termination (missing the `plot` field); 1.15 produced complete, valid JSON on repeated
      real regenerations of the same video. Applied as the new default for every `generate()` call.

## 3. Summary-only mode

- [x] 3.1 Add `summary_only: bool = False` to `caption.run()`: when set, writes/validates `summary.json` only and
      returns, without loading full per-segment frames, touching `captions_ctx.json`, or looping over segments.
      Verified: `ovu caption <project> --context --summary-only` run on two real videos (`family-test-1`,
      `family-test-2`), both produced valid JSON with no per-scene files created.
- [x] 3.2 Make `summary_only` resumable like every other step (skip if `summary.json` exists unless `--force`).
      Verified: an earlier version always regenerated regardless of `force`; caught during re-testing (unexpected
      regeneration instead of an "already done" message), fixed, re-verified with a skip message on a repeat call.
- [x] 3.3 Wire `--summary-only` into the CLI: `caption` subcommand (direct) and `process` subcommand (`--vlm
      --summary-only` skips plain captions, context captions, chapters and the report). Verified: single command
      `ovu process <new-project> --vlm --summary-only --language de` run end-to-end on a freshly created project
      from a real, previously untouched video - produced `transcript.json`, `embeddings.npz`, `summary.json` only;
      no `captions.json`, `captions_ctx.json`, `chapters.json` or `report.pdf` created; no errors.

## 4. Documentation

- [x] 4.1 Document the known mirror/reflection limitation (real example: `family-test-2`, a baby in front of a
      mirror, mis-described as "two children playing" both before and after this change) in design.md's risks -
      not something this change fixes.
- [x] 4.2 Add a usage section to `README.md` for calling this from another project as an external CLI tool: `ovu new
      <name> <video-path>` (note: copies the video file), `ovu process <name> --vlm --summary-only --language de`,
      then read `data/projects/<name>/summary.json` (fields: `genre`, `characters: [{name, appearance}]`,
      `objects: [string]`, `places: [string]`, `plot`). Verify: the documented command sequence matches exactly what
      was run in 3.3's end-to-end verification.

## Workflow follow-up

- Archive this change once the README usage section (4.2) is written and the user has had a chance to read it.
