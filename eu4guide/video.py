"""Download a guide video, its captions and metadata with yt-dlp."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

CACHE = Path("videos")


def video_id(arg: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([\w-]{11})", arg)
    if m:
        return m.group(1)
    if re.fullmatch(r"[\w-]{11}", arg):
        return arg
    sys.exit(f"Not a YouTube link or video id: {arg}")


def cache_dir(vid: str) -> Path:
    d = CACHE / vid
    d.mkdir(parents=True, exist_ok=True)
    return d


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def need_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not on PATH. Install it (winget install ffmpeg, brew install ffmpeg, apt install ffmpeg).")


def ytdlp(*args: str) -> None:
    run([sys.executable, "-m", "yt_dlp", "--no-warnings", "--no-progress", *args])


def download(vid: str) -> Path:
    """Fetch video (no audio), English captions and metadata into videos/<id>/."""
    out = cache_dir(vid)
    url = f"https://youtu.be/{vid}"
    if not (out / "info.info.json").exists():
        ytdlp("--skip-download", "--write-info-json", "-o", str(out / "info"), url)
    if not list(out.glob("video.*.json3")):
        # manual English subs win over auto-captions when both exist
        ytdlp("--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en,en-orig",
              "--sub-format", "json3", "-o", str(out / "video.%(ext)s"), url)
        if not list(out.glob("video.*.json3")):
            sys.exit("This video has no English captions, so there is no transcript to work from.")
    if not (out / "video.mp4").exists():
        # H.264 decodes far faster than AV1/VP9, which matters when sampling a 1h video
        ytdlp("-f", "bv*[height<=1080][vcodec^=avc1]/bv*[height<=1080][ext=mp4]/bv*[height<=1080]",
              "--remux-video", "mp4", "-o", str(out / "video.%(ext)s"), url)
    return out


def info(out: Path) -> dict:
    f = out / "info.info.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text(encoding="utf-8"))
    return {"id": d.get("id"), "title": d.get("title"), "channel": d.get("channel") or d.get("uploader"),
            "duration": d.get("duration"), "upload_date": d.get("upload_date")}


def frame(out: Path, second: float, dest: Path) -> Path:
    """Save one full 1920x1080 frame."""
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(second), "-i", str(out / "video.mp4"),
         "-frames:v", "1", "-vf", "scale=1920:1080", "-y", str(dest)])
    return dest
