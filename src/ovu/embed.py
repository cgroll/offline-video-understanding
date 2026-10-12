"""Embed a video with EmbeddingGemma 2, one vector per time unit and variant (all in embeddings.npz).

Variants:
  text         transcript words inside a 20 s window ("title: none | text: ..."; zero vector if no speech)
  video        frames of a 20 s window at 1 fps (140 soft tokens per frame)
  audio        raw 16 kHz mono waveform of a 20 s window
  video_audio  frames + waveform in one input
  text_video   transcript + frames in one input
  frame        one vector per second: the single frame at that second as an image
  video_shots  frames of content segments (needs `frame`): split at hard cuts and at frame-embedding drops, short
               segments merged, long ones split to <= 10 s; spans in shot_starts/shot_ends
  caption      VLM scene descriptions (captions.json) embedded as text, same spans as video_shots
  caption_ctx  same for the descriptions with context (captions_ctx.json)
  chapter      chapter title + summary (chapters.json); spans in chapter_starts/chapter_ends
  topic        transcript text of each topic chapter (ovu.topics: sentences split by their embeddings, no VLM);
               spans in topic_starts/topic_ends; only for videos with speech
Window spans are stored as starts/ends, the window transcripts as texts.
"""

import json
import time
from pathlib import Path

import numpy as np

from ovu.embedder import DIM, as_document, load_embedder
from ovu.media import SAMPLE_RATE, load_audio, load_frames, scene_cuts
from ovu.paths import out_dir
from ovu.segments import shots, window_text, windows
from ovu.topics import MIN_SENTENCES, segment, spans
from ovu.transcribe import load_transcript

WINDOW_VARIANTS = ["text", "video", "audio", "video_audio", "text_video"]
VARIANTS = WINDOW_VARIANTS + ["frame", "video_shots", "caption", "caption_ctx", "chapter", "topic"]
FRAME_VARIANTS = ["frame", "video_shots", "video", "video_audio", "text_video"]
CAPTION_FILES = {"caption": "captions.json", "caption_ctx": "captions_ctx.json"}


def caption_text(c: dict) -> str:
    parts = [c["description"]]
    if c["on_screen_text"]:
        parts.append(f"On-screen text: {c['on_screen_text']}")
    if c["keywords"]:
        parts.append("Keywords: " + ", ".join(c["keywords"]))
    return " ".join(parts)


def load_embeddings(video: Path) -> dict:
    return dict(np.load(out_dir(video) / "embeddings.npz"))


def available(video: Path) -> list[str]:
    """Variants whose inputs exist (VLM outputs are optional, topic chapters need speech)."""
    d = out_dir(video)
    speech = len(sentences(load_transcript(video))) >= MIN_SENTENCES
    return [v for v in VARIANTS if (v not in CAPTION_FILES or (d / CAPTION_FILES[v]).exists())
            and (v != "chapter" or (d / "chapters.json").exists()) and (v != "topic" or speech)]


def sentences(transcript: dict) -> list[dict]:
    return [s for s in transcript["segments"] if s["text"].strip()]


