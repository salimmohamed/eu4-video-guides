"""The guide format: JSON schema, validation, and rendering to HTML."""
import html
import json
import re
from importlib import resources
from pathlib import Path

GUIDES = Path("guides")

STEP = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "The action, imperative and specific (who, what, which option)."},
        "note": {"type": "string", "description": "Why, a condition, or an alternative. Empty string if none."},
        "date": {"type": "string", "description": "In-game date on screen when it happened, e.g. 'Nov 1444' or '25 Aug 1450'."},
        "t": {"type": "integer", "description": "Video second where the narrator says it."},
        "wait": {"type": "boolean", "description": "True for an event to wait for rather than an action to take."},
    },
    "required": ["text", "note", "date", "t", "wait"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "nation": {"type": "string"},
        "patch": {"type": "string", "description": "EU4 patch the guide is for, e.g. '1.36'. 'unknown' if not stated."},
        "summary": {"type": "string", "description": "One short sentence: patch and the years covered."},
        "video": {
            "type": "object",
            "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "channel": {"type": "string"}},
            "required": ["id", "title", "channel"],
            "additionalProperties": False,
        },
        "phases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "era": {"type": "string", "description": "Date range of the phase, e.g. 'Aug 1450 to Oct 1452'."},
                    "jump": {"type": "string", "description": "Short label for the jump row, usually the start year."},
                    "intro": {"type": "string", "description": "One or two sentences of context. Empty string if none."},
                    "steps": {"type": "array", "items": STEP},
                },
                "required": ["name", "era", "jump", "intro", "steps"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["nation", "patch", "summary", "video", "phases"],
    "additionalProperties": False,
}


def slug(nation: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", nation.lower()).strip("-")


def validate(g: dict) -> None:
    """Light structural check, so a hand-written guide fails with a clear message."""
    for key in SCHEMA["required"]:
        if key not in g:
            raise ValueError(f"guide is missing '{key}'")
    for pi, p in enumerate(g["phases"]):
        for key in ("name", "era", "jump", "steps"):
            if key not in p:
                raise ValueError(f"phase {pi} is missing '{key}'")
        for si, s in enumerate(p["steps"]):
            for key in ("text", "date", "t"):
                if key not in s:
                    raise ValueError(f"phase {pi} ('{p['name']}') step {si} is missing '{key}'")
            if not isinstance(s["t"], int):
                raise ValueError(f"phase {pi} step {si}: 't' must be whole seconds")


def render(json_path: Path) -> Path:
    g = json.loads(json_path.read_text(encoding="utf-8-sig"))  # tolerate a BOM from Windows editors
    validate(g)
    tpl = resources.files("eu4guide").joinpath("template.html").read_text(encoding="utf-8")
    data = json.dumps(g, ensure_ascii=False).replace("</", "<\\/")
    page = tpl.replace("__TITLE__", html.escape(f"{g['nation']} Playbook")).replace("/*GUIDE*/null", data)
    out = json_path.with_suffix(".html")
    out.write_text(page, encoding="utf-8")
    render_index(json_path.parent)
    return out


def render_index(folder: Path) -> Path:
    rows = []
    for f in sorted(folder.glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8-sig"))
        steps = sum(len(p["steps"]) for p in g["phases"])
        rows.append(
            f'<li><a href="{html.escape(f.stem)}.html">{html.escape(g["nation"])}</a>'
            f'<span>{html.escape(g.get("patch", ""))} · {steps} steps · '
            f'{html.escape(g["video"].get("channel", ""))}</span></li>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>EU4 Playbooks</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=IBM+Plex+Sans:wght@400;500&display=swap">
<style>
:root{{--bg:#f3f2ef;--fg:#22201f;--muted:#6b6560;--line:#dcd8d2;--accent:#8e1b24;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--bg:#17161a;--fg:#ece8e3;--muted:#a39d96;--line:#36333a;--accent:#e0676f;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 "IBM Plex Sans",system-ui,sans-serif;padding:32px max(16px,env(safe-area-inset-left,0px))}}
main{{max-width:640px;margin:0 auto}} h1{{font-family:Cinzel,Georgia,serif;color:var(--accent);margin:0 0 16px}}
ul{{list-style:none;padding:0;margin:0;border-top:1px solid var(--line)}}
li{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:10px 2px;border-bottom:1px solid var(--line)}}
a{{color:var(--fg);font-weight:500}} span{{color:var(--muted);font-size:.85rem}}
</style></head><body><main><h1>EU4 Playbooks</h1><ul>
{chr(10).join(rows)}
</ul></main></body></html>"""
    out = folder / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
