"""The guide format (JSON schema, validation) and the static site build."""
import html
import json
import re
import shutil
from importlib import resources
from pathlib import Path

GUIDES = Path("guides")
REFERENCE = Path("reference")
SITE = Path("site")

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


def load(path: Path) -> dict:
    g = json.loads(path.read_text(encoding="utf-8-sig"))  # tolerate a BOM from Windows editors
    validate(g)
    g["slug"] = path.stem
    return g


def reference_html(refs: list[dict]) -> str:
    """Static markup for the shared charts, so they show without JavaScript."""
    if not refs:
        return ""
    e = html.escape
    figs = []
    for r in refs:
        src = f"reference/{e(r['file'])}"
        cap = f"\n      <figcaption>{e(r['caption'])}</figcaption>" if r.get("caption") else ""
        figs.append(
            f'    <figure>\n      <h3>{e(r["title"])}</h3>\n'
            f'      <a class="img" href="{src}" target="_blank" rel="noopener">'
            f'<img src="{src}" alt="{e(r.get("alt") or r["title"])}" loading="lazy" width="2000" height="1125"></a>'
            f"{cap}\n    </figure>")
    return ('<section id="reference" aria-labelledby="refh">\n    <h2 id="refh">Reference</h2>\n'
            "    <p>Charts that apply to every nation. Click one to open it full size.</p>\n"
            + "\n".join(figs) + "\n  </section>")


def build_site(out: Path = SITE) -> Path:
    """Render every guide in guides/ plus the reference charts into one static site."""
    guides = [load(p) for p in sorted(GUIDES.glob("*.json"))]
    guides.sort(key=lambda g: g["nation"])
    refs_file = REFERENCE / "references.json"
    refs = json.loads(refs_file.read_text(encoding="utf-8-sig")) if refs_file.exists() else []

    out.mkdir(parents=True, exist_ok=True)
    (out / "reference").mkdir(exist_ok=True)
    for r in refs:
        src = REFERENCE / r["file"]
        if not src.exists():
            raise FileNotFoundError(f"reference/references.json lists {r['file']}, but the file is missing")
        shutil.copyfile(src, out / "reference" / r["file"])

    def embed(obj) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    tpl = resources.files("eu4guide").joinpath("site.html").read_text(encoding="utf-8")
    page = tpl.replace("/*GUIDES*/[]", embed(guides)).replace("<!--REFERENCE-->", reference_html(refs))
    index = out / "index.html"
    index.write_text(page, encoding="utf-8", newline="\n")
    (out / ".nojekyll").write_text("")
    return index
