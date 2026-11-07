# EU4 video guides

Turns Europa Universalis IV guide videos on YouTube into playbooks. Each playbook is a checklist grouped
by era, where every step has the in-game date shown in the video and a timestamped link back to it.
See README.md for usage.

## Layout

- `eu4guide/`: the `eu4guide` CLI (`uv run eu4guide --help`).
  - `video.py` downloads with yt-dlp into `videos/<id>/`. That folder is gitignored and is a cache.
  - `dates.py` finds the date box automatically (`calibrate`), OCRs it every N seconds and drops misreads.
  - `timeline.py` writes `videos/<id>/timeline.md`, which is the captions in 30s blocks tagged with the in-game date.
  - `guide.py` holds the guide JSON schema and validation, and renders `template.html` into HTML plus `guides/index.html`.
  - `generate.py` writes a guide from a timeline with the Claude API (`run` command).
  - `instructions.md` is how to write a guide. The API prompt and the Claude Code skill both use it.
- `guides/`: one `<nation>.json` and a rendered `<nation>.html` per guide. `papal-states.json` is the
  reference example that both paths imitate.
- `.claude/skills/eu4-guide/`: the in-session way to make a guide without an API key.

## Notes

- To change how guides are written, edit `eu4guide/instructions.md`. Don't change the API prompt or the skill separately.
- To change how guides look, edit `eu4guide/template.html`, then run `uv run eu4guide render` to rebuild every guide.
- The OCR cache is `videos/<id>/dates_raw.json`, keyed on crop and interval. The detected crop is in `crop.txt`.
- Downloaded videos and transcripts stay out of git. They're other people's content.
