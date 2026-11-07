"""Write a guide from a timeline with the Claude API (needs `pip install eu4-video-guides[ai]`)."""
import json
import sys
from importlib import resources
from pathlib import Path

from .guide import GUIDES, SCHEMA, slug, validate

MODEL = "claude-opus-5-5"


def system_prompt() -> list[dict]:
    instructions = resources.files("eu4guide").joinpath("instructions.md").read_text(encoding="utf-8")
    example = GUIDES / "papal-states.json"
    text = instructions
    if example.exists():
        text += ("\n\n## Example of a finished guide\n\nThis is the Papal States guide, written from a "
                 "48-minute video. Match its level of detail and style.\n\n```json\n"
                 + example.read_text(encoding="utf-8") + "\n```\n")
    # Stable across runs, so it is cached after the first guide.
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def generate(timeline: Path, nation: str | None = None, model: str = MODEL) -> Path:
    try:
        import anthropic
    except ImportError:
        sys.exit("The API step needs the anthropic package: uv sync --extra ai")

    ask = "Write the playbook for this video."
    if nation:
        ask += f" The nation is {nation}."
    client = anthropic.Anthropic()
    try:
        with client.beta.messages.stream(
            model=model,
            max_tokens=64000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            thinking={"type": "adaptive"},
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
            system=system_prompt(),
            messages=[{"role": "user", "content": [
                {"type": "text", "text": timeline.read_text(encoding="utf-8")},
                {"type": "text", "text": ask},
            ]}],
        ) as stream:
            print(f"Writing the guide with {model} (a few minutes for a long video)...")
            msg = stream.get_final_message()
    except anthropic.AuthenticationError:
        sys.exit("No valid Claude API credentials. Set ANTHROPIC_API_KEY, or use the Claude Code "
                 "skill instead (see README).")
    except anthropic.APIStatusError as e:
        sys.exit(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("Couldn't reach the Claude API. Check your connection.")

    if msg.stop_reason == "refusal":
        sys.exit("The model declined this request.")
    if msg.stop_reason == "max_tokens":
        sys.exit("The guide was cut off at the output limit. Try a shorter video.")
    text = next(b.text for b in msg.content if b.type == "text")
    g = json.loads(text)
    validate(g)
    GUIDES.mkdir(exist_ok=True)
    out = GUIDES / f"{slug(g['nation'])}.json"
    out.write_text(json.dumps(g, indent=2, ensure_ascii=False), encoding="utf-8")
    u = msg.usage
    print(f"Tokens: {u.input_tokens} in, {u.cache_read_input_tokens or 0} cached, {u.output_tokens} out")
    return out
