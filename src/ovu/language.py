"""Output language of the model-generated texts (scene descriptions, chapters, summaries, reports).

The transcript always stays in the spoken language. Generated texts use, in this order:
  1. a language given by the user (`--language de` or `--language German`)
  2. the language stored in the project's project.json (from an earlier run)
  3. detected: the language of the transcript if it has enough words, else of the project title, else English
The choice is stored in project.json so that all steps of a project use the same language. Choosing a different
language explicitly deletes the generated texts (and their embeddings), so no project mixes languages.
"""

import json
from pathlib import Path

import numpy as np

from ovu.paths import load_project, out_dir, title, update_project

MIN_WORDS = 20
FALLBACK = "en"
GENERATED_FILES = ["captions.json", "captions_ctx.json", "summary.json", "chapters.json", "report.pdf"]
GENERATED_EMBEDDINGS = ["caption", "caption_ctx", "chapter", "chapter_starts", "chapter_ends"]


def _detector():
    from lingua import LanguageDetectorBuilder

    return LanguageDetectorBuilder.from_all_languages().build()


def normalize(lang: str) -> str:
    """ISO 639-1 code from a code or an English language name ('de', 'German' -> 'de')."""
    from lingua import IsoCode639_1, Language

    try:
        return Language.from_iso_code_639_1(IsoCode639_1.from_str(lang.lower())).iso_code_639_1.name.lower()
    except ValueError:
        try:
            return Language.from_str(lang).iso_code_639_1.name.lower()
        except ValueError:
            raise SystemExit(f"unknown language '{lang}'; use an ISO 639-1 code like de, en, fr") from None


def name(code: str) -> str:
    """English name for prompts ('de' -> 'German')."""
    from lingua import IsoCode639_1, Language

    return Language.from_iso_code_639_1(IsoCode639_1.from_str(code)).name.title()


def detect(video: Path) -> tuple[str, str]:
    """(code, source) with source in transcript | title | fallback."""
    t = out_dir(video) / "transcript.json"
    words = [w["word"] for w in json.loads(t.read_text())["words"]] if t.exists() else []
    candidates = ([("transcript", " ".join(words))] if len(words) >= MIN_WORDS else []) + [("title", title(video))]
    detector = _detector()
    for source, text in candidates:
        lang = detector.detect_language_of(text)
        if lang is not None:
            return lang.iso_code_639_1.name.lower(), source
    return FALLBACK, "fallback"


def invalidate_generated(video: Path) -> None:
    """Delete generated texts, reports and their embeddings (transcript and visual embeddings are kept)."""
    d = out_dir(video)
    for f in GENERATED_FILES:
        (d / f).unlink(missing_ok=True)
    npz = d / "embeddings.npz"
    if npz.exists():
        emb = dict(np.load(npz))
        if any(k in emb for k in GENERATED_EMBEDDINGS):
            np.savez(npz, **{k: v for k, v in emb.items() if k not in GENERATED_EMBEDDINGS})


def output_language(video: Path, override: str | None = None) -> str:
    """Language code for generated texts; resolves and stores it in project.json on first use."""
    d = out_dir(video)
    stored = load_project(d).get("language")
    if override:
        code, source = normalize(override), "user"
        if code == stored:
            return code
        if stored:
            print(f"output language changes from {name(stored)} to {name(code)}: deleting generated texts")
            invalidate_generated(video)
    elif stored:
        return stored
    else:
        code, source = detect(video)
    update_project(d, language=code, language_source=source)
    print(f"output language: {name(code)} ({source})")
    return code
