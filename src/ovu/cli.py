"""`ovu` command line: download, run the pipeline steps, search, evaluate, start the GUI.

A video argument is a file path or a (partial) slug of a video in data/videos (see `ovu list`).
"""

import argparse
from pathlib import Path

from ovu.paths import eval_file, list_videos, out_dir, resolve_video, slug

LANG_HELP = ("language of generated texts, ISO code or name (default: detected from the transcript, else the title; "
             "stored per video)")


def cmd_list(a) -> None:
    for v in list_videos():
        d = out_dir(v)
        done = [f.stem for f in sorted(d.glob("*.json")) + sorted(d.glob("*.npz"))]
        print(f"{slug(v)}\n    {', '.join(done) or '(not processed)'}")


def cmd_process(a) -> None:
    """Full pipeline; every step skips work that is already done unless --force."""
    from ovu import caption, chapters, embed, transcribe

    if a.video.startswith(("http://", "https://")):
        from ovu import download

        video = download.run(a.video, a.cookies_from)
    else:
        video = resolve_video(a.video)
    transcribe.run(video, a.force)
    embed.run(video, ["frame", "video_shots"], a.force)
    if not a.no_vlm:
        from ovu.vlm import load_vlm

        vlm = load_vlm()
        caption.run(video, context=False, force=a.force, vlm=vlm, lang=a.language)
        caption.run(video, context=True, force=a.force, vlm=vlm, lang=a.language)
        chapters.run(video, a.force, vlm=vlm, lang=a.language)
        del vlm
    embed.run(video, None, a.force)
    print(f"done: {slug(video)}  ->  ovu app {slug(video)}")


def main() -> None:
    p = argparse.ArgumentParser(prog="ovu", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="videos in data/videos and what has been computed")

    s = sub.add_parser("download", help="download a video (yt-dlp) into data/videos")
    s.add_argument("url")
    s.add_argument("--cookies-from", metavar="BROWSER", help="use this browser's cookies, e.g. chrome or firefox")

    s = sub.add_parser("process", help="full pipeline: transcribe, embed, captions, chapters (URL or video)")
    s.add_argument("video")
    s.add_argument("--no-vlm", action="store_true", help="skip scene descriptions and chapters")
    s.add_argument("--language", help=LANG_HELP)
    s.add_argument("--cookies-from", metavar="BROWSER")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("transcribe", help="speech to text (Parakeet)")
    s.add_argument("video")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("embed", help="EmbeddingGemma 2 variants (default: all available)")
    s.add_argument("video")
    s.add_argument("variants", nargs="*")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("caption", help="VLM scene descriptions (needs video_shots)")
    s.add_argument("video")
    s.add_argument("--context", action="store_true", help="hierarchical: global summary + previous scene")
    s.add_argument("--language", help=LANG_HELP)
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("chapters", help="chapters + overall summary from the scene descriptions")
    s.add_argument("video")
    s.add_argument("--language", help=LANG_HELP)
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("search", help="text query -> best moments")
    s.add_argument("video")
    s.add_argument("query")
    s.add_argument("--variant", help="e.g. frame, caption_ctx+frame (default depends on the video)")
    s.add_argument("-k", type=int, default=5)

    s = sub.add_parser("eval", help="evaluate all variants on eval/<slug>.json")
    s.add_argument("video")
    s.add_argument("--queries", type=Path)

    s = sub.add_parser("app", help="search GUI on http://localhost:PORT")
    s.add_argument("video")
    s.add_argument("--port", type=int, default=7860)

    a = p.parse_args()
    if a.cmd == "list":
        cmd_list(a)
    elif a.cmd == "download":
        from ovu import download
        download.run(a.url, a.cookies_from)
    elif a.cmd == "process":
        cmd_process(a)
    else:
        video = resolve_video(a.video)
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
        elif a.cmd == "search":
            from ovu import search
            search.search(video, a.query, a.variant, a.k)
        elif a.cmd == "eval":
            from ovu import search
            search.evaluate(video, a.queries or eval_file(video))
        elif a.cmd == "app":
            from ovu.app import server
            server.run(video, a.port)


if __name__ == "__main__":
    main()
