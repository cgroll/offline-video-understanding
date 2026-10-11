# Eval sets

One JSON file per video, named `<slug>.json` (the slug of the video file, see `ovu list`). Eval sets describe video
content and are therefore git-ignored; keep them locally.

```json
{
 "video": "file name of the video in data/videos",
 "note": "how the intervals were obtained",
 "queries": [
  {"type": "speech", "q": "query text", "intervals": [[12, 20]]},
  {"type": "visual", "q": "query text", "intervals": [[40, 45], [130, 138]]}
 ]
}
```

- `type`: `speech` (only findable via what is said), `visual` (only via what is shown), `both`, or `story`
  (plot-level, spanning several scenes); results are reported per type.
- `intervals`: relevant time ranges in seconds; a query can have several.
- Run with `uv run ovu eval <video>` (or `--queries <file>`).
