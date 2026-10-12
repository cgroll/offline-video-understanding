"""Search GUI: text query -> similarity per second along the timeline, frame -> similar frames, transcript, scene
descriptions and chapters. Keeps EmbeddingGemma 2 (text side) in memory to embed queries; frontend is index.html.
"""

import json
from pathlib import Path

import numpy as np

from ovu.embed import load_embeddings
from ovu.media import make_thumbs
from ovu.paths import eval_file, out_dir, title
from ovu.search import per_second as fused_per_second
from ovu.segments import spans, to_seconds
from ovu.transcribe import load_transcript

# variant -> label; window/shot/chapter variants are spread to seconds by averaging the units covering each second
VARIANTS = {
    "frame": "Frame (per second)",
    "video": "Video clip (20 s window)",
    "text": "Transcript (20 s window)",
    "audio": "Audio (20 s window)",
    "text_video": "Transcript + video (20 s window)",
    "video_shots": "Video scenes (2–10 s)",
    "caption": "Scene description (VLM)",
    "caption_ctx": "Scene description with context (VLM)",
    "chapter": "Chapters (VLM)",
}
# late fusions (mean of per-second scores), only for text queries
FUSIONS = {
    "text+frame": "Transcript + frame (fusion)",
    "text+caption+frame": "Transcript + description + frame (fusion)",
    "caption+frame": "Description + frame (fusion)",
    "caption_ctx+frame": "Description (context) + frame (fusion)",
    "chapter+caption_ctx+frame": "Chapters + description + frame (fusion)",
}


def create_app(video: Path):
    import torch
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    from ovu.embedder import encode_queries, load_embedder

    vdir = out_dir(video)
    emb = load_embeddings(video)
    transcript = load_transcript(video)
    ef = eval_file(video)
    examples = [q["q"] for q in json.loads(ef.read_text())["queries"]][::5][:5] if ef.exists() else []
    # show the descriptions with context when available
    cap_path = next((p for p in [vdir / "captions_ctx.json", vdir / "captions.json"] if p.exists()), None)
    captions = json.loads(cap_path.read_text()) if cap_path else []
    ch_path = vdir / "chapters.json"
    chapters = json.loads(ch_path.read_text()) if ch_path.exists() else {"chapters": [], "summary": {}}
    n_sec = len(emb["frame"])
    variants = [v for v in VARIANTS if v in emb]
    fusions = [f for f in FUSIONS if all(v in emb for v in f.split("+"))]
    make_thumbs(video, vdir / "thumbs")
    model = load_embedder(audio=False)

    def as_list(row: np.ndarray) -> list[float]:
        # nothing at that second (no speech) -> 0, which the frontend draws as "empty"
        return np.round(np.nan_to_num(row, nan=0.0), 4).tolist()

    app = FastAPI()
    app.mount("/thumbs", StaticFiles(directory=vdir / "thumbs"), name="thumbs")

    @app.get("/")
    def index():
        return FileResponse(Path(__file__).parent / "index.html")

    @app.get("/video")
    def video_file():
        return FileResponse(video, media_type="video/mp4")

    @app.get("/api/meta")
    def meta():
        return {"title": title(video), "duration": transcript["duration"], "n_seconds": n_sec,
                "variants": [{"id": v, "label": {**VARIANTS, **FUSIONS}[v]} for v in fusions + variants],
                "segments": transcript["segments"],
                "examples": examples,
                "chapters": chapters["chapters"], "summary": chapters["summary"],
                "shots": emb["shot_starts"].tolist() if "shot_starts" in emb else [],
                "captions": [{k: c[k] for k in ("start", "end", "description", "on_screen_text", "shot_type")}
                             for c in captions]}

    @app.get("/api/query")
    def query(q: str):
        with torch.inference_mode():
            qv = encode_queries(model, [q])
        return {"scores": {v: as_list(fused_per_second(emb, qv, v)[0]) for v in variants + fusions}}

    @app.get("/api/similar")
    def similar(t: int):
        if not 0 <= t < n_sec:
            raise HTTPException(400, "t out of range")
        scores = {}
        # compare against the unit (frame / window / shot / chapter) containing t
        for v in variants:
            s, e = spans(emb, v)
            inside = np.flatnonzero((s <= t + 0.5) & (t + 0.5 < e))
            u = int(inside[0]) if len(inside) else int(np.argmin(np.abs((s + e) / 2 - (t + 0.5))))
            if np.any(emb[v][u]):
                scores[v] = as_list(to_seconds(emb, v, emb[v] @ emb[v][u]))
        return {"scores": scores}

    return app


def run(video: Path, port: int = 7860) -> None:
    import uvicorn

    uvicorn.run(create_app(video), host="127.0.0.1", port=port)
