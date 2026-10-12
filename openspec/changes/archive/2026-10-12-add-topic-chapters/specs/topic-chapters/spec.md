# Spec Delta

## Purpose

Split a video with speech into topic chapters from what is said, without the VLM, as a navigation and search level
between content segments and the whole video.

## ADDED Requirements

### Requirement: Sentence units
The system SHALL use the non-empty transcript segments as units, embed each one as a text document with EmbeddingGemma
2 and compare them by cosine similarity. A video with fewer than 4 non-empty segments SHALL get no topic chapters.

#### Scenario: Video without speech
- **WHEN** the transcript of a video is empty
- **THEN** no topic chapters and no `topic` variant are stored, and every other step works as before

### Requirement: Optimal contiguous segmentation
For a given number of chapters k, the system SHALL split the units into k contiguous chapters that minimize the sum
over chapters of (number of units − mean pairwise cosine similarity inside the chapter × number of units), computed
exactly. Chapter starts SHALL lie on unit starts.

#### Scenario: Topic change between sentences
- **WHEN** a video talks about one topic and then about an unrelated one
- **THEN** a chapter boundary lies at the start of the first sentence of the new topic

### Requirement: Number of chapters
The system SHALL compute the optimal segmentation for every k from 2 to min(40, number of units / 2) and keep the
k with the highest mean silhouette score (cosine distance, units labeled by chapter).

#### Scenario: No preset count
- **WHEN** topic chapters are computed
- **THEN** the number of chapters is chosen automatically and is not given by the user

### Requirement: Chapter spans
Topic chapters SHALL cover the whole video without gaps: the first starts at 0, each ends where the next begins and
the last ends at the video duration. Each chapter's text SHALL be the transcript text of its units.

#### Scenario: Silence before the first sentence
- **WHEN** the first sentence starts at second 5
- **THEN** the first topic chapter still starts at 0
