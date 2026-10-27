# Spec Delta

## MODIFIED Requirements

### Requirement: Local speech to text with timestamps
The system SHALL transcribe the audio track (16 kHz mono) with Parakeet TDT 0.6B v3 (onnx-asr, int8, CPU) and
Silero VAD, and SHALL write `transcript.json` containing the video duration, VAD speech segments
(`start`, `end`, `text`, `speaker`) and words with absolute start times (`t`, `word`) merged from token timestamps.
Each segment's `speaker` SHALL be assigned locally by speaker diarization of the same audio track, identifying the
diarized speaker interval with the largest time overlap with the segment; `speaker` SHALL be `null` when no
diarized interval overlaps the segment at all.

#### Scenario: Video with speech
- **WHEN** `ovu transcribe <video>` runs on a video with German speech
- **THEN** `transcript.json` lists speech segments and word timestamps in seconds from the video start

#### Scenario: Video without speech
- **WHEN** the video contains only music or silence
- **THEN** `transcript.json` is still written, with few or empty segments, and later steps treat the transcript as
  missing rather than as content

#### Scenario: Two people talking
- **WHEN** a video has two people speaking in different, non-overlapping intervals
- **THEN** their segments carry two distinct `speaker` labels, consistent across the whole video (the same person
  keeps the same label throughout)

#### Scenario: More than four distinct voices
- **WHEN** a video has more than four distinct speakers
- **THEN** every segment still gets one of (at most) four speaker labels, each voice mapped to whichever label's
  diarized intervals overlap it most - the system SHALL NOT error or stop transcribing because of this

#### Scenario: No matching diarized interval
- **WHEN** an ASR segment falls in a gap the diarizer did not assign to any speaker
- **THEN** that segment's `speaker` is `null` rather than a guessed label
