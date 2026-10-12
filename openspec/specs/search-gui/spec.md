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
The GUI SHALL show a chapter track (if chapters exist), a topic track (if topic chapters exist), a filmstrip with
segment boundary ticks, a curve of the selected variant with numbered top peaks, one heatmap row per variant (colour
scaled per row), a playhead and a hover tooltip with thumbnail, time, all variant scores, chapter and topic chapter,
scene description and spoken text.

#### Scenario: Text query
- **WHEN** the user submits a query
- **THEN** every row shows the per-second similarity and the top hits appear as cards with thumbnail, time, score,
  scene description and spoken text

#### Scenario: Topic track
- **WHEN** a video with topic chapters is open
- **THEN** the topic track shows one block per topic chapter labelled with the beginning of its first sentence, the
  block under the playhead is outlined, clicking a block seeks to its start, and after a query each block shows its
  score on the colour ramp

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

### Requirement: Chapter hits
After a query or a similarity search the GUI SHALL list the best matching chapters above the clip hits, ranked by the
cosine similarity of their own vector: topic chapters, or the VLM chapters when the video has no topic chapters.

#### Scenario: Open a found chapter
- **WHEN** the user clicks a chapter card
- **THEN** the video seeks to the chapter start; the card shows rank, similarity score, time range, duration, the
  thumbnail of the best-matching second inside the chapter for the selected variant, and the chapter's title or first
  sentence

### Requirement: Playback speed
The player SHALL offer the speeds 1×, 1.5× and 2× as a toggle in the player bar and via the keys `<` and `>`,
SHALL show the active speed, and SHALL restore the last chosen speed when the GUI is opened again in the same browser.

#### Scenario: Faster playback
- **WHEN** the user clicks 2× or presses `>` twice from 1×
- **THEN** the video plays at double speed, 2× is highlighted, and timeline and transcript stay in sync

#### Scenario: Speed remembered
- **WHEN** the user chose 1.5× and reloads the page
- **THEN** the video starts at 1.5×
