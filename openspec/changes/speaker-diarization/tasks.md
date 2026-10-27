# Tasks

## 1. Dependency and diarization wrapper

- [x] 1.1 Add the NeMo ASR dependency needed for `SortformerEncLabelModel` to `pyproject.toml` (matching
      `conversation-transcriptor`'s working dependency pin) and verify `uv sync` succeeds and
      `python -c "from nemo.collections.asr.models import SortformerEncLabelModel"` imports without error.
- [x] 1.2 Add `diarize(wav_path) -> list[dict]` to `src/ovu/transcribe.py` (or a small new `src/ovu/diarize.py` if it
      keeps `transcribe.py` readable): loads Sortformer with the same streaming-module parameters as
      `conversation-transcriptor/convscript/model_sortformer.py`, runs `model.diarize(audio=[wav_path], batch_size=1)`,
      returns `[{start, end, speaker}]` with `speaker` as `"SPEAKER_00".."SPEAKER_03"`, frees the model
      (`del model; torch.cuda.empty_cache()`). Heavy imports (`torch`, `nemo`) inside the function, per project
      style. Verify: run it directly against one short local WAV (e.g. extracted from a test video) and print the
      returned intervals - they should cover most of the file's speech duration.
- [x] 1.3 Add `assign_speakers(segments, intervals) -> None` (mutates `segments` in place or returns a new list):
      for each ASR segment, find the diarized interval with the largest overlap and set `speaker` to its label, or
      `None` if no interval overlaps at all. Verify with a few hand-written small cases (e.g. in a `__main__` smoke
      check or a short inline test): two non-overlapping speaker intervals correctly split two segments; a segment
      with no overlapping interval gets `None`.

## 2. Wire into the transcribe step

- [x] 2.1 In `transcribe.run()`, after the Parakeet pass, extract a temporary 16 kHz mono WAV (ffmpeg, same filter
      args as `media.load_audio` but `-f wav` to a `tempfile.NamedTemporaryFile`), call `diarize()` on it inside a
      `try`/`finally` that always deletes the temp file, then call `assign_speakers()` on the ASR segments before
      writing `transcript.json`. Verify: `uv run ovu transcribe <project> --force` on a video with two speakers
      produces a `transcript.json` whose segments carry two distinct `speaker` values.
- [x] 2.2 Wrap the diarization call (temp-WAV extraction through `assign_speakers`) in a `try`/`except` that logs a
      warning and leaves every segment's `speaker` as `None` on failure, so a missing GPU or a model-load error
      never stops the step from writing the transcript. Verify: temporarily force an exception (e.g. an invalid
      model name) and confirm `transcript.json` is still written, with `speaker: null` everywhere and a warning
      printed.
- [x] 2.3 Confirm `transcript.json` from a video with no speech still gets a `speaker` key (`null`) on its (few or
      zero) segments, and that an old, pre-existing `transcript.json` without any `speaker` keys still loads and
      displays correctly everywhere that reads it (GUI, search, captions) - verify by running the GUI against one
      previously-processed project (`the-kite`, `tagesschau` or `arte-flat-earth`) without re-running transcribe.

## 3. GUI display

- [x] 3.1 In `src/ovu/app/index.html::renderSegs()`, add a speaker badge (same visual pattern as the existing
      scene-description `shot_type` badge) in front of the transcript line's text when `s.speaker` is present;
      render nothing extra when it is `null`/absent. Verify: open `uv run ovu app <project>` on a multi-speaker test
      video and visually confirm each transcript line shows its speaker.

## 4. Validate on real test videos

- [ ] 4.1 Run the full pipeline (`uv run ovu process <project> --force`, no `--vlm` needed for this check) on the 3
      family test videos agreed with the user, each containing multiple speakers. Verify: for each, manually listen
      to the audio alongside the labelled transcript (GUI transcript tab) and judge whether speaker labels switch
      at the right moments and stay consistent for the same person throughout - record the outcome (good /
      acceptable / poor, with examples of any mislabelling) in a short note for the project's own decisions log, per
      proposal.md's "judged manually" eval approach.
- [x] 4.2 Record the actual wall-clock overhead of the diarization pass on these 3 videos (step 4.1's run already
      prints step timings) to close the design's one open question; no code change expected from this, just the
      measurement.

## Workflow follow-up

- Archive this change once 4.1's manual judgment on the 3 test videos is "good" or "acceptable" (per the user); if
  "poor", revisit the design (e.g. Sortformer's streaming parameters) before archiving.
