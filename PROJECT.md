# Pipeline

How a video becomes searchable, which local model does what, and in which order. All results of a video are in
`data/processed/<slug>/`. `ovu process` runs the steps in the order below.

## Models

| Model | Size / precision | Runs on | Used for |
|---|---|---|---|
| [Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) via onnx-asr + Silero VAD | int8 ONNX | CPU | speech to text with word timestamps (multilingual) |
| [EmbeddingGemma 2](https://huggingface.co/google/embeddinggemma-2) | 740M, bf16, ~2 GB VRAM | GPU | one 768-d vector space for text, images, video and audio; queries and all variants |
| [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) | 4-bit nf4 (bitsandbytes), ~3.5-4.5 GB VRAM | GPU | scene descriptions, global summary, chapters (vision and text-only) |
| [lingua](https://github.com/pemistahl/lingua-py) | rule/statistics based | CPU | detecting the output language |
| ffmpeg | | CPU | decoding audio (16 kHz mono) and frames (1 fps), hard-cut detection, thumbnails |

## Steps

1. **Download** (`ovu download`, optional): yt-dlp saves the video as MP4 (≤ 1080p) in `data/videos/`.
2. **Transcribe** (Parakeet + VAD) → `transcript.json`: speech segments and word timestamps in the spoken language.
3. **Frame embeddings** (EmbeddingGemma 2): one image per second → variant `frame`.
4. **Content segments**: boundaries at hard cuts (ffmpeg scene score > 0.3) and where the frame-embedding similarity
   to the previous second drops below 0.85; segments are 2-10 s. Each segment is embedded as a video clip →
   `video_shots`.
5. **Output language** → `meta.json`: user choice (`--language`), else detected from the transcript (≥ 20 words),
   else from the title, else English. Used by all generated texts; the transcript is never translated.
6. **Scene descriptions, plain** (Qwen3-VL) → `captions.json`: per segment, 3 frames (start, middle, end) → JSON with
   `description`, `on_screen_text`, `shot_type`, `keywords`.
7. **Scene descriptions with context** (Qwen3-VL) → `summary.json`, `captions_ctx.json`:
   a global summary from a 40-frame storyboard plus the title (characters with fixed labels, recurring objects,
   places, plot); then per segment all frames as video input plus the global summary and the previous description.
   Near-black/uniform segments are described without context, so the model cannot fill them with the story.
8. **Chapters** (Qwen3-VL, text only) → `chapters.json`: the context descriptions are grouped into 6-20 contiguous
   chapters with title and summary, then an overall summary (plot, characters, themes) is written from the chapters.
9. **Remaining embeddings** (EmbeddingGemma 2) → `embeddings.npz`:
   - 20 s windows, 10 s stride: `text` (transcript), `video`, `audio`, `video_audio`, `text_video`
   - per segment: `caption`, `caption_ctx` (descriptions embedded as text)
   - per chapter: `chapter`

## Search

A query is embedded with EmbeddingGemma 2 (`SearchQuery` prompt) and compared with every variant. Unit scores are
spread to one score per second; variants joined by `+` are fused as the per-second mean over the variants that have a
value (e.g. no transcript where nothing is said). Moments are the peaks of the per-second curve, at least 8 s apart.

Default variant: `text+frame` for videos with speech, `caption_ctx+frame` without. In the evaluation so far, frame
and scene-description variants find visual content, the transcript finds spoken content, and fusions of both are
best overall; 20 s windows localize poorly.

## GUI (`ovu app`)

A FastAPI server keeps the text side of EmbeddingGemma 2 in memory and serves one HTML page:

- **Video player** with the current time and a button (key `S`) to find moments similar to the current frame.
- **Side tabs**: spoken transcript, scene descriptions (with context if available) and chapters with the overall
  summary; the entry at the playhead is highlighted, a click jumps there, and during a search a bar shows how well
  each entry matches.
- **Timeline**: chapter track, filmstrip with segment boundaries, a curve of the selected variant with numbered top
  hits, one heatmap row per variant (colour scaled per row), playhead; hover shows thumbnail, all scores, chapter,
  description and speech; click seeks.
- **Top hits**: cards with thumbnail, time, score, description and speech, each with a "similar" button.
