"""`ovu` command line: create projects, run the pipeline steps, search, evaluate, report, start the GUI.

A project is a directory data/projects/<name>/ with one video; commands take the project name or a unique part of it
(see `ovu list`).
"""

import argparse
import shutil
from pathlib import Path

from ovu.paths import eval_file, list_projects, load_project, new_project_dir, resolve_video, update_project

LANG_HELP = ("language of generated texts, ISO code or name (default: detected from the transcript, else the title; "
             "stored per project, changing it regenerates descriptions and chapters)")


def cmd_new(a) -> None:
    d = new_project_dir(a.name)
    if a.source.startswith(("http://", "https://")):
        from ovu import download

        try:
            video = download.run(a.source, d, a.cookies_from)
        except RuntimeError as e:
            shutil.rmtree(d, ignore_errors=True)
            raise SystemExit(str(e)) from None
    else:
        src = Path(a.source).expanduser()
        if not src.is_file():
            raise SystemExit(f"no such file: {src}")
        d.mkdir(parents=True)
        video = Path(shutil.copy2(src, d / src.name))
    update_project(d, name=a.name, video=video.name, title=a.title or video.stem)
    print(f"project '{a.name}' -> {d}\nnext: ovu process {a.name}")


def cmd_list(a) -> None:
    for d in list_projects():
        p = load_project(d)
        done = [f.name for f in sorted(d.iterdir()) if f.suffix in {".json", ".npz", ".pdf"} and f.name != "project.json"]
        print(f"{d.name}  ({p.get('language', '?')})  {p.get('title', '')}\n    {', '.join(done) or '(not processed)'}")


def cmd_process(a) -> None:
    """Full pipeline; every step skips work that is already done unless --force."""
    from ovu import caption, chapters, embed, language, report, transcribe

    video = resolve_video(a.project)
    transcribe.run(video, a.force)
    embed.run(video, ["frame", "video_shots"], a.force)
    if a.language and not a.vlm:
        language.output_language(video, a.language)  # stored for later --vlm runs
    if a.vlm:
        from ovu.vlm import load_vlm

        language.output_language(video, a.language)  # a changed language deletes stale texts before anything runs
        vlm = load_vlm()
        caption.run(video, context=False, force=a.force, vlm=vlm)
        caption.run(video, context=True, force=a.force, vlm=vlm)
        chapters.run(video, a.force, vlm=vlm)
        del vlm
    # without --vlm only variants whose inputs exist are computed, so no VLM-based variant is added
    embed.run(video, None, a.force)
    if a.vlm:
        report.run(video, a.force)
    print(f"done: {video.parent.name}  ->  ovu app {video.parent.name}")


def main() -> None:
    p = argparse.ArgumentParser(prog="ovu", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="create a project from a video file (copied) or a URL (downloaded)")
    s.add_argument("name", help="project name: lower-case letters, digits and '-'")
    s.add_argument("source", help="video file or URL")
    s.add_argument("--title", help="title used as metadata (default: the video file name)")
    s.add_argument("--cookies-from", metavar="BROWSER", help="for URLs: use this browser's cookies, e.g. chrome")

    sub.add_parser("list", help="projects, their language and what has been computed")

    s = sub.add_parser("process", help="pipeline: transcribe and embed; with --vlm also descriptions, chapters, report")
    s.add_argument("project")
    s.add_argument("--vlm", action="store_true",
                   help="also run the vision-language model: scene descriptions, chapters, PDF report (slow)")
    s.add_argument("--language", help=LANG_HELP)
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("transcribe", help="speech to text (Parakeet)")
    s.add_argument("project")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("embed", help="EmbeddingGemma 2 variants (default: all available)")
    s.add_argument("project")
    s.add_argument("variants", nargs="*")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("caption", help="VLM scene descriptions (needs video_shots)")
    s.add_argument("project")
    s.add_argument("--context", action="store_true", help="hierarchical: global summary + previous scene")
    s.add_argument("--language", help=LANG_HELP)
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("chapters", help="chapters + overall summary from the scene descriptions")
    s.add_argument("project")
    s.add_argument("--language", help=LANG_HELP)
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("report", help="PDF with one representative frame, time range and summary per chapter")
    s.add_argument("project")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("search", help="text query -> best moments")
    s.add_argument("project")
    s.add_argument("query")
    s.add_argument("--variant", help="e.g. frame, caption_ctx+frame (default depends on the video)")
    s.add_argument("-k", type=int, default=5)

    s = sub.add_parser("eval", help="evaluate all variants on the project's eval.json")
    s.add_argument("project")
    s.add_argument("--queries", type=Path)

    s = sub.add_parser("app", help="search GUI on http://localhost:PORT")
    s.add_argument("project")
    s.add_argument("--port", type=int, default=7860)

    a = p.parse_args()
    if a.cmd == "new":
        cmd_new(a)
    elif a.cmd == "list":
        cmd_list(a)
    elif a.cmd == "process":
        cmd_process(a)
    else:
        video = resolve_video(a.project)
        if a.cmd == "transcribe":
            from ovu import transcribe
            transcribe.run(video, a.force)
        elif a.cmd == "embed":
            from ovu import embed
            embed.run(video, a.variants or None, a.force)
        elif a.cmd == "caption":
            from ovu import caption
            caption.run(video, a.context, a.force, lang=a.language)
        elif a.cmd == "chapters":
            from ovu import chapters
            chapters.run(video, a.force, lang=a.language)
        elif a.cmd == "report":
            from ovu import report
            report.run(video, a.force)
        elif a.cmd == "search":
            from ovu import search
            search.search(video, a.query, a.variant, a.k)
        elif a.cmd == "eval":
            from ovu import search
            queries = a.queries or eval_file(video)
            if not queries.exists():
                raise SystemExit(f"no eval set: {queries} (format: eval/README.md) or pass --queries")
            search.evaluate(video, queries)
        elif a.cmd == "app":
            from ovu.app import server
            server.run(video, a.port)


if __name__ == "__main__":
    main()
