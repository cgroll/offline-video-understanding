# multimodal-embeddings Specification

## Purpose
Represent every part of a video in one vector space with EmbeddingGemma 2 (text, images, video and audio), on several
time granularities, so that a text query can be matched against what is said, shown, heard and described.

## Requirements

### Requirement: Embedding model
The system SHALL compute L2-normalized 768-d EmbeddingGemma 2 vectors (bfloat16 on GPU) and store all variants in
`embeddings.npz`; text inputs SHALL use the document prefix `title: <title or none> | text: ...`.

#### Scenario: Comparable vectors
- **WHEN** a text query is compared with any stored variant
- **THEN** the dot product of the normalized vectors is the cosine similarity

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

### Requirement: Content segments
The system SHALL split a video into content segments of 2 to 10 s at 1 s resolution, with boundaries at hard cuts
(ffmpeg scene score > 0.3) and at seconds where the frame-embedding similarity to the previous second drops below
0.85; shorter segments SHALL be merged into their predecessor and longer ones split evenly. Segment spans SHALL be
stored as `shot_starts`/`shot_ends`.

#### Scenario: Animated sequence without hard cuts
- **WHEN** a long animated passage changes content without a cut
- **THEN** embedding drops create segment boundaries and no segment exceeds 10 s

### Requirement: Incremental computation
The step SHALL compute only variants that are missing (default: all whose inputs exist); `--force` SHALL recompute the
requested variants while keeping all other stored variants.

#### Scenario: Adding a variant later
- **WHEN** `ovu embed <video> caption_ctx --force` runs on an existing `embeddings.npz`
- **THEN** only `caption_ctx` is recomputed and all other arrays are preserved
