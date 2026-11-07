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

def _obj(props: dict, desc: str = "") -> dict:
    o = {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    if desc:
        o["description"] = desc
    return o


S = {"type": "string"}

STEP = _obj({
    "who": {"type": "string", "description": "Optional bold lead-in: a nation, 'Rivals', 'Get ready', 'Peace'. Empty string if none."},
    "text": {"type": "string", "description": "The action, imperative and specific. Empty string when the step is only a chain."},
    "chain": {"type": "array", "items": S, "description": "Sub-steps done in this order, each ticked separately. Empty for a single action. Use for prep before a war or event, and for 'improve relations, then ally'."},
    "note": {"type": "string", "description": "Why, a condition, or an alternative. Empty string if none."},
    "date": {"type": "string", "description": "In-game date on screen when it happened, e.g. 'Nov 1444' or '25 Aug 1450'."},
    "t": {"type": "integer", "description": "Video second where the narrator says it."},
    "wait": {"type": "boolean", "description": "True for an event to wait for rather than an action to take."},
})

GROUP = _obj({
    "name": {"type": "string", "description": "Topic label picked for this nation and era ('Estates', 'Diplomacy', 'Curia', 'In order'). Empty for no header."},
    "ordered": {"type": "boolean", "description": "True when the steps must happen in this order (wars). False for setup lists."},
    "steps": {"type": "array", "items": STEP},
})

LOADOUT = _obj({
    "tech": {"type": "integer", "description": "Military tech you'd have on time for this era. 0 hides the card (day one, benchmarks, later picks)."},
    "note": {"type": "string", "description": "One line about the army for this era, e.g. a big tech jump. Empty if none."},
    "have": {"type": "array", "items": S, "description": "What you should have by the start of this era. Name the actual pick in brackets, e.g. 'Tier 2 reform (Commercial Mission)'."},
})

PANEL = _obj({
    "title": S,
    "items": {"type": "array", "items": _obj({"label": S, "text": S})},
}, "A mechanic only this nation has, shown above the first era (the Curia for the Pope, janissaries for the Ottomans).")

SCHEMA = _obj({
    "nation": S,
    "patch": {"type": "string", "description": "EU4 patch the guide is for, e.g. '1.36'. 'unknown' if not stated."},
    "summary": {"type": "string", "description": "One short sentence: patch and the years covered."},
    "video": _obj({"id": S, "title": S, "channel": S}),
    "panels": {"type": "array", "items": PANEL},
    "phases": {"type": "array", "items": _obj({
        "name": {"type": "string", "description": "Short and specific, e.g. 'War with Naples'."},
        "era": {"type": "string", "description": "Date range, e.g. 'Aug 1450 to Oct 1452'."},
        "jump": {"type": "string", "description": "Short label for the jump row, usually the start year."},
        "intro": {"type": "string", "description": "One or two sentences of context. Empty string if none."},
        "loadout": LOADOUT,
        "groups": {"type": "array", "items": GROUP},
    })},
})

STEP_DEFAULTS = {"who": "", "text": "", "chain": [], "note": "", "wait": False}


def slug(nation: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", nation.lower()).strip("-")


def validate(g: dict) -> None:
    """Check structure and fill optional fields, so hand-written guides can leave them out."""
    for key in ("nation", "summary", "video", "phases"):
        if key not in g:
            raise ValueError(f"guide is missing '{key}'")
    g.setdefault("patch", "unknown")
    g.setdefault("panels", [])
    for pi, p in enumerate(g["phases"]):
        where = f"phase {pi} ('{p.get('name', '?')}')"
        for key in ("name", "era", "jump", "groups"):
            if key not in p:
                raise ValueError(f"{where} is missing '{key}'")
        p.setdefault("intro", "")
        p.setdefault("loadout", {"tech": 0, "note": "", "have": []})
        p["loadout"].setdefault("note", "")
        p["loadout"].setdefault("have", [])
        for gi, grp in enumerate(p["groups"]):
            grp.setdefault("name", "")
            grp.setdefault("ordered", False)
            for si, s in enumerate(grp["steps"]):
                for k, v in STEP_DEFAULTS.items():
                    s.setdefault(k, v)
                if "date" not in s or "t" not in s:
                    raise ValueError(f"{where} group {gi} step {si} needs 'date' and 't'")
                if not isinstance(s["t"], int):
                    raise ValueError(f"{where} group {gi} step {si}: 't' must be whole seconds")
                if not (s["text"] or s["chain"]):
                    raise ValueError(f"{where} group {gi} step {si} has neither 'text' nor 'chain'")


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
    army_file = REFERENCE / "army.json"
    army = json.loads(army_file.read_text(encoding="utf-8-sig")) if army_file.exists() else None
    page = (tpl.replace("/*GUIDES*/[]", embed(guides))
               .replace("/*ARMY*/null", embed(army))
               .replace("<!--REFERENCE-->", reference_html(refs)))
    index = out / "index.html"
    index.write_text(page, encoding="utf-8", newline="\n")
    (out / ".nojekyll").write_text("")
    return index
