# output-language Specification

## Purpose
Choose the language of all model-generated texts per video, so that descriptions, chapters and summaries match the
video by default while users can request another language.

## Requirements

### Requirement: Language resolution
The system SHALL resolve the output language of a video in this order: a language given by the user (ISO 639-1 code
or English name), the language stored in `meta.json`, the language detected (lingua, offline) from the transcript if
it has at least 20 words, the language detected from the video title, and finally English. The result and its source
(`user`, `transcript`, `title`, `fallback`) SHALL be stored in `meta.json` and reused by all later steps.

#### Scenario: Video with speech
- **WHEN** a video with German speech is captioned without `--language`
- **THEN** descriptions, chapters and summaries are written in German and `meta.json` records `transcript` as source

#### Scenario: Video without speech
- **WHEN** a video has no transcribed speech and an English title
- **THEN** generated texts are English and `meta.json` records `title` as source

#### Scenario: User choice
- **WHEN** the user runs `ovu process <video> --language fr`
- **THEN** generated texts are French and later steps without `--language` keep using French

### Requirement: Transcript stays original
The transcript SHALL always be in the spoken language and SHALL NOT be translated; only generated texts follow the
output language.

#### Scenario: Different output language
- **WHEN** the output language differs from the spoken language
- **THEN** the transcript panel shows the original speech while scene descriptions and chapters use the output language

### Requirement: Language-neutral prompts
Prompts SHALL be written in English with English JSON keys and SHALL request text values in the output language by
its English name.

#### Scenario: Same keys for every language
- **WHEN** two videos are processed in different output languages
- **THEN** their result files have identical JSON keys
