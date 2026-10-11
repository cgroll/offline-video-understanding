# search-gui Specification

## Purpose
Explore a processed video interactively: search by text, see where along the timeline each variant matches, jump to
moments, find similar frames, and read transcript, scene descriptions and chapters.

## Requirements

### Requirement: Local web app
`ovu app <video>` SHALL serve a single-page GUI on `127.0.0.1` (default port 7860) with the video (HTTP range
requests), one thumbnail per second, and JSON endpoints for metadata, text queries and frame similarity, keeping the
text side of EmbeddingGemma 2 in memory.

#### Scenario: Seeking
- **WHEN** the user clicks a position on the timeline
- **THEN** the video jumps to that second and pauses

### Requirement: Timeline visualisation
The GUI SHALL show a chapter track (if chapters exist), a filmstrip with segment boundary ticks, a curve of the
selected variant with numbered top peaks, one heatmap row per variant (colour scaled per row), a playhead and a hover
tooltip with thumbnail, time, all variant scores, chapter title, scene description and spoken text.

#### Scenario: Text query
- **WHEN** the user submits a query
- **THEN** every row shows the per-second similarity and the top hits appear as cards with thumbnail, time, score,
  scene description and spoken text

### Requirement: Similar frames
The GUI SHALL rank the video by similarity to the unit (frame, window, segment, chapter) containing the current or a
selected second, excluding the source neighbourhood from the top hits.

#### Scenario: Similar to current frame
- **WHEN** the user presses `S` or the "Similar to" button
- **THEN** all rows show similarity to the current position and the hits list the most similar other moments

### Requirement: Text panels
The GUI SHALL offer tabs for the spoken transcript, the scene descriptions (with context when available) and the
chapters with the overall summary; the entry at the playhead SHALL be highlighted and clicking an entry SHALL seek.
For videos without speech the scene tab and the best description-based fusion SHALL be selected by default.

#### Scenario: Video without speech
- **WHEN** the GUI opens a video whose transcript is empty
- **THEN** the scene description tab is shown and the default variant is `caption_ctx+frame` if available
