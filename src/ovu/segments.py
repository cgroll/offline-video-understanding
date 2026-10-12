"""Time units the embeddings are computed on, and spreading unit scores to one score per second.

Units: frame (1 s), window (20 s, 10 s stride), shot (content segment, 2-10 s), chapter (story section),
topic chapter (sentences grouped by topic).
"""

import numpy as np

WINDOW_S = 20.0
STRIDE_S = 10.0
SHOT_VARIANTS = ("video_shots", "caption", "caption_ctx")


def windows(total: float, size: float = WINDOW_S, stride: float = STRIDE_S) -> list[tuple[float, float]]:
    """Overlapping fixed-length windows covering the whole video (last one is clipped to the end)."""
    starts = np.arange(0, max(total - size, 0) + stride, stride)
    return [(float(s), float(min(s + size, total))) for s in starts if s < total]


def window_text(words: list[dict], start: float, end: float) -> str:
    return " ".join(w["word"] for w in words if start <= w["t"] < end)


def shots(cuts: list[float], frame_emb: np.ndarray, total: float, sim_threshold: float = 0.85,
          min_len: int = 2, max_len: int = 10) -> list[tuple[float, float]]:
    """Content segments at 1 s resolution.

    Boundaries = hard cuts (rounded to the second) + content changes, i.e. seconds where the frame embedding
    similarity to the previous second drops below `sim_threshold` (catches animated transitions without a cut).
    Segments shorter than `min_len` are merged into their predecessor, longer than `max_len` split evenly.
    """
    n = len(frame_emb)
    sim = (frame_emb[:-1] * frame_emb[1:]).sum(1)
    bounds = {round(c) for c in cuts} | {t + 1 for t in np.flatnonzero(sim < sim_threshold)}
    bounds = sorted(b for b in bounds if 0 < b < n)
    segs = []
    for a, b in zip([0] + bounds, bounds + [n]):
        if segs and (b - a < min_len or segs[-1][1] - segs[-1][0] < min_len):
            segs[-1] = (segs[-1][0], b)
        else:
            segs.append((a, b))
    out = []
    for a, b in segs:
        k = int(np.ceil((b - a) / max_len))
        edges = np.round(np.linspace(a, b, k + 1)).astype(int)
        out += [(float(x), float(min(y, total))) for x, y in zip(edges[:-1], edges[1:])]
    return out


def spans(emb: dict, variant: str) -> tuple[np.ndarray, np.ndarray]:
    """Start/end seconds of the units a stored variant has one vector for."""
    if variant == "frame":
        n = len(emb["frame"])
        return np.arange(n, dtype=float), np.arange(n, dtype=float) + 1
    if variant in SHOT_VARIANTS:
        return emb["shot_starts"], emb["shot_ends"]
    if variant == "chapter":
        return emb["chapter_starts"], emb["chapter_ends"]
    if variant == "topic":
        return emb["topic_starts"], emb["topic_ends"]
    return emb["starts"], emb["ends"]


def to_seconds(emb: dict, variant: str, sims: np.ndarray) -> np.ndarray:
    """Spread unit scores (..., n_units) to one score per second (mean of the units covering that second).

    Units with a zero vector (text windows without speech) don't count; seconds without any valid unit are NaN.
    """
    if variant == "frame":
        return sims
    secs = np.arange(len(emb["frame"])) + 0.5
    s, e = spans(emb, variant)
    valid = np.any(emb[variant] != 0, axis=1)
    cover = ((secs >= s[:, None]) & (secs < e[:, None]) & valid[:, None]).astype(np.float32)
    n = cover.sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, (sims @ cover) / n, np.nan)
