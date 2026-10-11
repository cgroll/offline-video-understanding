# transcription Specification

## Purpose
Turn the speech in a video into text with word-level timestamps, locally, as the basis for transcript search and
the transcript panel of the GUI.

## Requirements

### Requirement: Local speech to text with timestamps
The system SHALL transcribe the audio track (16 kHz mono) with Parakeet TDT 0.6B v3 (onnx-asr, int8, CPU) and
Silero VAD, and SHALL write `transcript.json` containing the video duration, VAD speech segments
(`start`, `end`, `text`) and words with absolute start times (`t`, `word`) merged from token timestamps.

#### Scenario: Video with speech
- **WHEN** `ovu transcribe <video>` runs on a video with German speech
- **THEN** `transcript.json` lists speech segments and word timestamps in seconds from the video start

#### Scenario: Video without speech
- **WHEN** the video contains only music or silence
- **THEN** `transcript.json` is still written, with few or empty segments, and later steps treat the transcript as
  missing rather than as content

### Requirement: Skip finished work
The step SHALL not recompute an existing `transcript.json` unless `--force` is given.

#### Scenario: Second run
- **WHEN** `transcript.json` exists and `--force` is not given
- **THEN** the step prints that the file exists and does nothing
