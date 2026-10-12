# search-evaluation Specification

## Purpose
Find moments in a video by text query over all embedding variants, and measure retrieval and localization quality
against queries with known time intervals.

## Requirements

### Requirement: Per-second scoring and fusion
The system SHALL embed a query with the `SearchQuery` prompt and compute cosine similarities per unit, spread them to
one score per second (mean over units covering the second, ignoring zero vectors), and support late fusion of
variants joined by `+` as the per-second mean over the variants that have a value at that second.

#### Scenario: Fusion on a video without speech
- **WHEN** the variant `text+frame` is scored on a video whose transcript is empty
- **THEN** each second's score equals the `frame` score instead of being pulled down by missing text

### Requirement: Moment ranking
The system SHALL rank moments as greedy peaks of the per-second curve, at least 8 s apart, counting a flat plateau
once at its center; `ovu search` SHALL print the top k peaks with time and score, using a default variant that
depends on whether the video has speech.

#### Scenario: Default variant
- **WHEN** `ovu search <video> "query"` runs without `--variant` on a video without speech
- **THEN** `caption_ctx+frame` is used if available, else `caption+frame`, else `frame`

### Requirement: Evaluation
`ovu eval` SHALL read the project's `eval.json` (or a file given with `--queries`; queries with `type` and relevant
`intervals`) and report Hit@1, Hit@3 and MRR per variant and query type on two levels: unit level (stored variants
over their own units) and second level (all variants and fusions over peaks, a hit if the peak lies within an
interval ±2 s), plus the rank of every query. `queries` MAY be missing or empty, in which case the query report is
skipped.

#### Scenario: Query never reached
- **WHEN** a relevant interval is suppressed by a neighbouring peak
- **THEN** the query counts as a miss and its rank is shown as `-`

#### Scenario: No eval set
- **WHEN** the project has no `eval.json` and no `--queries` file is given
- **THEN** the command exits with a message naming the expected file

### Requirement: Boundary evaluation
When the eval file contains `boundaries` (reference chapter starts in seconds, without 0), `ovu eval` SHALL report
for the topic chapters and, if present, the VLM chapters the number of predicted boundaries, precision, recall and F1.
A predicted start (other than 0) matches at most one unmatched reference within ±5 s, closest first.

#### Scenario: Boundaries only
- **WHEN** `eval.json` contains `boundaries` but no `queries`
- **THEN** only the boundary table is printed
