# EU4 video guides

I learn EU4 nations from YouTube guides, but I kept losing my place. The narrator says "declare on Naples now" and I'm sitting in 1447 wondering if that was 1450 or 1460 in his game. This turns a guide video into a checklist I can keep open next to the game. Every step has the in-game date it happened in the video and a link back to that moment.

It reads the date in the top-right corner of the screen every 5 seconds, lines it up with the video's captions, and then a model writes the steps from that.

Example: [Papal States](guides/papal-states.html), from The Red Hawk's 1.36 guide. 127 steps over 11 eras, 1444 to 1507.

## What you need

- [uv](https://docs.astral.sh/uv/)
- ffmpeg on your PATH (`winget install ffmpeg`, `brew install ffmpeg` or `apt install ffmpeg`)
- One of these, for writing the guide:
  - Claude Code, which uses the skill in this repo. No API key needed.
  - A Claude API key in `ANTHROPIC_API_KEY`, for the fully automatic `run` command.

```
git clone git@github.com:salimmohamed/eu4-video-guides.git
cd eu4-video-guides
uv sync --extra ai
```

## Making a guide

With Claude Code, open it in this folder and ask:

```
make a playbook for https://youtu.be/<video>
```

With an API key, one command does everything and opens the result:

```
uv run eu4guide run https://youtu.be/<video>
```

Either way it ends up in `guides/<nation>.json` and `guides/<nation>.html`, and `guides/index.html` lists them all.

The timeline part for a 48 minute guide took about 3 minutes on my machine, mostly downloading the video. It read the date in 578 of 585 frames. Everything is cached in `videos/`, so running it again on the same video is quick.

## Commands

| Command | What it does |
|---|---|
| `eu4guide timeline <url>` | Download, find the date box, read the dates, write `videos/<id>/timeline.md`. No API needed. |
| `eu4guide run <url>` | `timeline`, then write the guide with the Claude API, then render it. |
| `eu4guide render [guide.json]` | Turn guide JSON into HTML. Renders every guide if you don't pass one. |
| `eu4guide frame <url> <seconds>` | Save one full frame, for checking the date box by hand. |
| `eu4guide schema` | Print the guide JSON schema. |

`--every 10` reads the date less often, which is faster. `--crop w:h:x:y` skips the automatic search for the date box.

## How it works

1. yt-dlp downloads the video without audio, the English captions and the title.
2. It grabs 10 frames across the video and runs OCR on the top-right corner to find where the date sits. That way it works at different UI scales without setting anything up.
3. ffmpeg crops just the date box every 5 seconds and RapidOCR reads it. The month matching is loose because OCR turns "1 April 1507" into "1Apr1507" and "October" into "0ctober" a lot. Misreads get dropped if the year is far off from the readings around it.
4. The captions go into 30 second blocks, each tagged with the date on screen. That's `timeline.md`.
5. A model turns the timeline into steps grouped by era, following `eu4guide/instructions.md` and using the Papal States guide as the example.
6. `render` puts the JSON into `eu4guide/template.html`. Ticks are saved in your browser, and the page prints cleanly.

## Known limits

- It needs English captions. Videos without them stop with an error.
- The date has to be readable in the top-right corner. If the narrator spends long stretches in menus or the ledger, those parts show "not visible" and the guide uses the nearest date before them.
- Auto captions get EU4 names wrong a lot ("duckets", "Aon" for Avignon). The model fixes most of them from context, but it's worth a skim.
- I've only tested it on one of The Red Hawk's videos at 1080p so far.
- I haven't run the `run` command end to end yet since I don't have an API key set up. The Claude Code route is the one I've used.

Downloaded videos, frames and transcripts stay local in `videos/`, which is gitignored. The guides link back to the original videos and credit the channel.

## License

MIT
