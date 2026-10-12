## 1. Segmentation

- [x] 1.1 `topics.py`: vectorized DP cost from 2-D prefix sums, one DP table for k_max = min(40, n/2) with backtracking
  for every k, numpy silhouette (singleton = 0), `segment(sim) -> start indices`, `spans(starts, unit_starts,
  duration)` with the first chapter at 0 and no gaps. Verify by running it on the cached test-video sentence
  embeddings: k = 12 and the same boundaries as the scratchpad experiment.

## 2. Embedding variant

- [x] 2.1 `embed.py`: variant `topic` (available only when the transcript has ≥ 4 non-empty segments); embed the
  sentences with the loaded model, segment, embed each chapter's text as a document, store `topic`, `topic_starts`
  and `topic_ends`; print the number of chapters, k and the time. Verify that `uv run ovu process <project>` computes
  only `topic` and keeps all other arrays.
- [x] 2.2 `segments.spans`: `topic` → `topic_starts`/`topic_ends`. Verify that `uv run ovu search <project> "<query>"
  --variant topic` prints peaks.
- [x] 2.3 Docs: variant list in the `embed.py` docstring, README/PROJECT.md (topic chapters, no VLM needed),
  AGENTS.md file list.

## 3. Evaluation

- [x] 3.1 `search.evaluate`: optional `queries`, optional `boundaries` with a table of n/P/R/F1 (±5 s, one-to-one,
  closest first) for `topic` and `chapter`. Move `data/projects/<project>/eval_boundaries.json` into
  `data/projects/<project>/eval.json`. Verify that `uv run ovu eval <project>` reports F1 ≈ 0.91 for topic.
- [x] 3.2 Document `boundaries` in `eval/README.md`.
- [x] 3.3 Run `uv run ovu eval <project>` on the projects with query eval sets after computing `topic` there, and
  compare `topic` with `text+frame` (current default) on the second level. Note the result in the final summary.

## 4. GUI

- [x] 4.1 `server.py`: label for `topic`; `meta` returns `topics` (start, end, first sentence); `/api/query` and
  `/api/similar` return `units` (per-unit scores for `topic` and `chapter`). Verify with `curl` on `/api/meta` and
  `/api/query?q=...`.
- [x] 4.2 `index.html`: topic track on the timeline. One block per topic chapter labelled with its first sentence,
  the current block outlined, clicking it seeks, and after a query the score is shown on the colour ramp. The tooltip
  names the topic chapter. Verify in the browser on the test video.
- [x] 4.3 `index.html`: chapter hits above the clip hits (topic, else VLM chapters), as cards with rank, time range,
  duration, a score badge as on the clip cards, the best-second thumbnail of the selected variant, text and
  click-to-seek. Verify in the browser with a query and with "Similar".

## 5. Check

- [x] 5.1 Run `openspec validate --strict add-topic-chapters` and `openspec validate --specs --strict`, both green.
- [x] 5.2 Restart the GUI on the test video and check end to end with 2-3 queries; take a screenshot.

## Workflow follow-up

- Archive the change (`/opsx:archive`) after review.
