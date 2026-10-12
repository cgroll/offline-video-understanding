"""Download a video (e.g. YouTube) into a project directory with yt-dlp.

YouTube often refuses anonymous downloads ("This video is not available"). What made it work locally:
browser cookies (`--cookies-from-browser`, needs the secretstorage module on Linux to decrypt Chrome cookies) and a
JavaScript runtime for YouTube's challenges (node; yt-dlp only enables deno by default).
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run(url: str, dest: Path, cookies_from: str | None = None, max_height: int = 1080) -> Path:
    """Download into `dest` (created if needed) and return the video file."""
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "yt_dlp", "-f", f"bv*[height<={max_height}]+ba/b", "--merge-output-format", "mp4",
           "-o", str(dest / "%(title)s.%(ext)s"), "--print", "after_move:filepath", "--no-simulate"]
    if shutil.which("node"):
        cmd += ["--js-runtimes", "node"]
    if cookies_from:
        cmd += ["--cookies-from-browser", cookies_from]
    out = subprocess.run(cmd + [url], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(f"yt-dlp failed:\n{out.stderr[-2000:]}\n"
                           "Hint: try --cookies-from chrome (or firefox) if YouTube says the video is not available.")
    path = Path(out.stdout.strip().splitlines()[-1])
    print(f"-> {path}")
    return path
