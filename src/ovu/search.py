"""Text search over a processed video, and evaluation against queries with known time intervals.

A variant is a stored one (text, frame, video_shots, caption_ctx, ...) or a late fusion of several joined by "+":
the mean of their per-second cosine similarities, ignoring variants that have nothing at that second (text where
nothing is said).

Eval, two levels (each query has relevant time intervals):
  unit    stored variants only, ranked over their own units (window / shot / frame / chapter); a unit is relevant if
          it overlaps an interval by >= min(3 s, interval length, unit length)
  second  every variant incl. fusions, scores spread to seconds; ranked over peaks (plateau centers, >= 8 s
          apart) like the GUI; a peak is relevant if it lies inside an interval +-2 s. Measures localization.
"""

import json
import warnings
from pathlib import Path

import numpy as np

from ovu.embed import VARIANTS, load_embeddings
from ovu.segments import spans, to_seconds

FUSIONS = ["text+video", "text+video_shots", "text+frame", "text+video+audio", "text+caption",
           "caption+frame", "text+caption+frame", "caption_ctx+frame", "chapter+frame", "chapter+caption_ctx+frame"]
MIN_OVERLAP_S = 3.0
NMS_S = 8
TOL_S = 2
MISS = 10**6


def per_second(emb: dict, q: np.ndarray, variant: str) -> np.ndarray:
    """(n_queries, n_seconds) scores; NaN where no fused variant has anything."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN seconds
        return np.nanmean([to_seconds(emb, v, q @ emb[v].T) for v in variant.split("+")], axis=0)


def default_variant(emb: dict, has_speech: bool) -> str:
    for v in (["text+frame"] if has_speech else []) + ["caption_ctx+frame", "caption+frame", "frame"]:
        if all(p in emb for p in v.split("+")):
            return v
    return "frame"


def peaks(row: np.ndarray, k: int | None = None) -> list[int]:
    """Greedy peaks on a per-second curve; a flat plateau (window variants) counts once, at its center."""
    row, out = np.nan_to_num(row.astype(float), nan=-1.0), []
    while np.isfinite(row).any() and (k is None or len(out) < k):
        i = int(np.argmax(row))
        lo = hi = i
        while lo > 0 and abs(row[lo - 1] - row[i]) < 1e-6:
            lo -= 1
        while hi < len(row) - 1 and abs(row[hi + 1] - row[i]) < 1e-6:
            hi += 1
        c = (lo + hi) // 2
        out.append(c)
        row[max(0, min(lo, c - NMS_S)):max(hi, c + NMS_S) + 1] = -np.inf
    return out


def fmt(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def search(video: Path, query: str, variant: str | None = None, k: int = 5) -> None:
    from ovu.embedder import encode_queries, load_embedder
    from ovu.transcribe import load_transcript

    emb = load_embeddings(video)
    variant = variant or default_variant(emb, bool(load_transcript(video)["words"]))
    row = per_second(emb, encode_queries(load_embedder(audio=False), [query]), variant)[0]
    print(f"variant: {variant}")
    for t in peaks(row, k):
        print(f"{fmt(t)}  {row[t]:.3f}")


def unit_rank(emb: dict, v: str, row: np.ndarray, intervals: list[list[float]]) -> int:
    s, e = spans(emb, v)
    rel = np.any([np.minimum(e, b) - np.maximum(s, a) >= np.minimum(min(MIN_OVERLAP_S, b - a), e - s) - 1e-6
                  for a, b in intervals], axis=0)
    return int(np.argmax(rel[np.argsort(-row, kind="stable")])) + 1


def second_rank(row: np.ndarray, intervals: list[list[float]]) -> int:
    for r, t in enumerate(peaks(row), 1):
        if any(a - TOL_S <= t + 0.5 <= b + TOL_S for a, b in intervals):
            return r
    return MISS  # never reached: the interval was suppressed by a neighbouring peak


def report(df, variants: list[str], title: str) -> None:
    import pandas as pd

    df["hit@1"], df["hit@3"], df["mrr"] = df["rank"] == 1, df["rank"] <= 3, 1 / df["rank"]
    order = {v: i for i, v in enumerate(variants)}
    tab = lambda g: g.groupby("variant")[["hit@1", "hit@3", "mrr"]].mean().sort_index(key=lambda i: i.map(order))
    types = [t for t in ["speech", "visual", "both", "story"] if (df.type == t).any()]
    wide = pd.concat({t: tab(df[df.type == t]) for t in types} | {"all": tab(df)}, axis=1)
    counts = df[df.variant == variants[0]]["type"].value_counts().to_dict()
    print(f"\n===== {title} =====  (queries: {counts})")
    print(wide.round(2).to_string())


def evaluate(video: Path, queries_file: Path) -> None:
    import pandas as pd

    from ovu.embedder import encode_queries, load_embedder

    emb = load_embeddings(video)
    queries = json.loads(queries_file.read_text())["queries"]
    q = encode_queries(load_embedder(audio=False), [x["q"] for x in queries])
    stored = [v for v in VARIANTS if v in emb]
    fused = stored + [f for f in FUSIONS if all(v in emb for v in f.split("+"))]
    unit, second = [], []
    for v in stored:
        for query, row in zip(queries, q @ emb[v].T):
            unit.append({"variant": v, "type": query["type"], "q": query["q"],
                         "rank": unit_rank(emb, v, row, query["intervals"])})
    for v in fused:
        for query, row in zip(queries, per_second(emb, q, v)):
            second.append({"variant": v, "type": query["type"], "q": query["q"],
                           "rank": second_rank(row, query["intervals"])})
    report(pd.DataFrame(unit), stored, "unit level (own windows / shots / frames / chapters)")
    sec = pd.DataFrame(second)
    report(sec, fused, "second level (peaks on per-second curve, like the GUI)")
    print("\n== second level: rank per query ==")
    ranks = sec.pivot_table(index=["type", "q"], columns="variant", values="rank")[fused].astype(int)
    print(ranks.astype(str).replace(str(MISS), "-").to_string())
