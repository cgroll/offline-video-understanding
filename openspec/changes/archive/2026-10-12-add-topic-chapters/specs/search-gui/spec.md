## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Chapter hits
After a query or a similarity search the GUI SHALL list the best matching chapters above the clip hits, ranked by the
cosine similarity of their own vector: topic chapters, or the VLM chapters when the video has no topic chapters.

#### Scenario: Open a found chapter
- **WHEN** the user clicks a chapter card
- **THEN** the video seeks to the chapter start; the card shows rank, similarity score, time range, duration, the
  thumbnail of the best-matching second inside the chapter for the selected variant, and the chapter's title or first
  sentence
