"""eu4guide: EU4 YouTube guide -> dated playbook."""
import argparse
import json
import webbrowser
from pathlib import Path

from . import dates, guide, timeline, video


def cmd_timeline(a) -> Path:
    video.need_ffmpeg()
    vid = video.video_id(a.video)
    out = video.download(vid)
    meta = video.info(out)
    crop = a.crop
    if not crop:
        saved = out / "crop.txt"
        if saved.exists():
            crop = saved.read_text().strip()
        else:
            crop = dates.calibrate(out, meta.get("duration") or 600)
            saved.write_text(crop)
    raw = dates.read(out, crop, a.every)
    kept = dates.clean(raw)
    seen = sum(1 for _, d in raw if d)
    print(f"Date read in {seen}/{len(raw)} frames, {len(kept)} kept after dropping misreads")
    if seen < len(raw) * 0.3:
        print("Warning: the date was rarely readable. The guide may show lots of the menu or a "
              "non-standard UI. Check videos/<id>/dates.txt.")
    path = timeline.build(out, meta, kept)
    print(f"Timeline: {path}")
    return path


def cmd_run(a) -> None:
    from .generate import generate
    tl = cmd_timeline(a)
    js = generate(tl, a.nation, a.model)
    index = guide.build_site()
    print(f"Guide: {js}\nSite: {index}")
    if not a.no_open:
        webbrowser.open(index.resolve().as_uri() + f"#{js.stem}")


def cmd_build(a) -> None:
    index = guide.build_site(Path(a.out))
    n = len(list(guide.GUIDES.glob("*.json")))
    print(f"Built {index} with {n} {'nation' if n == 1 else 'nations'}")
    if a.open:
        webbrowser.open(index.resolve().as_uri() + (f"#{a.open}" if isinstance(a.open, str) else ""))


def cmd_frame(a) -> None:
    video.need_ffmpeg()
    out = video.download(video.video_id(a.video))
    print(video.frame(out, a.seconds, out / f"frame_{int(a.seconds)}.png"))


def cmd_schema(a) -> None:
    print(json.dumps(guide.SCHEMA, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(prog="eu4guide", description=__doc__)
    sub = ap.add_subparsers(required=True)

    def video_args(p):
        p.add_argument("video", help="YouTube link or video id")
        p.add_argument("--every", type=int, default=5, help="seconds between date reads (default 5)")
        p.add_argument("--crop", help="date box as w:h:x:y on a 1920x1080 frame (default: find it automatically)")

    p = sub.add_parser("run", help="video -> timeline -> guide (Claude API) -> HTML")
    video_args(p)
    p.add_argument("--nation", help="nation name, if the title is ambiguous")
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--no-open", action="store_true", help="don't open the guide in the browser")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("timeline", help="video -> videos/<id>/timeline.md (no API needed)")
    video_args(p)
    p.set_defaults(fn=cmd_timeline)

    p = sub.add_parser("build", help="guides/*.json + reference/ -> static site in site/")
    p.add_argument("--out", default="site")
    p.add_argument("--open", nargs="?", const=True, metavar="SLUG",
                   help="open the site in the browser, optionally on one nation's tab")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("frame", help="save one full frame, for checking the date box by hand")
    p.add_argument("video")
    p.add_argument("seconds", type=float)
    p.set_defaults(fn=cmd_frame)

    p = sub.add_parser("schema", help="print the guide JSON schema")
    p.set_defaults(fn=cmd_schema)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
