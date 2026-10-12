## MODIFIED Requirements

### Requirement: Full pipeline
`ovu process <project>` SHALL run transcription, `frame` and `video_shots` embeddings, plain and context scene
descriptions, chapters, and finally all remaining embedding variants; `--no-vlm` SHALL skip descriptions and chapters
and `--language` SHALL set the output language. The VLM SHALL be loaded once for all VLM steps.

#### Scenario: Re-running after an interruption
- **WHEN** `ovu process` is run again on a partially processed project
- **THEN** finished steps are skipped and processing continues where it stopped

### Requirement: Single steps and overview
The CLI SHALL provide `new`, `list`, `transcribe`, `embed`, `caption [--context]`, `chapters`, `search`, `eval` and
`app` subcommands, each processing step accepting `--force`; `ovu list` SHALL show every project with its title,
output language and the result files already computed.

#### Scenario: Overview
- **WHEN** the user runs `ovu list`
- **THEN** each project is printed with title, language and existing result files, or "(not processed)"
