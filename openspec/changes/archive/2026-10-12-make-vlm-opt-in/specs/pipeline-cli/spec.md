## MODIFIED Requirements

### Requirement: Full pipeline
`ovu process <project>` SHALL run transcription and all embedding variants that need no VLM output. With `--vlm` it
SHALL additionally run plain and context scene descriptions, chapters, their embeddings and finally the chapter
report, loading the VLM once for all VLM steps. `--language` SHALL set the output language; without `--vlm` it only
stores it in the project.

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
