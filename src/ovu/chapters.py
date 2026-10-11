"""Group scene descriptions into chapters and summarize the whole video bottom-up (text-only, local VLM).

Input: captions_ctx.json (or captions.json). Two text-only calls:
  1. chapters: all scene descriptions with timestamps -> 6-20 contiguous chapters with title + summary;
     boundaries are snapped to scene boundaries and made gap-free afterwards
  2. summary: video title + chapters -> overall summary (plot, characters, themes)

Writes chapters.json: {"source", "language", "summary": {plot, characters, themes},
"chapters": [{start, end, title, summary}], raw answers}. Texts are in the output language (see ovu.language).
"""

import json
import time
from pathlib import Path

import numpy as np

from ovu import language
from ovu.paths import out_dir
from ovu.vlm import generate, load_json, load_vlm

CHAPTER_PROMPT = """Video title: {title}

Below are descriptions of all scenes of a video in chronological order, each with start and end second.
The descriptions come from an image model and may contain individual errors.

{scenes}

Divide the video into 6 to 20 contiguous chapters (sections of content). The chapters must follow each other without
gaps and cover the whole video. Give times in seconds, at scene boundaries. Write all text values in {language}.
Answer only with JSON in this format (start/end as numbers):
{{"chapters": [{{"start": start_second, "end": end_second, "title": "short title",
               "summary": "2-3 sentences: what happens"}}]}}"""

SUMMARY_PROMPT = """Video title: {title}

Chapters of the video:
{chapters}

Summarize the whole video. Write all text values in {language}. Answer only with JSON in this format:
{{"plot": "5-8 sentences on the course of events, with beginning, turning points and end",
 "characters": ["character: role in the story"],
 "themes": ["central themes/moods"]}}"""


def fmt(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def clean_chapters(chapters: list[dict], bounds: np.ndarray, total: float) -> list[dict]:
    """Snap starts to the nearest scene boundary, sort, drop duplicates; each chapter ends where the next begins."""
    out = []
    for c in sorted(chapters, key=lambda c: float(c.get("start", 0))):
        start = float(bounds[np.argmin(np.abs(bounds - float(c.get("start", 0))))])
        if out and start <= out[-1]["start"]:
            continue
        out.append({"start": start, "title": str(c.get("title", "")).strip(),
                    "summary": str(c.get("summary", "")).strip()})
    if out:
        out[0]["start"] = 0.0
    for a, b in zip(out, out[1:] + [{"start": total}]):
        a["end"] = b["start"]
    return [{"start": c["start"], "end": c["end"], "title": c["title"], "summary": c["summary"]} for c in out]


def run(video: Path, force: bool = False, vlm=None, lang: str | None = None) -> None:
    d = out_dir(video)
    path = d / "chapters.json"
    if path.exists() and not force:
        print(f"{path} exists (use --force)")
        return
    code = language.output_language(video, lang)
    cap_file = next(p for p in [d / "captions_ctx.json", d / "captions.json"] if p.exists())
    captions = json.loads(cap_file.read_text())
    total = json.loads((d / "transcript.json").read_text())["duration"]
    bounds = np.array([c["start"] for c in captions] + [total])

    lines = []
    for c in captions:
        text = f" (on-screen text: {c['on_screen_text']})" if c["on_screen_text"] else ""
        lines.append(f"[{int(c['start'])}-{int(c['end'])}] {c['description']}{text}".replace("\n", " / "))

    t0 = time.time()
    model, processor = vlm or load_vlm()
    raw_ch = generate(model, processor, [{"type": "text", "text": CHAPTER_PROMPT.format(
        title=video.stem, scenes="\n".join(lines), language=language.name(code))}], max_new_tokens=3000)
    chapters = clean_chapters(load_json(raw_ch).get("chapters", []), bounds, total)
    print(f"{len(chapters)} chapters in {time.time() - t0:.0f}s")

    ch_text = "\n".join(f"[{fmt(c['start'])}-{fmt(c['end'])}] {c['title']}: {c['summary']}" for c in chapters)
    raw_sum = generate(model, processor, [{"type": "text", "text": SUMMARY_PROMPT.format(
        title=video.stem, chapters=ch_text, language=language.name(code))}], max_new_tokens=800)
    path.write_text(json.dumps({"source": cap_file.name, "language": code, "summary": load_json(raw_sum),
                                "chapters": chapters, "raw_chapters": raw_ch, "raw_summary": raw_sum},
                               ensure_ascii=False, indent=1))
    print(f"done in {time.time() - t0:.0f}s -> {path}\n\n{ch_text}")
