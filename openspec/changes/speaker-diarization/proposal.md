# Proposal

## Why

Most home/family videos have several people talking. `transcript.json` currently has no notion of who said what, so
the transcript panel and the transcript text itself read as one undifferentiated stream - useful for finding *that*
something was said, not *who* said it. A working reference implementation already exists in the sibling project
`conversation-transcriptor` (NVIDIA Sortformer diarization + overlap-based matching to ASR segments), so this is
reuse, not research.

## What Changes

- `ovu transcribe` additionally runs speaker diarization (NVIDIA Sortformer, `diar_streaming_sortformer_4spk-v2.1`,
  via NeMo, GPU) on the audio track, after Parakeet, within the same step.
- Each entry in `transcript.json`'s `segments` gets a `speaker` field (`"SPEAKER_00"`..`"SPEAKER_03"`, or `null` if
  diarization found no matching speaker interval for that segment), assigned by largest time overlap between the
  ASR segment and a diarization interval. Consecutive segments from the same speaker are left as separate entries
  (word timestamps already carry the finer-grained time detail; merging would lose segment boundaries other steps
  rely on).
- Sortformer supports at most 4 concurrent speakers; a 5th or later distinct voice is folded into one of the 4
  labels (whichever overlaps most) rather than erroring. Documented as a known limitation.
- The GUI's transcript panel shows the speaker label next to each spoken line when present.
- Sortformer is loaded and freed (`del model; torch.cuda.empty_cache()`) inside the transcribe step, the same
  pattern `conversation-transcriptor` already uses, so it is never resident at the same time as the VLM (Qwen3-VL,
  loaded later in `ovu process --vlm`). Parakeet stays on CPU, so it is unaffected.

**Effect on eval metrics**: none expected and none measured by `ovu eval`. Diarization adds a label to existing
transcript segments; it does not change any embedding, search variant or score. Quality for this change is judged
by manually checking speaker assignment against 3 test videos with multiple speakers (listening + reading the
labelled transcript), not by Hit@1/Hit@3/MRR.

**VRAM/runtime impact**: Sortformer adds a third GPU model used only during `ovu transcribe`, loaded and freed
before the step returns - peak VRAM during transcribe increases (Sortformer's footprint, freed immediately after),
but steady-state use is unchanged since it never overlaps with the VLM's ~4.5 GB or the GUI's ~1-2 GB. Runtime:
diarization adds one more full pass over the audio, in addition to Parakeet's; exact wall-clock cost to be measured
on the 3 test videos (not yet benchmarked - no comparable "offline streaming Sortformer on a short home video"
numbers available from `conversation-transcriptor`, which was built for longer conversation recordings).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `transcription`: `transcript.json` segments gain a `speaker` field; diarization runs as part of `ovu transcribe`.
- `search-gui`: the transcript panel (Text panels requirement) displays the speaker label per spoken line when
  present.

## Impact

- `src/ovu/transcribe.py`: add a diarization pass and overlap-based speaker assignment; `run()`'s output schema
  changes (additive field, backward compatible for older `transcript.json` files, which simply have no `speaker`
  key - treated as "unknown speaker" everywhere downstream).
- `pyproject.toml`: new dependency on NeMo's ASR collection (`nemo_toolkit[asr]` or equivalent) for
  `SortformerEncLabelModel`, matching `conversation-transcriptor`'s dependency.
- `src/ovu/app/server.py` / `index.html`: no new endpoint needed (speaker already travels inside `segments`); the
  transcript list rendering gains a per-line speaker badge.
- No change to `embed.py`, `caption.py`, `chapters.py`, `search.py` or the catalog/report pipeline - they keep
  reading `segments[].text`/`start`/`end` exactly as before.
