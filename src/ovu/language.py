"""Output language of the model-generated texts (scene descriptions, chapters, summaries).

The transcript always stays in the spoken language. Generated texts use, in this order:
  1. a language given by the user (`--language de` or `--language German`)
  2. the language stored for the video in meta.json (from an earlier run)
  3. detected: the language of the transcript if it has enough words, else of the video title, else English
The choice is stored in meta.json so that all steps of a video use the same language.
"""

import json
from pathlib import Path

from ovu.paths import out_dir

MIN_WORDS = 20
FALLBACK = "en"


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
    candidates = ([("transcript", " ".join(words))] if len(words) >= MIN_WORDS else []) + [("title", video.stem)]
    detector = _detector()
    for source, text in candidates:
        lang = detector.detect_language_of(text)
        if lang is not None:
            return lang.iso_code_639_1.name.lower(), source
    return FALLBACK, "fallback"


def output_language(video: Path, override: str | None = None) -> str:
    """Language code for generated texts; resolves and stores it in meta.json on first use."""
    path = out_dir(video) / "meta.json"
    meta = json.loads(path.read_text()) if path.exists() else {}
    if override:
        code, source = normalize(override), "user"
    elif "language" in meta:
        return meta["language"]
    else:
        code, source = detect(video)
    meta |= {"language": code, "language_source": source}
    path.write_text(json.dumps(meta, indent=1))
    print(f"output language: {name(code)} ({source})")
    return code
