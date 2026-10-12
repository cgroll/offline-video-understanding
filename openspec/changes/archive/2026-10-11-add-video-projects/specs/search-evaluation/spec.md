## MODIFIED Requirements

### Requirement: Evaluation
`ovu eval` SHALL read the project's `eval.json` (or a file given with `--queries`; queries with `type` and relevant
`intervals`) and report Hit@1, Hit@3 and MRR per variant and query type on two levels: unit level (stored variants
over their own units) and second level (all variants and fusions over peaks, a hit if the peak lies within an
interval ±2 s), plus the rank of every query.

#### Scenario: Query never reached
- **WHEN** a relevant interval is suppressed by a neighbouring peak
- **THEN** the query counts as a miss and its rank is shown as `-`

#### Scenario: No eval set
- **WHEN** the project has no `eval.json` and no `--queries` file is given
- **THEN** the command exits with a message naming the expected file
