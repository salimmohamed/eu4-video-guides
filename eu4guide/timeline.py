"""Join the transcript with the in-game dates into timeline.md."""
import json
from pathlib import Path


def transcript(out: Path) -> list[tuple[float, str]]:
    subs = sorted(out.glob("video.*.json3"))
    # "video.en.json3" is the processed track. Prefer it over "en-orig" or other variants.
    f = next((s for s in subs if s.name == "video.en.json3"), subs[0])
    data = json.loads(f.read_text(encoding="utf-8"))
    segs = []
    for ev in data.get("events", []):
        txt = "".join(s.get("utf8", "") for s in ev.get("segs") or []).replace("\n", " ").strip()
        if txt:
            segs.append((ev["tStartMs"] / 1000, txt))
    return segs


def fmt(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def date_at(dates: list[tuple[int, str]], t: float) -> str | None:
    cur = None
    for dt, d in dates:
        if dt > t:
            break
        cur = d
    return cur


def build(out: Path, meta: dict, dates: list[tuple[int, str]], block: int = 30) -> Path:
    vid = meta.get("id") or out.name
    chunks: dict[int, list[str]] = {}
    for t, txt in transcript(out):
        chunks.setdefault(int(t // block), []).append(txt)
    lines = [f"# {meta.get('title') or vid}",
             f"Channel: {meta.get('channel') or 'unknown'}",
             f"https://youtu.be/{vid}", "",
             "Each block: video time | in-game date on screen at that moment ('not visible' when the "
             "game wasn't on screen), then what the narrator says. Captions are auto-generated, so "
             "EU4 names are often misspelled.", ""]
    for b in sorted(chunks):
        start = b * block
        d = date_at(dates, start + block / 2) or "not visible"
        lines += [f"## {fmt(start)} (t={start}) | {d}", " ".join(chunks[b]), ""]
    path = out / "timeline.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    changes, last = [], None
    for t, d in dates:
        y = d.split()[-1]
        if y != last:
            changes.append(f"{fmt(t)}  {d}")
            last = y
    (out / "dates.txt").write_text("\n".join(changes), encoding="utf-8")
    return path
