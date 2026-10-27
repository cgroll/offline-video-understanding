"""ffmpeg-based media access: duration, audio, 1 fps frames, hard scene cuts, thumbnails."""

import re
import subprocess
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16_000
FRAME_W, FRAME_H = 640, 360


def duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def load_audio(video: Path) -> np.ndarray:
    """Mono float32 waveform at 16 kHz."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", str(SAMPLE_RATE),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(bytearray(raw), np.float32)


def extract_wav(video: Path, out_path: Path) -> None:
    """Mono WAV at 16 kHz, written to out_path (for tools that need a file path, e.g. diarization)."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-ac", "1", "-ar", str(SAMPLE_RATE),
                    "-f", "wav", str(out_path)], capture_output=True, check=True)


def load_frames(video: Path, w: int = FRAME_W, h: int = FRAME_H) -> np.ndarray:
    """RGB frames sampled at 1 fps, shape (seconds, h, w, 3); frame i shows second i."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1,scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(bytearray(raw), np.uint8).reshape(-1, h, w, 3)


def scene_cuts(video: Path, threshold: float = 0.3) -> list[float]:
    """Hard cuts: times where ffmpeg's frame-difference scene score exceeds the threshold."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                          f"scale=320:-2,select='gt(scene,{threshold})',metadata=print:file=-", "-an", "-f", "null", "-"],
                         capture_output=True, text=True, check=True, env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"}).stdout
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", out)]


def make_thumbs(video: Path, d: Path) -> None:
    """One small JPEG per second (0000.jpg = second 0) for the GUI."""
    d.mkdir(exist_ok=True)
    if not any(d.iterdir()):
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=1,scale=240:-2", "-q:v", "4",
                        "-start_number", "0", str(d / "%04d.jpg")], check=True)
