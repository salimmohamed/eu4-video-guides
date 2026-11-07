# Writing an EU4 playbook from a timeline

You get `timeline.md` for one Europa Universalis IV guide video. It is the transcript in 30-second
blocks. Each block heading gives the video time, `t=<seconds>`, and the in-game date that was on
screen at that moment. Turn it into a playbook: a checklist a player keeps open beside their game,
grouped by era, where every step says when it happened in-game and links back to the moment in the video.

## What goes in

- Every concrete instruction the narrator gives, in the order a player would do it. Keep the
  specific choices: which estate privileges, which advisors, rivals, allies, missions, event options,
  government reforms by tier, idea groups, policies, casus belli, what to take in each peace deal and
  the aggressive expansion they aim for, buildings, great projects.
- Conditions and alternatives go in the step's `note` ("If France refuses, ally Castile").
- Things the player waits for, rather than does, become steps with `"wait": true`. These are events,
  deaths, alliances breaking, or a rival getting weak ("Aragon releases Naples").
- Benchmarks the narrator shows (income, army size, buildings, realm at the end date) go in their own
  phase near the end.
- Long-term advice for after the covered period (later idea groups, later reform tiers, which regions
  to go for next) goes in a final "Later picks" phase.

## What stays out

- The intro, the outro, sponsor reads, requests to like and subscribe, and the nation's backstory.
  Keep a bonus from the intro only if it tells the player what to do.
- Anything that wasn't in the video. Don't add your own EU4 strategy. You may fix names.
- Narration of what happened in the narrator's game that isn't advice. Turn it into advice where the
  lesson is clear ("He declared while Aragon was fighting France" becomes "Declare on Aragon while
  they're at war with a bigger power").

## Dates and timestamps

- `date` is the in-game date on screen for the block where the step is said. Use the month and year
  ("Nov 1444"), or the day too when it marks an exact trigger ("25 Aug 1450"). If the block says
  "not visible", use the nearest visible date before it, or the year alone.
- Many guides open with an endgame preview (for example the realm in 1507) before going back to 1444.
  Don't let that preview date leak into the opening steps.
- `t` is the block's seconds value. Add up to 25 seconds if the instruction clearly sits late in the
  block. Steps within a phase should mostly have rising `t`, but order them as a player would do them.

## Phases

- Usually 7 to 12 phases. Split them at the natural turning points of the run, such as day-one setup,
  first missions, each major war or war pair, consolidation, a midgame economy phase, finishing a
  formable, benchmarks, and later picks.
- `name` is short and specific ("War with Naples"). `era` is the date range ("Aug 1450 to Oct 1452").
  `jump` is a compact label for the jump row, usually the start year ("1450"), or "Later".
- `intro` is one or two sentences on what this phase is about or what triggers it. Leave it empty if
  there's nothing to add.

## Groups

Each phase holds `groups`, and each group holds steps.

- Setup phases (day one, between wars, economy stretches) are grouped by topic, with names that fit this
  nation and era: "Estates", "Advisors (level 1)", "Diplomacy", "Curia", "Army and navy", "Trade",
  "Missions", "Subjects". Pick labels for what the nation actually does. There's no fixed list. Set
  `"ordered": false`.
- War phases are one group named "In order" with `"ordered": true`, because the order matters there.
  A long phase can have a few ordered groups, one per thread ("Naples again", "Venice").
- Benchmarks can be one group with an empty name.

## Steps and chains

One checkbox per real milestone. Everything you do to get ready for that milestone goes inside one
checkbox as a `chain`.

- A `chain` is a list of sub-steps done in order, and each one is ticked separately. Use it whenever
  one thing has to happen before another: `"who": "France", "chain": ["Improve relations", "Ally"]`.
- Prep before a war or event is one checkbox: `"who": "Get ready", "chain": ["Rival Naples", "Wait for
  them to rival back", "Excommunicate them if you can", "Raise army maintenance", "Take loans", "Hire
  the Papal Swiss Guard", "Take the mission for a 62-tradition general"]`. Don't split it into
  several checkboxes.
- Milestones stay separate checkboxes: the event you wait for, the declaration, the peace deal.
- `who` is an optional bold lead-in: a nation ("Austria"), "Rivals", "Get ready", "Peace". With a
  single action, use `who` plus `text` ("Austria" plus "Ally"). Use `text` alone for a plain step.
- Peace deals with several things to take are a chain under `"who": "Peace"`.

## Era card (`loadout`)

- `tech` is the military tech you'd have on time for that era: 3 in 1444, 4 by 1453, 5 by 1466, 6 by
  1479, 7 by 1492, 8 by 1505, 9 by 1518, then one every 13 years. The page looks up the army half-stack
  from Raven's chart. Use `tech: 0` for day one, benchmarks and later picks, which hides the card.
- `note` is one line about the army in that era, such as when artillery joins. Leave it empty
  otherwise. The page already says when a tech is a big jump.
- `have` lists what the player should have by the start of the era: idea groups, reform tiers,
  allies, subjects, missions. Always name the actual pick in brackets: "Tier 2 reform (Commercial
  Mission for a money run, Mission of Protection for crusades, External Mission for conquering
  Europe. He took Commercial)". Keep it to 2 to 4 items.

## Nation panels

`panels` holds mechanics only this nation has that matter all game, shown above the first era. Examples
are the Curia for the Pope, janissaries for the Ottomans, the Mandate for Ming and the shogunate for
Japan. Each item has a short bold `label` and a `text`. Most nations have one panel, and some have none.
One-off actions still go in the steps.

## Writing

- Steps are short imperatives a player can act on: "Rival Provence and one other (he picks Savoy)".
  Put the reason or detail in `note`.
- Auto-captions mangle EU4 names. Fix them from context: provinces, nations, estates, privileges,
  missions, reforms, events, ideas. Examples: "duckets" is ducats, "Aon" is Avignon, "pracy" is
  primacy, "Diplo vasil" is diplo-vassalize, "galys" is galleys.
- Plain words. No em dashes. Use commas or separate sentences.
- `summary` is one sentence, such as "EU4 1.36, 1444 to 1507." `patch` comes from the title or the
  narration, otherwise "unknown".
- `video` is the id, title and channel from the top of the timeline.
