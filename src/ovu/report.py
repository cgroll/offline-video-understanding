"""PDF report of a project: title page with the overall summary, then one entry per content chapter with number,
time range, title, one representative frame and the chapter summary. No model is loaded.

Representative frame: the second inside the chapter whose `frame` embedding is most similar to the chapter's text
embedding (`chapter`: title + summary), ignoring nearly uniform frames; middle of the chapter if none qualifies, the
visual medoid of the chapter if the chapter embeddings are missing or stale.
"""

import json
import subprocess
import unicodedata
import tempfile
from pathlib import Path

import numpy as np

from ovu.caption import EMPTY_STD
from ovu.media import load_frames
from ovu.paths import load_project, out_dir, title

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FRAME_WIDTH = 1280
IMAGE_SHARE = 0.72  # image width relative to the text width
LABELS = {
    "en": {"chapter": "Chapter", "summary": "Summary", "characters": "Characters", "themes": "Themes",
           "duration": "Duration", "language": "Language", "chapters": "Chapters",
           "footer": "Generated locally with offline-video-understanding"},
    "de": {"chapter": "Kapitel", "summary": "Zusammenfassung", "characters": "Figuren", "themes": "Themen",
           "duration": "Dauer", "language": "Sprache", "chapters": "Kapitel",
           "footer": "Lokal erzeugt mit offline-video-understanding"},
}


def fmt(t: float, long: bool) -> str:
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if long else f"{t // 60}:{t % 60:02d}"


def time_range(start: float, end: float, total: float) -> str:
    return f"{fmt(start, total >= 3600)}–{fmt(end, total >= 3600)}"


def representative_seconds(emb: dict, chapters: list[dict], uniform: np.ndarray) -> list[int]:
    frames = emb["frame"]
    have_text = ("chapter" in emb and len(emb["chapter"]) == len(chapters)
                 and np.allclose(emb["chapter_starts"], [c["start"] for c in chapters]))
    out = []
    for i, c in enumerate(chapters):
        secs = np.arange(int(c["start"]), max(int(np.ceil(c["end"])), int(c["start"]) + 1))
        secs = secs[secs < len(frames)]
        ok = secs[~uniform[secs]]
        if len(ok) == 0:
            out.append(int((c["start"] + c["end"]) / 2))
            continue
        target = emb["chapter"][i] if have_text else frames[ok].mean(0)
        out.append(int(ok[np.argmax(frames[ok] @ target)]))
    return out


def extract_frame(video: Path, t: int, path: Path, width: int) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t + 0.5}", "-i", str(video), "-frames:v", "1",
                    "-vf", f"scale={width}:-2", "-q:v", "3", str(path)], check=True)


def video_width(video: Path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                          "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True).stdout
    return int(out.strip().split(",")[0])


def _fonts() -> tuple[str, str]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    regular, bold = FONT_DIR / "DejaVuSans.ttf", FONT_DIR / "DejaVuSans-Bold.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("DejaVu", str(regular)))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(bold)))
        return "DejaVu", "DejaVu-Bold"
    return "Helvetica", "Helvetica-Bold"  # Latin-1 only


def run(video: Path, force: bool = False) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer
    from xml.sax.saxutils import escape

    d = out_dir(video)
    path = d / "report.pdf"
    ch_path = d / "chapters.json"
    if not ch_path.exists():
        raise SystemExit(f"no chapters for this project; run `ovu chapters {d.name}` (or `ovu process`) first")
    if path.exists() and not force and path.stat().st_mtime >= ch_path.stat().st_mtime:
        print(f"{path} exists (use --force)")
        return path

    data = json.loads(ch_path.read_text())
    chapters, summary = data["chapters"], data.get("summary", {})
    if not chapters:
        raise SystemExit(f"chapters.json has no chapters; rerun `ovu chapters {d.name} --force`")
    code = data.get("language") or load_project(d).get("language", "en")
    lab = LABELS.get(code, LABELS["en"])
    total = json.loads((d / "transcript.json").read_text())["duration"]
    emb = dict(np.load(d / "embeddings.npz"))
    frames = load_frames(video)
    uniform = frames.mean(axis=3).std(axis=(1, 2)) < EMPTY_STD
    del frames
    seconds = representative_seconds(emb, chapters, uniform)

    regular, bold = _fonts()
    ink, muted = colors.HexColor("#1b1b1b"), colors.HexColor("#6b6b66")
    h1 = ParagraphStyle("h1", fontName=bold, fontSize=22, leading=27, textColor=ink, spaceAfter=6)
    meta = ParagraphStyle("meta", fontName=regular, fontSize=10, leading=14, textColor=muted, spaceAfter=14)
    h2 = ParagraphStyle("h2", fontName=bold, fontSize=13, leading=17, textColor=ink, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", fontName=regular, fontSize=10.5, leading=15, textColor=ink)
    kicker = ParagraphStyle("kicker", fontName=regular, fontSize=9, leading=12, textColor=muted, spaceAfter=2)
    # NFKC maps full-width characters (yt-dlp puts e.g. "｜" into file names) to ones the font has
    p = lambda text, style: Paragraph(escape(unicodedata.normalize("NFKC", str(text))), style)

    story = [p(title(video), h1), p(f"{lab['duration']}: {fmt(total, total >= 3600)}  ·  {lab['language']}: {code}  ·  "
                                    f"{len(chapters)} {lab['chapters']}", meta)]
    if summary.get("plot"):
        story += [p(lab["summary"], h2), p(summary["plot"], body)]
    if summary.get("characters"):
        story += [p(lab["characters"], h2)] + [p(f"• {c}", body) for c in summary["characters"]]
    if summary.get("themes"):
        story += [p(lab["themes"], h2)] + [p(f"• {t}", body) for t in summary["themes"]]
    story.append(PageBreak())

    content_width = A4[0] - 4 * cm
    width = min(FRAME_WIDTH, video_width(video))
    with tempfile.TemporaryDirectory() as tmp:
        for i, (c, t) in enumerate(zip(chapters, seconds), 1):
            img_path = Path(tmp) / f"{i:03d}.jpg"
            extract_frame(video, t, img_path, width)
            img = Image(str(img_path))
            # small enough for two chapters per page
            img.drawWidth = IMAGE_SHARE * content_width
            img.drawHeight = img.drawWidth * img.imageHeight / img.imageWidth
            img.hAlign = "LEFT"
            story.append(KeepTogether([
                p(f"{lab['chapter']} {i}  ·  {time_range(c['start'], c['end'], total)}", kicker),
                p(c["title"], h2), img, Spacer(1, 6), p(c["summary"], body), Spacer(1, 18)]))

        def footer(canvas, doc):
            canvas.setFont(regular, 8)
            canvas.setFillColor(muted)
            canvas.drawString(2 * cm, 1.2 * cm, lab["footer"])
            canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(doc.page))

        SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                          bottomMargin=2 * cm, title=unicodedata.normalize("NFKC", title(video))).build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"{len(chapters)} chapters -> {path}")
    return path
