"""Topic chapters: split transcript sentences into contiguous chapters by their embeddings (no VLM).

For every k, the optimal split into k contiguous chapters minimizes the sum over chapters of
n * (1 - mean pairwise cosine similarity inside the chapter), computed exactly by dynamic programming over the
self-similarity matrix. The k with the highest mean silhouette (cosine distance) is kept.
"""

import numpy as np

MIN_SENTENCES = 4
MAX_CHAPTERS = 40


def _costs(sim: np.ndarray) -> np.ndarray:
    """cost[a, b] for the chapter of units a..b-1 (inf where b <= a)."""
    n = len(sim)
    c = np.zeros((n + 1, n + 1))
    c[1:, 1:] = sim.cumsum(0).cumsum(1)
    a, b = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
    block = c[b, b] - c[a, b] - c[b, a] + c[a, a]  # sum of sim[a:b, a:b]
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > a, (b - a) - block / np.maximum(b - a, 1), np.inf)


def _all_splits(sim: np.ndarray, k_max: int) -> dict[int, list[int]]:
    """k -> chapter start indices (first is 0) of the optimal split into k chapters, for k = 1..k_max."""
    n, cost = len(sim), _costs(sim)
    best = np.full((k_max + 1, n + 1), np.inf)
    arg = np.zeros((k_max + 1, n + 1), dtype=int)
    best[0, 0] = 0
    for k in range(1, k_max + 1):
        total = best[k - 1][:, None] + cost  # [previous end a, new end b]
        arg[k] = total.argmin(0)
        best[k] = total[arg[k], np.arange(n + 1)]
    out = {}
    for k in range(1, k_max + 1):
        starts, b = [], n
        for j in range(k, 0, -1):
            b = arg[j, b]
            starts.append(int(b))
        out[k] = starts[::-1]
    return out


def silhouette(dist: np.ndarray, labels: np.ndarray) -> float:
    """Mean silhouette for a precomputed distance matrix; a unit alone in its cluster scores 0."""
    ids = np.unique(labels)
    onehot = (labels[:, None] == ids[None, :]).astype(float)
    sizes = onehot.sum(0)
    sums = dist @ onehot  # distance of each unit to all members of each cluster
    own = labels[:, None] == ids[None, :]
    own_size = sizes[np.searchsorted(ids, labels)]
    a = sums[own] / np.maximum(own_size - 1, 1)
    b = np.where(own, np.inf, sums / sizes).min(1)
    s = np.where(own_size > 1, (b - a) / np.maximum(a, b), 0.0)
    return float(s.mean())


def segment(emb: np.ndarray) -> list[int]:
    """Start indices of the topic chapters for L2-normalized unit embeddings (first start is 0)."""
    n = len(emb)
    sim = emb @ emb.T
    dist = np.clip(1 - sim, 0, None)
    np.fill_diagonal(dist, 0)
    k_max = max(2, min(MAX_CHAPTERS, n // 2))
    splits = _all_splits(sim, k_max)

    def score(starts):
        labels = np.zeros(n, dtype=int)
        for s in starts[1:]:
            labels[s:] += 1
        return silhouette(dist, labels)

    return splits[max(range(2, k_max + 1), key=lambda k: score(splits[k]))]


def spans(starts: list[int], unit_starts: np.ndarray, duration: float) -> tuple[np.ndarray, np.ndarray]:
    """Gap-free chapter spans in seconds: the first chapter starts at 0, the last ends at the duration."""
    s = np.array([0.0] + [float(unit_starts[i]) for i in starts[1:]])
    return s, np.append(s[1:], duration)
