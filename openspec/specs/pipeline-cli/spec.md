# pipeline-cli Specification

## Purpose
Run the whole local pipeline, or single steps, with one command-line tool `ovu`.

## Requirements

### Requirement: Full pipeline
`ovu process <url-or-video>` SHALL download the video if a URL is given, then run transcription, `frame` and
`video_shots` embeddings, plain and context scene descriptions, chapters, and finally all remaining embedding
variants; `--no-vlm` SHALL skip descriptions and chapters and `--language` SHALL set the output language. The VLM
SHALL be loaded once for all VLM steps.

#### Scenario: Re-running after an interruption
- **WHEN** `ovu process` is run again on a partially processed video
- **THEN** finished steps are skipped and processing continues where it stopped

### Requirement: Single steps and overview
The CLI SHALL provide `list`, `download`, `transcribe`, `embed`, `caption [--context]`, `chapters`, `search`, `eval`
and `app` subcommands, each step accepting `--force`; `ovu list` SHALL show every video in `data/videos/` with the
result files already computed.

#### Scenario: Overview
- **WHEN** the user runs `ovu list`
- **THEN** each video slug is printed with its existing result files, or "(not processed)"
