# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
