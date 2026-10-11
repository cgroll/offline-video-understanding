"""Describe each scene (video_shots segment) with the local VLM; answers are JSON, visual content only.

Plain mode -> captions.json: per scene 3 frames (start, middle, end; 960x540), no context.

Context mode (hierarchical captioning) -> summary.json + captions_ctx.json:
  1. once per video: a storyboard of 40 evenly spaced frames + the video title -> global summary (characters with
     fixed names, recurring objects, places, plot)
  2. per scene: all frames of the scene as video input (1 fps, 640x360) + the global summary + the previous scene's
     description as text context; the model is told to describe only the current scene.
     Near-empty scenes (black / uniform frames) are described without context, since the model otherwise fills them
     with the story from the summary.

Captions: [{start, end, description, on_screen_text, shot_type, keywords, raw}], written in the output language
(see ovu.language). Resumable: done scenes are skipped.
Prompts must stay generic: no examples or hints taken from a specific video.
"""

import json
import time
from pathlib import Path

import numpy as np

from ovu import language
from ovu.media import load_frames
from ovu.paths import out_dir
from ovu.vlm import as_text, generate, load_json, load_vlm

W, H = 960, 540
STORYBOARD_N = 40
EMPTY_STD = 12  # grey-level std below this: frame is (nearly) uniform, e.g. black

PROMPT = """The three images are from the same scene of a video (beginning, middle, end).
Describe the scene as a whole (not image by image) and only what is actually visible; do not invent anything and
name people only if their name is shown in the image. Write all text values in {language}.
Answer only with JSON in this format:
{{"description": "1-3 sentences: setting, people or characters, objects, what happens",
 "on_screen_text": "text shown or visible in the image, verbatim, each text only once; otherwise empty",
 "shot_type": "kind of footage in 1-3 words",
 "keywords": ["5-10 keywords"]}}"""

SUMMARY_PROMPT = """Video title: {title}

The images are a storyboard: single frames spread evenly over the whole video, in chronological order. Summarize the
video so that its scenes can afterwards be described consistently. Use the title as a hint for topic and characters,
but describe only what the images support. Write all text values in {language}.
Answer only with JSON in this format:
{{"genre": "kind/genre of the video in a few words",
 "characters": [{{"name": "short, unambiguous label used for all scenes", "appearance": "how to recognize them"}}],
 "objects": ["recurring important objects with a distinguishing feature"],
 "places": ["recurring places/settings"],
 "plot": "3-6 sentences on the course of events"}}"""

CTX_PROMPT = """Context for the whole video (for orientation only, do not retell it):
{summary}

Previous scene: {previous}

The video above is the current scene ({start}-{end} s). Describe only what is visible and happens in this scene, as a
whole and in chronological order. Use the labels from the context for characters, objects and places when they are
clearly visible in this scene. Do not take anything from the context that is not visible in this scene; if the image
is empty, black or nothing is recognizable, say exactly that. Write all text values in {language}.
Answer only with JSON in this format:
{{"description": "1-3 sentences: who/what is visible, where, what happens",
 "on_screen_text": "text shown or visible in the image, verbatim, each text only once; otherwise empty",
 "shot_type": "kind of footage in 1-3 words",
 "keywords": ["5-10 keywords"]}}"""


def parse(raw: str) -> dict:
    d = load_json(raw)
    return {"description": as_text(d.get("description", raw if not d else "")),
            "on_screen_text": as_text(d.get("on_screen_text")),
            "shot_type": as_text(d.get("shot_type")),
            "keywords": [str(x) for x in d.get("keywords", []) or []]}


def is_empty(clip: np.ndarray) -> bool:
    """All frames nearly uniform (black screen, fade, plain colour)."""
    return all(f.mean(axis=2).std() < EMPTY_STD for f in clip)


def describe(model, processor, images, lang: str) -> str:
    return generate(model, processor, [*({"type": "image", "image": im} for im in images),
                                       {"type": "text", "text": PROMPT.format(language=lang)}])


def summarize(model, processor, frames: np.ndarray, title: str, lang: str) -> str:
    from PIL import Image

    idx = np.linspace(0, len(frames) - 1, STORYBOARD_N).round().astype(int)
    board = [Image.fromarray(frames[i]).resize((448, 252)) for i in idx]
    return generate(model, processor, [*({"type": "image", "image": im} for im in board),
                                       {"type": "text", "text": SUMMARY_PROMPT.format(title=title, language=lang)}],
                    max_new_tokens=700)


def describe_ctx(model, processor, clip: np.ndarray, summary: str, previous: str, s: float, e: float,
                 lang: str) -> str:
    from transformers.video_utils import VideoMetadata

    clip = clip if len(clip) % 2 == 0 else np.concatenate([clip, clip[-1:]])  # temporal patches pair up frames
    meta = VideoMetadata(total_num_frames=len(clip), fps=1.0, duration=float(len(clip)),
                         frames_indices=list(range(len(clip))))
    prompt = CTX_PROMPT.format(summary=summary, previous=previous or "(none, this is the first scene)",
                               start=int(s), end=int(e), language=lang)
    return generate(model, processor, [{"type": "video", "video": clip}, {"type": "text", "text": prompt}],
                    video_metadata=[meta], do_sample_frames=False)


def run(video: Path, context: bool = False, force: bool = False, vlm=None, lang: str | None = None) -> None:
    import torch
    from PIL import Image
    from tqdm import tqdm

    d = out_dir(video)
    emb = np.load(d / "embeddings.npz")
    segs = list(zip(emb["shot_starts"].tolist(), emb["shot_ends"].tolist()))
    path = d / ("captions_ctx.json" if context else "captions.json")
    done = {} if force or not path.exists() else {(c["start"], c["end"]): c for c in json.loads(path.read_text())}
    if not force and all(s in done for s in segs):
        print(f"{path.name}: all {len(segs)} scenes done (use --force)")
        return

    lang = language.name(language.output_language(video, lang))
    frames = load_frames(video) if context else load_frames(video, W, H)
    model, processor = vlm or load_vlm()
    t0, captions = time.time(), []
    summary = ""
    if context:
        spath = d / "summary.json"
        if force or not spath.exists():
            spath.write_text(summarize(model, processor, frames, video.stem, lang))
            print(f"summary in {time.time() - t0:.0f}s -> {spath}")
        summary = spath.read_text().strip()
    previous = ""
    for s, e in tqdm(segs, desc=path.stem):
        if (s, e) not in done:
            clip = frames[int(s):max(int(np.ceil(e)), int(s) + 1)]
            if context and not is_empty(clip):
                raw = describe_ctx(model, processor, clip, summary, previous, s, e, lang)
            else:
                idx = sorted({int(s), int((s + e) / 2), max(int(s), int(np.ceil(e)) - 1)})
                raw = describe(model, processor, [Image.fromarray(frames[min(i, len(frames) - 1)]) for i in idx],
                               lang)
            done[(s, e)] = {"start": s, "end": e, **parse(raw), "raw": raw}
            path.write_text(json.dumps([done[k] for k in sorted(done)], ensure_ascii=False, indent=1))
        captions.append(done[(s, e)])
        previous = done[(s, e)]["description"]
    path.write_text(json.dumps(captions, ensure_ascii=False, indent=1))
    print(f"{len(captions)} scenes in {time.time() - t0:.0f}s, "
          f"peak VRAM {torch.cuda.max_memory_allocated() / 1e9:.1f} GB -> {path}")
