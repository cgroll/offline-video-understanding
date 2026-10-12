"""Project layout: one directory per video, data/projects/<name>/, holding the video file, project.json, all results,
the eval set (eval.json) and reports. The data root can be overridden with the OVU_HOME environment variable.

Pipeline steps take the video path; its project directory is the video's parent directory.
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("OVU_HOME", Path(__file__).resolve().parents[2]))
PROJECTS = ROOT / "data" / "projects"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def out_dir(video: Path) -> Path:
    return video.parent


def project_name(video: Path) -> str:
    return video.parent.name


def eval_file(video: Path) -> Path:
    return video.parent / "eval.json"


def load_project(d: Path) -> dict:
    p = d / "project.json"
    return json.loads(p.read_text()) if p.exists() else {}


def update_project(d: Path, **fields) -> dict:
    data = load_project(d) | fields
    (d / "project.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    return data


def title(video: Path) -> str:
    """Title used as metadata in prompts and reports (default: the video file stem)."""
    return load_project(video.parent).get("title") or video.stem


def list_projects() -> list[Path]:
    return sorted(d for d in PROJECTS.glob("*") if (d / "project.json").exists())


def video_of(d: Path) -> Path:
    return d / load_project(d)["video"]


def resolve_video(arg: str) -> Path:
    """The video of the project named `arg`, or of the only project whose name contains `arg`."""
    projects = list_projects()
    matches = [d for d in projects if d.name == arg] or [d for d in projects if arg in d.name]
    if len(matches) == 1:
        return video_of(matches[0])
    names = "\n  ".join(d.name for d in (matches or projects)) or "(none, create one with `ovu new`)"
    raise SystemExit(f"{'ambiguous' if matches else 'no'} project for '{arg}'; projects:\n  {names}")


def new_project_dir(name: str) -> Path:
    if not NAME_RE.match(name):
        raise SystemExit(f"invalid project name '{name}': use lower-case letters, digits and '-'")
    d = PROJECTS / name
    if d.exists():
        raise SystemExit(f"project '{name}' already exists: {d}")
    return d
