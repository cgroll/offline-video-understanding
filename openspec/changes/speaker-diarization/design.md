# Design

## Context

`src/ovu/transcribe.py::run()` currently does one pass: `load_audio()` (ffmpeg -> in-memory float32 16 kHz mono
array) feeds Parakeet (`onnx_asr`, CPU) with VAD, producing `segments`/`words`. `conversation-transcriptor` already
has a proven diarization path (`convscript/model_sortformer.py`, `convscript/conversation_transcription.py`) built
for a different use case (standalone conversation recordings) - this design reuses its model choice and
overlap-matching logic, adapted to run inside `ovu transcribe` and to never block on failure. See proposal.md for
why and what; specs for the exact behaviour contract.

## Goals / Non-Goals

**Goals:**
- Reuse the proven Sortformer integration, not re-derive a diarization approach.
- Keep `ovu transcribe` a single step with one resumable output file, consistent with every other step in the
  pipeline.
- Never let diarization failure (model error, no GPU, video with no distinguishable speakers) stop transcription -
  speech-to-text is the more important half of this step and must still complete.

**Non-Goals:**
- Speaker *identification* (naming `SPEAKER_00` as "Mum"). Out of scope - `SPEAKER_NN` labels are stable within one
  video only, consistent with Sortformer's own guarantee (streaming speaker cache keeps labels consistent start to
  end of one file), not across videos.
- Changing VAD segment boundaries to align with speaker turns. Segments stay exactly as Parakeet+Silero produce
  them today; only a `speaker` field is added per segment.
- A dedicated eval-set metric for diarization accuracy. Judged manually on the 3 test videos per proposal.md.

## Decisions

- **Diarization runs inside `transcribe.run()`, after Parakeet, same output file.** Alternative considered: a
  separate `ovu diarize` step writing a second file (`speakers.json`) that other steps join against. Rejected:
  `transcript.json` is already the one place every downstream step (GUI, search, captions) reads text and timing
  from; a second file would need its own resumability handling and its own join logic wherever segments are read,
  for a feature that only ever makes sense together with the transcript.
- **Sortformer needs a WAV file path (per `conversation-transcriptor`'s working `model.diarize(audio=[str(fname)])`
  call), but `ovu`'s audio pipeline only ever holds audio as an in-memory array (`media.load_audio`).** Decision:
  extract a second, temporary 16 kHz mono WAV with ffmpeg (same filter args as `load_audio`, just `-f wav` instead
  of raw float32 to stdout, written to a `tempfile.NamedTemporaryFile`) solely for the Sortformer call, deleted
  immediately after. Alternative considered: change `load_audio` to always write a cached WAV next to
  `transcript.json` - rejected, that would be a permanent new project file for a need that is otherwise transient
  (not used by Parakeet, which takes the in-memory array).
- **Model lifecycle: load, diarize, `del model; torch.cuda.empty_cache()`, same as `conversation-transcriptor`.**
  This is the existing, proven pattern and keeps the step's peak VRAM transient - Sortformer is never resident
  alongside the VLM (loaded later, and only with `--vlm`) or anything the GUI holds.
- **Overlap-based speaker assignment reuses `conversation-transcriptor`'s logic** (largest-time-overlap match per
  ASR segment; a segment with no overlapping diarized interval gets `speaker = null`), ported as plain Python over
  lists/dicts rather than `conversation-transcriptor`'s `pandas`-DataFrame implementation - `ovu` does depend on
  `pandas` already (for other steps), but a per-video segment/interval list is small enough that plain loops are
  simpler here and avoid a DataFrame round-trip for no benefit.
- **Diarization failure degrades gracefully.** If Sortformer errors (no CUDA, model download fails, unsupported
  audio), `transcribe.run()` SHALL catch it, log a warning, and write `transcript.json` with every `speaker` set to
  `null` rather than failing the whole step. Rationale: matches the project's general resumability/robustness
  stance (`ovu ingest` steps already degrade individual item failures to an error marker rather than aborting) and
  keeps transcription - the more critical output - available even on a machine without a working GPU.
- **GUI rendering**: add a small speaker badge (same visual pattern as the existing scene-description `shot_type`
  badge in `index.html::renderSegs()`) in front of the transcript line when `s.speaker` is present; no badge when
  `null`.

## Risks / Trade-offs

- [NeMo is a heavy dependency (large transitive install, long first import) added just for one model] → accepted,
  it is already a proven, working dependency in `conversation-transcriptor` on the same machine; no lighter
  alternative diarization model was evaluated, matching the proposal's "reuse, not research" framing.
- [Sortformer's 4-speaker cap silently relabels a 5th voice onto an existing label] → documented behaviour (spec
  scenario "More than four distinct voices"), not silently hidden; acceptable because most home videos have very
  few people talking at once.
- [A temporary WAV file per `transcribe` run adds disk I/O and a small amount of extra runtime] → negligible next to
  model inference time; always cleaned up even on error (`try`/`finally`).
- [Diarization errors could mask a real GPU problem as "no speakers found"] → the warning is logged (printed), not
  swallowed silently, so it is visible in the run's console output / log file for long background runs.

## Migration Plan

Additive, backward compatible: existing `transcript.json` files from before this change simply lack `speaker` keys.
Every reader (GUI, future steps) SHALL treat a missing `speaker` the same as `speaker: null` - no forced
re-transcription. Re-running `ovu transcribe --force` on an old project adds speaker labels going forward; nothing
breaks if a project is never re-run.

## Open Questions

- Exact wall-clock overhead of Sortformer on a short (seconds-to-few-minutes) home video is unmeasured - to be
  recorded from the 3 test-video run per proposal.md; does not change the design or task breakdown, only informs
  whether diarization should ever become optional/flagged for very long videos later.