def run(video: Path, variants: list[str] | None = None, force: bool = False) -> None:
    """Compute the given variants (default: all available); --force recomputes them, other variants are kept."""
    import torch
    from PIL import Image
    from tqdm import tqdm

    d = out_dir(video)
    out = d / "embeddings.npz"
    old = dict(np.load(out)) if out.exists() else {}
    variants = [v for v in (variants or available(video)) if force or v not in old]
    if not variants:
        print("embeddings: nothing to do")
        return
    if "video_shots" in variants and "frame" not in variants and "frame" not in old:
        variants.insert(0, "frame")

    transcript = load_transcript(video)
    wins = windows(transcript["duration"])
    texts = [window_text(transcript["words"], s, e) for s, e in wins]
    frames = load_frames(video) if any(v in FRAME_VARIANTS for v in variants) else None
    audio = load_audio(video) if any("audio" in v for v in variants) else None
    model = load_embedder(audio=audio is not None)

    def clip(s, e):
        return frames[int(s):max(int(np.ceil(e)), int(s) + 1)]

    def wave(s, e):
        return audio[int(s * SAMPLE_RATE):int(e * SAMPLE_RATE)]

    inputs = {
        "text": lambda s, e, t: as_document(t) if t else None,
        "video": lambda s, e, t: {"text": "<|video|>", "video": clip(s, e)},
        "audio": lambda s, e, t: {"text": "<|audio|>", "audio": wave(s, e)},
        "video_audio": lambda s, e, t: {"text": "<|video|><|audio|>", "video": clip(s, e), "audio": wave(s, e)},
        "text_video": lambda s, e, t: {"text": as_document(t) + " <|video|>", "video": clip(s, e)},
    }

    result = {}
    with torch.inference_mode():
        if "frame" in variants:
            t0 = time.time()
            vecs = [model.encode({"text": "<|image|>", "image": [Image.fromarray(f)]}, normalize_embeddings=True)
                    for f in tqdm(frames, desc="frame")]
            result["frame"] = np.vstack(vecs).astype(np.float32)
            print(f"frame: {len(vecs)} frames in {time.time() - t0:.1f}s")
        if "video_shots" in variants:
            t0 = time.time()
            cuts = scene_cuts(video)
            segs = shots(cuts, result.get("frame", old.get("frame")), transcript["duration"])
            vecs = [model.encode({"text": "<|video|>", "video": clip(s, e)}, normalize_embeddings=True)
                    for s, e in tqdm(segs, desc="video_shots")]
            result |= {"video_shots": np.vstack(vecs).astype(np.float32), "scene_cuts": np.array(cuts),
                       "shot_starts": np.array([s for s, _ in segs]), "shot_ends": np.array([e for _, e in segs])}
            print(f"video_shots: {len(segs)} segments from {len(cuts)} hard cuts in {time.time() - t0:.1f}s")
        for v, file in CAPTION_FILES.items():
            if v in variants:
                captions = json.loads((d / file).read_text())
                result[v] = model.encode([as_document(caption_text(c)) for c in captions],
                                         normalize_embeddings=True).astype(np.float32)
                print(f"{v}: {len(captions)} scene descriptions")
        if "chapter" in variants:
            chapters = json.loads((d / "chapters.json").read_text())["chapters"]
            result["chapter"] = model.encode([as_document(c["summary"], c["title"]) for c in chapters],
                                             normalize_embeddings=True).astype(np.float32)
            result |= {"chapter_starts": np.array([c["start"] for c in chapters]),
                       "chapter_ends": np.array([c["end"] for c in chapters])}
            print(f"chapter: {len(chapters)} chapters")
        if "topic" in variants:
            t0 = time.time()
            sents = sentences(transcript)
            sent_emb = model.encode([as_document(s["text"]) for s in sents], normalize_embeddings=True)
            starts = segment(sent_emb)
            ts, te = spans(starts, np.array([s["start"] for s in sents]), transcript["duration"])
            texts_ch = [" ".join(s["text"] for s in sents[a:b]) for a, b in zip(starts, starts[1:] + [len(sents)])]
            result |= {"topic": model.encode([as_document(t) for t in texts_ch], normalize_embeddings=True)
                       .astype(np.float32), "topic_starts": ts, "topic_ends": te}
            print(f"topic: {len(starts)} chapters from {len(sents)} sentences in {time.time() - t0:.1f}s")
        for v in [v for v in variants if v in WINDOW_VARIANTS]:
            t0 = time.time()
            vecs = []
            for (s, e), t in tqdm(list(zip(wins, texts)), desc=v):
                inp = inputs[v](s, e, t)
                vecs.append(np.zeros(DIM, np.float32) if inp is None else model.encode(inp, normalize_embeddings=True))
            result[v] = np.vstack(vecs).astype(np.float32)
            print(f"{v}: {len(vecs)} windows in {time.time() - t0:.1f}s")

    np.savez(out, **{**old, **result, "starts": np.array([s for s, _ in wins]), "ends": np.array([e for _, e in wins]),
                     "texts": np.array(texts)})
    print(f"-> {out}")
