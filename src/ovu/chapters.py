"""Group scene descriptions into content chapters and summarize the whole video bottom-up (text-only, local VLM).

Input: captions_ctx.json (or captions.json). Text-only calls:
  1. starts: all scene descriptions with timestamps -> chapter starts with short titles (short answer, so it is not
     cut off; a small model tends to make one chapter per scene when it also writes summaries)
  2. per chapter: its scene descriptions -> title + 2-3 sentence summary
  3. summary: video title + chapters -> overall summary (plot, characters, themes)
Chapters are snapped to scene boundaries, made gap-free, merged when shorter than MIN_CHAPTER_S and capped at
MAX_CHAPTERS. Chapters longer than max(SPLIT_MIN_S, duration / SPLIT_FRACTION) are split by running pass 1 again on
their own scenes (a small model tends to stop proposing chapters after the first part of a long input).
If no chapter can be read, nothing is written.

Writes chapters.json: {"source", "language", "summary": {plot, characters, themes},
"chapters": [{start, end, title, summary}], raw answers}. Texts are in the output language (see ovu.language).
"""

import json
import re
import time
from pathlib import Path

import numpy as np

from ovu import language
from ovu.paths import out_dir, title
from ovu.vlm import generate, load_json, load_vlm

MIN_CHAPTER_S = 20
MAX_CHAPTERS = 20
SPLIT_MIN_S = 120
SPLIT_FRACTION = 8
SPLIT_ROUNDS = 3

STARTS_PROMPT = """Video title: {title}

Below are descriptions of {which} in chronological order, each with start and end second.
The descriptions come from an image model and may contain individual errors.

{scenes}

Divide {part} into {n_chapters} chapters by content: each chapter is a coherent section of the story or topic and
usually spans many scenes; a chapter should last at least {min_len} seconds. Give for each chapter only its start
second (a scene start) and a short title in {language}.
Answer only with JSON in this format (start as a number):
{{"chapters": [{{"start": start_second, "title": "short title"}}]}}"""

CHAPTER_PROMPT = """Video title: {title}

Descriptions of the scenes of one chapter ({start}-{end} s) of this video, in chronological order:

{scenes}

Write a short title and a summary of what happens in this chapter, as a whole, in {language}. Do not list the scenes
one by one and do not invent anything that is not in the descriptions.
Answer only with JSON in this format:
{{"title": "short title", "summary": "2-3 sentences"}}"""

SUMMARY_PROMPT = """Video title: {title}

Chapters of the video:
{chapters}

Summarize the whole video. Write all text values in {language}. Answer only with JSON in this format:
{{"plot": "5-8 sentences on the course of events, with beginning, turning points and end",
 "characters": ["character: role in the story"],
 "themes": ["central themes/moods"]}}"""


