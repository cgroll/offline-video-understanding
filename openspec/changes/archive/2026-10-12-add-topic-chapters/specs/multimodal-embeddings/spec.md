## MODIFIED Requirements

### Requirement: Embedding variants
The system SHALL provide the variants `frame` (one image per second); `text`, `video`, `audio`, `video_audio`,
`text_video` (20 s windows, 10 s stride); `video_shots`, `caption`, `caption_ctx` (per content segment); `chapter`
(per chapter); and `topic` (per topic chapter: its transcript text as a document, spans in
`topic_starts`/`topic_ends`).

#### Scenario: Window without speech
- **WHEN** a 20 s window contains no transcribed words
- **THEN** its `text` vector is all zeros and it counts as missing in search

#### Scenario: Frames sampled at 1 fps
- **WHEN** video or frame variants are computed
- **THEN** frames are decoded with ffmpeg at 1 fps and 640x360 and passed to the model without resampling

#### Scenario: Topic variant without VLM
- **WHEN** `ovu process <project>` runs without `--vlm` on a video with speech
- **THEN** `embeddings.npz` contains `topic`, `topic_starts` and `topic_ends`
