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
spaced frames, the video title and the video's own spoken transcript (chronological, with speaker labels where
known, or a placeholder when there is no speech), and SHALL then describe each segment from all its frames as video
input (1 fps) together with the global summary and the previous segment's description, storing the result in
`captions_ctx.json`. The prompt SHALL instruct the model to describe only what is visible in the current segment.
After generation, `summary.json` SHALL be checked for its expected top-level fields; if any are missing the file is
still written (for inspection) but a warning SHALL be printed.

#### Scenario: Consistent naming
- **WHEN** the same character appears in several segments
- **THEN** descriptions use the name established in the global summary

#### Scenario: Empty segment
- **WHEN** all frames of a segment are nearly uniform (grey-level std < 12, e.g. black)
- **THEN** the segment is described without context, so that no story content is invented

#### Scenario: Name only in speech
- **WHEN** a person's name is said in the transcript but not shown as on-screen text
- **THEN** the global summary MAY use that name for a visually matching character, since the transcript is this
  video's own data, not external knowledge

#### Scenario: Malformed summary
- **WHEN** the model's answer for the global summary is not valid JSON or is missing an expected field
- **THEN** `summary.json` is still written as given, and a warning naming the problem is printed

### Requirement: Summary-only mode
The system SHALL offer a mode that writes or refreshes only `summary.json` (from the storyboard, title and
transcript as above) and SHALL NOT load the full per-segment frame set, write `captions_ctx.json` or loop over
segments. Like other steps, it SHALL skip the work if `summary.json` already exists unless `--force` is given.

#### Scenario: Quick overview
- **WHEN** only a coarse description of a video is wanted, not a scene-by-scene story
- **THEN** summary-only mode produces `summary.json` in roughly the time of one VLM call, without the per-segment
  captioning cost

#### Scenario: Re-running without --force
- **WHEN** summary-only mode runs again and `summary.json` already exists
- **THEN** it is left unchanged and the step reports it as already done

### Requirement: Repetition-safe generation
Every local VLM call (plain captions, context captions, the global summary) SHALL use a repetition penalty on top of
greedy decoding, so that a longer or more complex prompt does not cause the model to degenerate into repeating one
token or phrase until the output token budget is exhausted.

#### Scenario: Long prompt
- **WHEN** a prompt is long enough that greedy decoding alone would risk a repetition loop (e.g. a global summary
  prompt that includes a full transcript)
- **THEN** generation still completes with varied, non-repeating text within the token budget

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
