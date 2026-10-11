"""Project layout: videos in data/videos, results per video in data/processed/<slug>, eval queries in eval/<slug>.json.

The project root can be overridden with the OVU_HOME environment variable.
"""

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("OVU_HOME", Path(__file__).resolve().parents[2]))
VIDEOS = ROOT / "data" / "videos"
PROCESSED = ROOT / "data" / "processed"
EVAL = ROOT / "eval"
VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov"}


def slug(video: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", video.stem.lower()).strip("-")


def out_dir(video: Path) -> Path:
    d = PROCESSED / slug(video)
    d.mkdir(parents=True, exist_ok=True)
    return d


def eval_file(video: Path) -> Path:
    return EVAL / f"{slug(video)}.json"


def list_videos() -> list[Path]:
    return sorted(p for p in VIDEOS.glob("*") if p.suffix.lower() in VIDEO_EXT)


def resolve_video(arg: str) -> Path:
    """A path to a video file, or a (partial) slug / name of a video in data/videos."""
    p = Path(arg).expanduser()
    if p.is_file():
        return p.resolve()
    key = slug(Path(arg + ".x"))
    matches = [v for v in list_videos() if key in slug(v)]
    if len(matches) == 1:
        return matches[0]
    found = "\n  ".join(slug(v) for v in (matches or list_videos())) or "(none)"
    raise SystemExit(f"{'ambiguous' if matches else 'no'} video for '{arg}'; candidates:\n  {found}")
