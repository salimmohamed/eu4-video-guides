# EU4 video guides

Turns Europa Universalis IV guide videos on YouTube into playbooks. Each playbook is a checklist grouped
by era, where every step has the in-game date shown in the video and a timestamped link back to it.
`uv run eu4guide --help` lists the commands.

## Layout

- `eu4guide/`: the `eu4guide` CLI (`uv run eu4guide --help`).
  - `video.py` downloads with yt-dlp into `videos/<id>/`. That folder is gitignored and is a cache.
  - `dates.py` finds the date box automatically (`calibrate`), OCRs it every N seconds and drops misreads.
  - `timeline.py` writes `videos/<id>/timeline.md`, which is the captions in 30s blocks tagged with the in-game date.
  - `guide.py` holds the guide JSON schema and validation, and `build_site()` renders every guide plus the reference charts into `site/` using `site.html`.
  - `generate.py` writes a guide from a timeline with the Claude API (`run` command).
  - `instructions.md` is how to write a guide. The API prompt and the Claude Code skill both use it.
- `guides/`: one `<nation>.json` per guide. The file name is the tab's URL slug (`#papal-states`). `papal-states.json` is the
  example that both writing paths imitate.
- `reference/`: shared charts shown under every nation, listed in `references.json`. `army.json` is
  Raven's army chart as data. Each era card looks up its half-stack there from the era's `loadout.tech`.
- Site: https://salimmohamed.github.io/eu4-video-guides/ (public repo). `.github/workflows/pages.yml` rebuilds it on push to main
  when guides, reference or the site template change. The build is stdlib only. `site/` is gitignored.
- `.claude/skills/eu4-guide/`: the in-session way to make a guide without an API key.

## Notes

- To change how guides are written, edit `eu4guide/instructions.md`. Don't change the API prompt or the skill separately.
- To change how the site looks, edit `eu4guide/site.html`, then check it with `uv run eu4guide build --open`.
- The OCR cache is `videos/<id>/dates_raw.json`, keyed on crop and interval. The detected crop is in `crop.txt`.
- Downloaded videos and transcripts stay out of git. They're other people's content.
