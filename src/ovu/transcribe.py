"""Speech to text with Parakeet TDT 0.6B v3 (onnx-asr, int8, CPU) + Silero VAD, plus speaker diarization
(Sortformer, GPU, see diarize.py).

Writes transcript.json with
  segments: [{start, end, text, speaker}]  VAD speech segments; speaker is "SPEAKER_00".."SPEAKER_03" or null
  words:    [{t, word}]                    word start times (absolute seconds), from token timestamps
"""

import json
import tempfile
import time
from pathlib import Path

from ovu.media import SAMPLE_RATE, duration, extract_wav, load_audio
from ovu.paths import out_dir

MODEL = "nemo-parakeet-tdt-0.6b-v3"


def to_words(start: float, tokens: list[str], stamps: list[float]) -> list[dict]:
    """Merge sentencepiece tokens into words; a leading space starts a new word."""
    words = []
    for tok, t in zip(tokens, stamps):
        if tok.startswith(" ") or not words:
            words.append({"t": round(start + t, 2), "word": tok.strip()})
        else:
            words[-1]["word"] += tok
    return [w for w in words if w["word"]]


def load_transcript(video: Path) -> dict:
    return json.loads((out_dir(video) / "transcript.json").read_text())


def run(video: Path, force: bool = False) -> None:
    import onnx_asr

    out = out_dir(video) / "transcript.json"
    if out.exists() and not force:
        print(f"{out} exists (use --force)")
        return

    t0 = time.time()
    model = onnx_asr.load_model(MODEL, quantization="int8")
    vad = onnx_asr.load_vad("silero")
    audio = load_audio(video)

    segments, words = [], []
    for r in model.with_vad(vad).with_timestamps().recognize(audio, sample_rate=SAMPLE_RATE):
        segments.append({"start": round(r.start, 2), "end": round(r.end, 2), "text": r.text.strip()})
        words += to_words(r.start, r.tokens or [], r.timestamps or [])

    diarize_speakers(segments, video)

    out.write_text(json.dumps({"video": video.name, "duration": duration(video), "model": MODEL,
                               "segments": segments, "words": words}, ensure_ascii=False, indent=1))
    print(f"{len(segments)} segments, {len(words)} words in {time.time() - t0:.1f}s -> {out}")


def diarize_speakers(segments: list[dict], video: Path) -> None:
    """Sets segment["speaker"] on every segment (via Sortformer diarization, matched by time overlap), or None on
    every segment if diarization is unavailable or fails - transcription must always complete either way."""
    for seg in segments:
        seg["speaker"] = None
    if not segments:
        return

    from ovu.diarize import assign_speakers, diarize

    wav_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = Path(f.name)
        extract_wav(video, wav_path)
        intervals = diarize(str(wav_path))
        assign_speakers(segments, intervals)
    except Exception as e:  # noqa: BLE001 - diarization is a nice-to-have, the transcript must not be lost
        print(f"diarization failed, speakers left unset: {type(e).__name__}: {e}")
        for seg in segments:
            seg["speaker"] = None
    finally:
        if wav_path is not None:
            wav_path.unlink(missing_ok=True)
