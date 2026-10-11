# chapters Specification

## Purpose
Aggregate segment descriptions into story-level chapters and an overall summary, as a navigation level in the GUI and
as a search level for plot-level queries.

## Requirements

### Requirement: Chapter segmentation
The system SHALL ask the local VLM (text only) to group the segment descriptions (with start/end seconds, preferring
`captions_ctx.json` over `captions.json`) into 6 to 20 contiguous chapters with `title` and `summary` in the
output language, and SHALL post-process them so that chapter starts lie on segment boundaries, the first chapter
starts at 0 and each chapter ends where the next begins.

#### Scenario: Gap or overlap in the model answer
- **WHEN** the model returns chapters with gaps, overlaps or unsorted times
- **THEN** the stored chapters are sorted, deduplicated, snapped to segment boundaries and gap-free

### Requirement: Bottom-up video summary
The system SHALL produce an overall summary (`plot`, `characters`, `themes`) from the video title and the chapter
list, and SHALL store it with the chapters, the output language and both raw model answers in `chapters.json`.

#### Scenario: Summary available in the GUI
- **WHEN** `chapters.json` exists
- **THEN** the GUI shows the summary above the chapter list
