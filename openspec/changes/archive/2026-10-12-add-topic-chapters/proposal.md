## Why

Between content segments (2-10 s) and the whole video there is no navigation level unless the VLM runs. The VLM
chapters are slow (~20 min of scene descriptions for 17 min of video) and use only the image descriptions, not what is
said. On a 17-minute test video with 11 reference chapter starts, the VLM-style chaptering over the transcript reached a
boundary F1 of 0.40 (boundaries 1-2 sentences late, long chapters over-split). An embedding-only segmentation of the
transcript sentences reached 0.91, needed no extra model and ran in seconds. With topic chapters the GUI can show and
rank whole chapters, not only single moments.

## What Changes

- New pipeline output **topic chapters**: one EmbeddingGemma vector per transcript sentence. An optimal contiguous
  segmentation (dynamic programming over the cosine self-similarity matrix) is computed for every number of chapters,
  and the number is chosen by the silhouette score. Runs without the VLM as part of `ovu process`/`ovu embed`.
- New embedding variant `topic`: the transcript text of each topic chapter embedded as a document, with spans
  `topic_starts`/`topic_ends` in `embeddings.npz`. It is searchable like the other variants: a heatmap row, `ovu search`
  and `ovu eval`.
- GUI:
  - a "Topics" track on the timeline showing the topic chapters, with their query score when there is a query
  - a ranked list of matching chapters above the clip hits; it uses topic chapters, or the VLM chapters when the video
    has no topic chapters
  - chapter cards show their score as a badge on the thumbnail, the same way the clip cards already do
- `ovu eval`: an optional `boundaries` list in `eval.json` (reference chapter starts) is scored as boundary
  precision/recall/F1 (±5 s) for the topic chapters and, if present, the VLM chapters; `queries` becomes optional.

## Capabilities

### New Capabilities
- `topic-chapters`: segmentation of a video into topic chapters from the transcript sentence embeddings, and the
  choice of how many chapters to make

### Modified Capabilities
- `multimodal-embeddings`: new variant `topic` (per topic chapter) with spans `topic_starts`/`topic_ends`
- `search-gui`: topic track and ranked chapter hits (with score) above the clip hits
- `search-evaluation`: optional boundary evaluation from `eval.json`; `queries` optional

## Impact

- New module `src/ovu/topics.py` (numpy only, no new dependency). Changes in `embed.py`, `segments.py` (spans),
  `search.py` (boundary eval), `app/server.py` and `app/index.html`.
- VRAM: none extra. It reuses the EmbeddingGemma instance that is already loaded in the embedding step. Runtime: about
  1 s to embed ~150 sentences plus the chapter texts, and well under a second for the DP over every k ≤ 40 at a few
  hundred sentences.
- Videos without speech get no `topic` variant and no topic track. Everything else is unchanged.
- Eval: `topic` is a new stored variant in the query eval (per-second Hit@1/Hit@3/MRR), measured on the projects that
  have query eval sets and compared with `text+frame`. Better chapter-level hits are
  expected, and no change for the other variants. Boundary quality is measured on the test video, where the
  `eval_boundaries.json` used in the experiment moves into `eval.json` (target: reproduce F1 0.91). There is only one
  annotated video, so this is a tendency, not a result.
