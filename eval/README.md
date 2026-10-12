# Eval sets

An eval set is a file `eval.json` in a project directory (`data/projects/<name>/eval.json`). Eval sets describe video
content and are therefore never committed (`data/` is git-ignored).

```json
{
 "video": "file name of the project's video",
 "note": "how the intervals were obtained",
 "queries": [
  {"type": "speech", "q": "query text", "intervals": [[12, 20]]},
  {"type": "visual", "q": "query text", "intervals": [[40, 45], [130, 138]]}
 ],
 "boundaries": [149, 192, 402]
}
```

- `type`: `speech` (only findable via what is said), `visual` (only via what is shown), `both`, or `story`
  (plot-level, spanning several scenes); results are reported per type.
- `intervals`: relevant time ranges in seconds; a query can have several.
- Run with `uv run ovu eval <project>` (or `--queries <file>`).
- `boundaries` (optional): reference chapter starts in seconds (without 0), e.g. where each story or topic begins.
  `ovu eval` reports precision, recall and F1 of the topic chapter starts (and the VLM chapter starts, if present);
  a predicted start matches at most one reference within ±5 s. `queries` may be left out for a boundaries-only set.
