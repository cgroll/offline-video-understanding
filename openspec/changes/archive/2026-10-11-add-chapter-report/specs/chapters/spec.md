## MODIFIED Requirements

### Requirement: Chapter segmentation
The system SHALL segment a video into content chapters in two text-only VLM passes over the segment descriptions
(with start/end seconds, preferring `captions_ctx.json` over `captions.json`): first chapter starts with a short
title only, then one call per chapter that writes its `title` and `summary` from that chapter's descriptions, all in
the output language. It SHALL post-process the chapters so that starts lie on segment boundaries, the first chapter
starts at 0, each chapter ends where the next begins, chapters shorter than 20 s are merged into a neighbour and there
are at most 20 chapters. A chapter longer than max(120 s, 1/8 of the video) SHALL be split by asking the model again
with only that chapter's descriptions, for up to three rounds.

#### Scenario: Gap or overlap in the model answer
- **WHEN** the model returns chapters with gaps, overlaps or unsorted times
- **THEN** the stored chapters are sorted, deduplicated, snapped to segment boundaries and gap-free

#### Scenario: Too fine-grained answer
- **WHEN** the model proposes a chapter for almost every segment, including chapters of a few seconds
- **THEN** short chapters are merged so that every chapter lasts at least 20 s and there are at most 20

#### Scenario: Model stops proposing chapters early
- **WHEN** the first pass puts all chapter starts into the first third of the video
- **THEN** the long remaining chapter is subdivided by a second pass over its own descriptions

#### Scenario: Truncated answer
- **WHEN** the model's answer is cut off and is no longer valid JSON
- **THEN** all complete chapter entries before the cut are used

#### Scenario: No usable chapters
- **WHEN** no chapter can be read from the answer
- **THEN** the step fails with an error and writes neither chapters nor a summary

### Requirement: Bottom-up video summary
The system SHALL produce an overall summary (`plot`, `characters`, `themes`) from the video title and the chapter
list, and SHALL store it with the chapters, the output language and the raw model answers in `chapters.json`.

#### Scenario: Summary available in the GUI
- **WHEN** `chapters.json` exists
- **THEN** the GUI shows the summary above the chapter list
