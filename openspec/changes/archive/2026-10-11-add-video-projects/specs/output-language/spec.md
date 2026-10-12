## MODIFIED Requirements

### Requirement: Language resolution
The system SHALL resolve the output language of a project in this order: a language given by the user (ISO 639-1
code or English name), the language stored in `project.json`, the language detected (lingua, offline) from the
transcript if it has at least 20 words, the language detected from the project title, and finally English. The result
and its source (`user`, `transcript`, `title`, `fallback`) SHALL be stored in `project.json` and reused by all later
steps.

#### Scenario: Video with speech
- **WHEN** a video with German speech is captioned without `--language`
- **THEN** descriptions, chapters and summaries are written in German and `project.json` records `transcript` as
  source

#### Scenario: Video without speech
- **WHEN** a video has no transcribed speech and an English title
- **THEN** generated texts are English and `project.json` records `title` as source

#### Scenario: User choice
- **WHEN** the user runs `ovu process <project> --language fr`
- **THEN** generated texts are French and later steps without `--language` keep using French

## ADDED Requirements

### Requirement: Changing the language
When a language given by the user differs from the language stored in the project, the system SHALL delete the
project's generated texts (scene descriptions, global summary, chapters, reports) and their embeddings before
continuing, so that no project mixes languages.

#### Scenario: Switch from English to German
- **WHEN** a project has English descriptions and the user runs `ovu process <project> --language de`
- **THEN** descriptions, summary, chapters and reports are regenerated in German, while transcript and visual
  embeddings are kept
