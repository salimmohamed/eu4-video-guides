"""Find and read EU4's in-game date (top-right corner) across a video."""
import difflib
import json
import re
import statistics
import sys
import tempfile
from pathlib import Path

from . import video

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
# Loose on purpose: OCR drops spaces and letters ("1Apr1507", "29 Apil1481", "Februaly").
DATE_RE = re.compile(r"(\d{1,2})\s*([A-Za-z]{2,})\s*(1[3-8]\d\d)")

# Search area for calibration on a 1920x1080 frame: the right 40%, top 15%.
SEARCH = (1150, 0, 770, 160)  # x, y, w, h

_engine = None


def engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def ocr(path: Path) -> list[tuple[list, str]]:
    """Find and read every text line in an image (slow, used for calibration)."""
    res, _ = engine()(str(path))
    return [(r[0], r[1]) for r in res] if res else []


def ocr_line(path: Path) -> str:
    """Read an image that is already just one line of text. About 100x faster than ocr()."""
    res, _ = engine()(str(path), use_det=False, use_cls=False, use_rec=True)
    return " ".join(r[0] for r in res) if res else ""


def month(token: str) -> str | None:
    t = token.lower()
    by_prefix = [m for m in MONTHS if m.lower().startswith(t[:3])]
    if len(by_prefix) == 1:
        return by_prefix[0]
    close = difflib.get_close_matches(t, [m.lower() for m in MONTHS], n=1, cutoff=0.6)
    return MONTHS[[m.lower() for m in MONTHS].index(close[0])] if close else None


def parse(text: str) -> str | None:
    s = re.sub(r"0(?=[A-Za-z])", "O", text.replace(",", " "))  # "60ctober" is "6 October"
    m = DATE_RE.search(s)
    if not m:
        return None
    mon = month(m.group(2))
    if not mon:
        return None
    day = int(m.group(1))
    return f"{day} {mon} {m.group(3)}" if 1 <= day <= 31 else f"{mon} {m.group(3)}"


def calibrate(out: Path, duration: float, samples: int = 10) -> str:
    """Locate the date box by OCR-ing the top-right of frames spread through the video.

    Returns an ffmpeg crop string w:h:x:y in 1920x1080 coordinates.
    """
    sx, sy, sw, sh = SEARCH
    boxes = []
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(samples):
            t = duration * (0.1 + 0.8 * i / max(samples - 1, 1))
            f = video.frame(out, t, Path(tmp) / f"{i}.png")
            from PIL import Image  # rapidocr pulls in pillow
            Image.open(f).crop((sx, sy, sx + sw, sy + sh)).save(f)
            for pts, text in ocr(f):
                if parse(text):
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    boxes.append((min(xs) + sx, min(ys) + sy, max(xs) + sx, max(ys) + sy))
    if not boxes:
        sys.exit("Couldn't find the in-game date in the top-right corner. Save a frame with "
                 "`eu4guide frame <url> <seconds>`, find the date box and pass --crop w:h:x:y.")
    # The date text is centred, so its width changes with the month name. Use the median
    # centre and the widest box seen, plus padding for longer dates than were sampled.
    cx = statistics.median((b[0] + b[2]) / 2 for b in boxes)
    cy = statistics.median((b[1] + b[3]) / 2 for b in boxes)
    w = max(b[2] - b[0] for b in boxes) * 1.35 + 20
    h = statistics.median(b[3] - b[1] for b in boxes) + 16
    x, y = max(0, int(cx - w / 2)), max(0, int(cy - h / 2))
    w, h = int(min(w, 1920 - x)), int(min(h, 1080 - y))
    print(f"Date box found at x={x} y={y} ({w}x{h}) in {len(boxes)}/{samples} sample frames")
    return f"{w}:{h}:{x}:{y}"


def read(out: Path, crop: str, every: int) -> list[tuple[int, str | None]]:
    """OCR the date every `every` seconds. Cached in dates_raw.json."""
    cache = out / "dates_raw.json"
    meta = {"crop": crop, "every": every, "parser": 2}  # bump parser when parse() changes
    if cache.exists():
        saved = json.loads(cache.read_text(encoding="utf-8"))
        if isinstance(saved, dict) and saved.get("meta") == meta:
            return [tuple(x) for x in saved["dates"]]
    crops = out / "crops"
    stamp = crops / "crop.txt"
    key = f"{crop}@{every}"
    if not (stamp.exists() and stamp.read_text() == key):
        for old in crops.glob("*.png") if crops.exists() else []:
            old.unlink()
        crops.mkdir(exist_ok=True)
        w, h, x, y = crop.split(":")
        print(f"Cropping the date every {every}s (decodes the whole video, a few minutes)...")
        video.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(out / "video.mp4"),
                   "-vf", f"fps=1/{every},scale=1920:1080,crop={w}:{h}:{x}:{y},scale={int(w) * 3}:-1",
                   str(crops / "%05d.png")])
        stamp.write_text(key)
    files = sorted(crops.glob("*.png"))
    dates = []
    for i, f in enumerate(files):
        dates.append((i * every, parse(ocr_line(f))))
        if i % 100 == 99:
            print(f"  read {i + 1}/{len(files)} frames")
    cache.write_text(json.dumps({"meta": meta, "dates": dates}), encoding="utf-8")
    return dates


def clean(dates: list[tuple[int, str | None]]) -> list[tuple[int, str]]:
    """Drop isolated misreads: a year far from the median of its neighbours.

    Not a monotonic filter: guides often open with an endgame preview before
    jumping back to 1444, and loaded saves can go backwards.
    """
    def year(d): return int(d.split()[-1])
    good = [(t, d) for t, d in dates if d]
    kept = []
    for i, (t, d) in enumerate(good):
        near = sorted(year(x[1]) for x in good[max(0, i - 3):i + 4])
        if abs(year(d) - near[len(near) // 2]) <= 3:
            kept.append((t, d))
    return kept
