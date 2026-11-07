---
name: eu4-guide
description: Turn an EU4 (Europa Universalis IV) YouTube guide into a dated playbook in guides/. Use when the user gives a YouTube link and asks for a playbook, guide, checklist or notes for a nation, or asks to redo or fix an existing guide.
---

# Make an EU4 playbook from a video

1. Build the timeline. This downloads the video, finds the date box and reads the date. The first run on
   a long video takes several minutes, so run it in the background and wait for it to finish:

   ```
   uv run eu4guide timeline <url>
   ```

   Check the "Date read in N/M frames" line. If fewer than about half the frames were read, look at
   `videos/<id>/dates.txt`. If the date box search failed, save a frame with
   `uv run eu4guide frame <url> <seconds>`, look at it, and re-run with `--crop w:h:x:y`.

2. Read `eu4guide/instructions.md` and the example guide `guides/papal-states.json`. Then read all of
   `videos/<id>/timeline.md`. Don't skim it. Steps come from everywhere in the video.

3. Write `guides/<nation-slug>.json` following the instructions. `uv run eu4guide schema` prints the
   exact format. The slug is lowercase with hyphens, like `papal-states` or `castile`.

4. Render it and open it:

   ```
   uv run eu4guide render guides/<nation-slug>.json --open
   ```

5. Tell the user how many phases and steps the guide has, and the date range it covers. Also mention
   anything you weren't sure about, such as names the captions garbled that you couldn't work out, or
   long stretches with no visible date.
