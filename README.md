# offline-video-understanding

**Understand and search videos with local models only.** Give it a video file or a URL and it transcribes the speech,
embeds frames, scenes, audio and text into one vector space, describes every scene with a local vision-language
model, groups the scenes into chapters with a summary, writes a PDF report (one picture, time range and summary per
chapter), and lets you search the video by text in a browser GUI, down to the second. Nothing is sent to a cloud API; everything runs on one consumer GPU (developed on an 8 GB RTX 3070
Laptop).

It is a research project: the question is how far fully local models get in video understanding, measured with a
small evaluation (`ovu eval`). See [PROJECT.md](PROJECT.md) for the pipeline in detail.

## Use it

Requirements: Linux, an NVIDIA GPU with ≥ 8 GB VRAM, `ffmpeg`, [uv](https://docs.astral.sh/uv/), and `node` for
YouTube downloads. Models (~12 GB) are downloaded from Hugging Face on first use.

```bash
uv sync

# One project per video: copy a local file or download a URL
uv run ovu new my-video ~/Videos/clip.mp4
uv run ovu new my-talk "https://www.youtube.com/watch?v=..." --cookies-from chrome

# Pipeline: transcript + embeddings (search works after this)
uv run ovu process my-video
# Optional, slow: scene descriptions, chapters and PDF report with a local vision-language model
uv run ovu process my-video --vlm [--language de]

uv run ovu list                       # projects, language and what has been computed
uv run ovu app my-video               # GUI on http://localhost:7860
uv run ovu search my-video "a red car in the rain"
open data/projects/my-video/report.pdf
```

- Each project lives in `data/projects/<name>/`: the video, `project.json`, all results, `report.pdf` and an optional
  eval set `eval.json`. Commands take the project name or a unique part of it.
- Every step skips finished work, so an interrupted `ovu process` simply continues; `--force` recomputes.
- The vision-language model (Qwen3-VL, ~9 GB download, ~3 s of compute per second of video) is off by default;
  `--vlm` adds scene descriptions, chapters with summary and `report.pdf`.
- Generated texts (descriptions, chapters, summary, report) use the language spoken in the video, or the title's
  language if there is no speech; choose another with `--language en|de|fr|...` (changing it regenerates them). The
  transcript always stays in the original language.
- YouTube often refuses anonymous downloads; `--cookies-from chrome` (or `firefox`) uses your browser's cookies.
- Single steps: `ovu transcribe | embed | caption [--context] [--summary-only] | chapters | report | search | eval | app`.

### Just "what is this video about?" (no per-scene descriptions)

For a quick global summary - genre, characters, objects, places, a few sentences of plot - without the slow,
scene-by-scene description pass:

```bash
uv run ovu process my-video --vlm --summary-only [--language de]
cat data/projects/my-video/summary.json
```

This still runs transcription and the non-VLM embeddings as usual, then only the global-summary VLM call (seconds,
not minutes) - no `captions.json`, `captions_ctx.json`, `chapters.json` or `report.pdf`. The summary is built from a
40-frame storyboard spread over the whole video, the title, **and the video's own transcript** (a name or
explanation said in speech can inform the summary even when the frames alone are ambiguous). `summary.json` is
plain JSON:

```json
{"genre": "...", "characters": [{"name": "...", "appearance": "..."}], "objects": ["..."], "places": ["..."],
 "plot": "3-6 sentences"}
```

**Calling this from another project** (e.g. a sibling project that wants a quick video summary, without sharing a
Python environment with this repo - there is no importable API, only the CLI and the JSON files it writes):

```bash
cd /path/to/offline-video-understanding
uv run ovu new <project-name> /path/to/video.mp4      # copies the video into data/projects/<project-name>/
uv run ovu process <project-name> --vlm --summary-only --language de
cat data/projects/<project-name>/summary.json          # stable path, read it directly
```

Runtime for a video a few minutes long is roughly tens of seconds, dominated by model loading and the one summary
call, not video length; peak VRAM ~3.5-4.5 GB; fully local, no network calls. Note `ovu new` always copies the video
file (plain filesystem copy, no hash verification) - a caller with its own rules about not duplicating originals
should be aware of that before passing in a file it considers the single/original copy.

**The GUI** shows the video with a timeline: chapters, a filmstrip, the similarity curve of the selected search
variant with its top hits, and one heatmap row per variant. Topic chapters, found from the transcript without the
vision-language model, appear as their own track and as ranked chapter hits above the moment hits. Click the
timeline to jump, hover for a preview, press `S` to find moments similar to the current frame and `<` `>` (or the 1×
/ 1.5× / 2× buttons) to change the playback speed. Side tabs show the transcript, the scene descriptions and the
chapters with the summary, all synchronized with playback.

**Runtime** (13 min video, RTX 3070 8 GB): transcription ~10 s, embeddings ~10 min, scene descriptions ~40 min,
chapters ~2 min.

## Contribute

```bash
git clone <repo> && cd offline-video-understanding
uv sync                       # Python 3.12 env with all dependencies
npm install -g @fission-ai/openspec   # spec-driven workflow (optional for small fixes)
```

- **Specs first.** Behaviour is specified per capability in [`openspec/specs/`](openspec/specs); project-wide
  constraints are in [`openspec/config.yaml`](openspec/config.yaml). New features start as an OpenSpec change
  (`openspec new change <name>` or `/opsx:propose` in Claude Code), are implemented, then archived into the specs.
- **Local models only**, and pipeline prompts stay generic: no names, genres or examples from a particular video.
- **Measure.** Changes affecting retrieval quality come with `ovu eval` numbers. Eval sets live in the project as
  `eval.json` (format in [eval/README.md](eval/README.md)) and are not committed, since they describe video content.
- **Never commit videos, results or eval sets.** `data/` is git-ignored.
- Code is English, plain Python modules under `src/ovu/` (one module per pipeline step); see [AGENTS.md](AGENTS.md)
  for orientation.
