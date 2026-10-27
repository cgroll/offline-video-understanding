# pipeline-cli Specification

## Purpose
Run the whole local pipeline, or single steps, with one command-line tool `ovu`.

## Requirements

### Requirement: Full pipeline
`ovu process <project>` SHALL run transcription and all embedding variants that need no VLM output. With `--vlm` it
SHALL additionally run plain and context scene descriptions, chapters, their embeddings and finally the chapter
report, loading the VLM once for all VLM steps. With `--vlm --summary-only` it SHALL instead only (re)write
`summary.json`, skipping plain captions, context captions, chapters and the report. `--language` SHALL set the
output language; without `--vlm` it only stores it in the project.

#### Scenario: Re-running after an interruption
- **WHEN** `ovu process` is run again on a partially processed project
- **THEN** finished steps are skipped and processing continues where it stopped

#### Scenario: Report at the end
- **WHEN** `ovu process --vlm` completes on a project
- **THEN** `report.pdf` exists in the project directory

#### Scenario: Default run without VLM
- **WHEN** the user runs `ovu process <project>` without `--vlm`
- **THEN** transcript and the `frame`, `video_shots`, `text`, `video`, `audio`, `video_audio` and `text_video`
  embeddings are computed, no vision-language model is loaded, and no descriptions, chapters or report are created

#### Scenario: Summary-only run
- **WHEN** the user runs `ovu process <project> --vlm --summary-only`
- **THEN** transcript and non-VLM embeddings are computed as usual, `summary.json` is written, and no
  `captions.json`, `captions_ctx.json`, `chapters.json` or `report.pdf` is created

### Requirement: Single steps and overview
The CLI SHALL provide `new`, `list`, `transcribe`, `embed`, `caption [--context] [--summary-only]`, `chapters`,
`report`, `search`, `eval` and `app` subcommands, each processing step accepting `--force`; `ovu list` SHALL show
every project with its title, output language and the result files already computed.

#### Scenario: Overview
- **WHEN** the user runs `ovu list`
- **THEN** each project is printed with title, language and existing result files, or "(not processed)"

#### Scenario: Summary-only caption step
- **WHEN** the user runs `ovu caption <project> --context --summary-only`
- **THEN** only `summary.json` is written or refreshed; `captions_ctx.json` is not read for completion and not
  written to