def fmt(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def parse_chapters(raw: str) -> list[dict]:
    """Chapter entries from the answer; from a truncated answer, every complete {...} entry with a start."""
    entries = load_json(raw).get("chapters")
    if entries is None:
        entries = []
        for m in re.finditer(r"\{[^{}]*\}", raw):
            try:
                entries.append(json.loads(m.group(0)))
            except json.JSONDecodeError:
                pass
    out = []
    for e in entries:
        try:
            out.append({"start": float(e["start"]), "title": str(e.get("title", "")).strip()})
        except (KeyError, TypeError, ValueError):
            pass
    return out


def clean_chapters(chapters: list[dict], bounds: np.ndarray, total: float) -> list[dict]:
    """Snap starts to scene boundaries, sort, dedupe, start at 0, merge short chapters, cap the number."""
    out = []
    for c in sorted(chapters, key=lambda c: c["start"]):
        start = float(bounds[np.argmin(np.abs(bounds - c["start"]))])
        if start >= total or (out and start <= out[-1]["start"]):
            continue
        out.append({"start": start, "title": c["title"]})
    if not out:
        return []
    out[0]["start"] = 0.0

    def ends():
        return [b["start"] for b in out[1:]] + [total]

    while len(out) > 1:
        lengths = [e - c["start"] for c, e in zip(out, ends())]
        i = int(np.argmin(lengths))
        if lengths[i] >= MIN_CHAPTER_S and len(out) <= MAX_CHAPTERS:
            break
        del out[i if i > 0 else 1]  # merge into the previous chapter; the first one absorbs its successor
    return [{"start": c["start"], "end": e, "title": c["title"]} for c, e in zip(out, ends())]


def scene_lines(captions: list[dict], start: float = 0, end: float = float("inf")) -> str:
    lines = []
    for c in captions:
        if start <= c["start"] < end:
            text = f" (on-screen text: {c['on_screen_text']})" if c["on_screen_text"] else ""
            lines.append(f"[{int(c['start'])}-{int(c['end'])}] {c['description']}{text}".replace("\n", " / "))
    return "\n".join(lines)


def run(video: Path, force: bool = False, vlm=None, lang: str | None = None) -> None:
    code = language.output_language(video, lang)  # may delete stale texts, so resolve first
    lang_name = language.name(code)
    d = out_dir(video)
    path = d / "chapters.json"
    if path.exists() and not force:
        print(f"{path} exists (use --force)")
        return
    cap_file = next(p for p in [d / "captions_ctx.json", d / "captions.json"] if p.exists())
    captions = json.loads(cap_file.read_text())
    total = json.loads((d / "transcript.json").read_text())["duration"]
    bounds = np.array([c["start"] for c in captions])

    t0 = time.time()
    model, processor = vlm or load_vlm()
    raw_starts = []

    def propose(start: float, end: float, whole: bool) -> list[dict]:
        prompt = STARTS_PROMPT.format(
            title=title(video), scenes=scene_lines(captions, start, end), language=lang_name, min_len=MIN_CHAPTER_S,
            which="all scenes of a video" if whole else f"the scenes of one part ({int(start)}-{int(end)} s) of a video",
            part="the video" if whole else "this part", n_chapters="6 to 15" if whole else "2 to 5")
        raw_starts.append(generate(model, processor, [{"type": "text", "text": prompt}], max_new_tokens=800))
        return [c for c in parse_chapters(raw_starts[-1]) if start <= c["start"] < end]

    chapters = clean_chapters(propose(0, total, True), bounds, total)
    if not chapters:
        raise SystemExit(f"no chapters in the model answer (nothing written):\n{raw_starts[-1][:1000]}")
    max_len = max(SPLIT_MIN_S, total / SPLIT_FRACTION)
    for _ in range(SPLIT_ROUNDS):
        long = [c for c in chapters if c["end"] - c["start"] > max_len]
        if not long:
            break
        proposed = [{"start": c["start"], "title": c["title"]} for c in chapters]
        for c in long:
            proposed += propose(c["start"], c["end"], False)
        chapters = clean_chapters(proposed, bounds, total)
    print(f"{len(chapters)} chapters in {time.time() - t0:.0f}s ({len(raw_starts)} segmentation calls)")

    raw_chapters = []
    for c in chapters:
        raw = generate(model, processor, [{"type": "text", "text": CHAPTER_PROMPT.format(
            title=title(video), start=int(c["start"]), end=int(c["end"]), language=lang_name,
            scenes=scene_lines(captions, c["start"], c["end"]))}], max_new_tokens=300)
        ans = load_json(raw)
        c["title"] = str(ans.get("title") or c["title"]).strip()
        c["summary"] = str(ans.get("summary") or "").strip()
        raw_chapters.append(raw)

    ch_text = "\n".join(f"[{fmt(c['start'])}-{fmt(c['end'])}] {c['title']}: {c['summary']}" for c in chapters)
    raw_sum = generate(model, processor, [{"type": "text", "text": SUMMARY_PROMPT.format(
        title=title(video), chapters=ch_text, language=lang_name)}], max_new_tokens=800)
    path.write_text(json.dumps({"source": cap_file.name, "language": code, "summary": load_json(raw_sum),
                                "chapters": chapters, "raw_starts": raw_starts, "raw_chapters": raw_chapters,
                                "raw_summary": raw_sum}, ensure_ascii=False, indent=1))
    print(f"done in {time.time() - t0:.0f}s -> {path}\n\n{ch_text}")
