# scene-descriptions Specification

## Purpose
Give every content segment a human-readable description with a local vision-language model, so that scenes without
speech become searchable as text and readable in the GUI.

## Requirements

### Requirement: Plain scene descriptions
The system SHALL describe each content segment with Qwen3-VL-4B-Instruct (4-bit nf4) from three frames (start,
middle, end; 960x540) and SHALL store the JSON fields `description`, `on_screen_text`, `shot_type`, `keywords`
plus the raw answer in `captions.json`, with text values in the video's output language.

#### Scenario: Text shown on screen
- **WHEN** a segment shows a title or caption text
- **THEN** the text is reproduced in `on_screen_text`, each distinct text once

### Requirement: Descriptions with context
With `--context` the system SHALL first create a global summary (`summary.json`) from a storyboard of 40 evenly
spaced frames plus the video title, and SHALL then describe each segment from all its frames as video input (1 fps)
together with the global summary and the previous segment's description, storing the result in `captions_ctx.json`.
The prompt SHALL instruct the model to describe only what is visible in the current segment.

#### Scenario: Consistent naming
- **WHEN** the same character appears in several segments
- **THEN** descriptions use the name established in the global summary

#### Scenario: Empty segment
- **WHEN** all frames of a segment are nearly uniform (grey-level std < 12, e.g. black)
- **THEN** the segment is described without context, so that no story content is invented

### Requirement: Generic prompts
Pipeline prompts SHALL NOT contain examples, names, genres or other hints derived from a specific video; only the
video title from the file name MAY be passed as metadata.

#### Scenario: New video type
- **WHEN** a video of an unseen genre is processed
- **THEN** the prompts are identical to those used for any other video, except for the title

### Requirement: Resumable captioning
Captioning SHALL write results after every segment and SHALL skip segments already present unless `--force` is given.

#### Scenario: Interrupted run
- **WHEN** a captioning run is aborted and restarted without `--force`
- **THEN** it continues with the first segment that has no description
