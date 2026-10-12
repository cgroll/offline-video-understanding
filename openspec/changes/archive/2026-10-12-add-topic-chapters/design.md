## Context

`embed.run` loads EmbeddingGemma once and computes all missing variants into `embeddings.npz`. Each variant is tied to
its units through `segments.spans`, so `to_seconds`, the search, the eval and the GUI's similar mode work for any
variant that has spans. The VLM chapters (`chapter` variant, `chapters.json`) stay as they are. The experiment behind
this change (scratchpad scripts, one test video) is summarized in proposal.md.

## Goals / Non-Goals

**Goals:**
- Topic chapters for every video with speech, computed in the normal non-VLM pipeline, reproducible and resumable.
- A reproducible boundary metric, so that later changes to the segmentation can be compared.

**Non-Goals:**
- Titles or summaries for topic chapters. That would be a later `--vlm` step that writes one title and summary per
  existing topic chapter.
- Using image signals for the segmentation. In the experiment the mixed image similarity lowered F1 from 0.91 to 0.73,
  and recurring-shot markers did not help.
- Replacing the VLM chapters or changing how they are made.

## Decisions

- **Store inside `embeddings.npz` and add no new JSON file.** The arrays are `topic` (one vector per chapter) and
  `topic_starts`/`topic_ends`. The GUI builds the chapter labels from the transcript, because the first sentence is
  the start of the first segment at or after the chapter start. This keeps one source of truth and the existing
  incremental logic: `topic` is "missing" until computed, and `--force` recomputes it. Alternative: a `topics.json`
  file. That is a second file to invalidate, and it holds nothing that cannot be derived.
- **The segmentation is a pure numpy module `topics.py`:** `segment(sim) -> list[start_index]`.
  - The cost matrix comes from 2-D prefix sums of the similarity matrix, so it is vectorized and needs no Python loop
    over pairs.
  - The DP table is filled once for k_max. Every k ≤ k_max is backtracked from the same table, so all candidate
    segmentations cost one DP.
  - The silhouette is implemented in numpy, about ten lines, to avoid adding scikit-learn as a direct dependency. A
    unit alone in its chapter gets silhouette 0, as in scikit-learn.
  - Alternatives considered: Foote novelty (F1 0.82 with the oracle count and 0.74 automatic, see proposal) and
    agglomerative clustering with a contiguity constraint (0.45).
- **Units are the transcript segments, the sentence-like chunks the ASR gives.** Fixed windows would cut sentences, and
  the boundary precision is per sentence.
- **Search vector = embedding of the chapter's full transcript text.** It is the same kind of document vector as
  `chapter`, so the query side, the spans and the eval need no special case. Long chapters stay well below the 8192
  token limit at speech rates (a 5-minute chapter is about 800 words). Alternative: the mean of the sentence vectors.
  That is weaker as a document representation and was not measured.
- **GUI chapter hits come from the unit scores.** `/api/query` and `/api/similar` additionally return the per-unit
  scores for `topic` and `chapter` as `units`. The frontend ranks those and picks each card's thumbnail as the best
  second of the selected variant inside the chapter span. Chapter cards reuse the clip card layout, including the score
  badge on the thumbnail.
- **The boundary eval lives in `search.evaluate`.** `boundaries` in `eval.json` is optional, and it is evaluated
  against `topic_starts` and `chapter_starts` from `embeddings.npz`. `eval/README.md` documents the key.

## Risks / Trade-offs

- [Tuned on one test video; the silhouette maximum is flat (k=12: 0.088, k=13/14: 0.086)] → `ovu eval` makes the
  boundary metric reproducible. Check the other test projects visually in the topic track, and add `boundaries` to
  their eval sets later.
- [Speech with little topic structure (dialogue in a film) can give arbitrary chapters] → They are only a navigation
  aid; the topic track is labeled as such, and nothing else depends on them.
- [O(k_max·n²) DP for long videos: 1 h ≈ 600 sentences, k_max = 40 → about 14M cell updates in numpy rows] →
  vectorized per (k, end); a few seconds at most.
- [Chapter labels are the first sentence, which may be a greeting or a fragment] → Accepted for now; VLM titles are
  the planned follow-up.

## Migration Plan

Existing projects get `topic` on the next `ovu process`/`ovu embed`, because the variant is missing and only it is
computed. Without it, the GUI hides the track and the chapter list as before. Rollback: drop the arrays. No other
file changes.
