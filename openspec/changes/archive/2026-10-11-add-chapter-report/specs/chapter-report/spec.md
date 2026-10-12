## Purpose
Turn a processed project into a readable PDF that tells the video chapter by chapter, with one representative frame,
the time range and a short summary per content chapter.

## ADDED Requirements

### Requirement: Report document
`ovu report <project>` SHALL write `report.pdf` into the project directory with a title page (project title, video
duration, output language, overall plot, characters and themes) followed by one entry per chapter of `chapters.json`
in chronological order. Each entry SHALL show the chapter number, its time range, its title, one representative frame
and its summary.

#### Scenario: Processed project
- **WHEN** the user runs `ovu report my-video` on a project with chapters
- **THEN** `data/projects/my-video/report.pdf` contains one entry per chapter, in the order of the video

#### Scenario: Chapters missing
- **WHEN** the project has no `chapters.json`
- **THEN** the command fails with a message to run `ovu chapters <project>` (or `ovu process`) first

### Requirement: Chapters by content
Report entries SHALL correspond to the content chapters produced by the chapters step, never to technical segments
(hard cuts, embedding changes or fixed windows).

#### Scenario: Many short segments
- **WHEN** a chapter spans 20 technical segments
- **THEN** the report shows that chapter once, with one frame

### Requirement: Timestamps
Time ranges SHALL be formatted `m:ss–m:ss`, or `h:mm:ss–h:mm:ss` for videos of one hour or longer, from the chapter's
start to its end.

#### Scenario: Short video
- **WHEN** a chapter runs from second 95 to second 152 of a 13-minute video
- **THEN** its entry shows `1:35–2:32`

### Requirement: Representative frame
For each chapter the system SHALL pick the second inside the chapter whose frame embedding is most similar to the
chapter's text embedding (title and summary), ignoring nearly uniform frames (e.g. black); if no frame qualifies it
SHALL use the middle of the chapter. The frame SHALL be extracted from the video at a width of at least 1280 pixels
(or the video's width if smaller).

#### Scenario: Chapter starting with a fade from black
- **WHEN** the first seconds of a chapter are black
- **THEN** the chosen frame is a non-black frame that matches the chapter summary best

### Requirement: Labels in the output language
Fixed labels of the report (e.g. "Chapter", "Summary", "Characters", "Themes", "Duration") SHALL be in the project's
output language when available (at least English and German) and English otherwise; all text SHALL render with
non-ASCII characters intact.

#### Scenario: German project
- **WHEN** the project's output language is German
- **THEN** labels read "Kapitel", "Zusammenfassung", "Figuren", "Themen", "Dauer"

### Requirement: Resumable report
The report step SHALL skip an existing `report.pdf` unless `--force` is given, and SHALL be recreated whenever the
chapters are regenerated.

#### Scenario: Chapters regenerated
- **WHEN** chapters are regenerated (e.g. after a language change) and `ovu process` runs
- **THEN** a new `report.pdf` is written
