# Spec Delta

## MODIFIED Requirements

### Requirement: Text panels
The GUI SHALL offer tabs for the spoken transcript, the scene descriptions (with context when available) and the
chapters with the overall summary; the entry at the playhead SHALL be highlighted and clicking an entry SHALL seek.
For videos without speech the scene tab and the best description-based fusion SHALL be selected by default. In the
transcript tab, a line whose segment has a speaker label SHALL show that label next to the spoken text; a line
without one SHALL show the text alone.

#### Scenario: Video without speech
- **WHEN** the GUI opens a video whose transcript is empty
- **THEN** the scene description tab is shown and the default variant is `caption_ctx+frame` if available

#### Scenario: Multiple speakers
- **WHEN** the transcript panel shows segments from two different speakers
- **THEN** each line displays which speaker it is attributed to, distinguishably from the spoken text

#### Scenario: Unlabelled segment
- **WHEN** a segment's `speaker` is `null`
- **THEN** its transcript line shows the text without a speaker label, not a placeholder like "unknown"
