# Strand

Follow a life across a city, or change to someone it crossed. A map of every person Wikidata
ties to a point in London (commemorated, buried, born, died, lived, designed, depicted, founded,
made, owned, named after), each with a dated life timeline you can fly along and the people they
were related to, so you can switch strands at any time. The journey strip at the top is the path
you took: your own story through real ones.

Personal project, outside the `.one` regime (Plumbline-class, like habituate).

## Build the data

```
python -X utf8 tools/pull_wikidata.py --phase places      # ~6 min, 14 relation queries over a London box
python -X utf8 tools/pull_wikidata.py --phase placetypes  # types of every place, used to drop area-level pins
python -X utf8 tools/pull_wikidata.py --phase people      # ~20 min, detail/events/positions/associates per person
python -X utf8 tools/build_site_data.py                    # -> site/data/index.json + site/data/people/*.json
python -X utf8 tools/synthesise.py --limit 600             # stories: ~30s per ten places through the claude CLI
```

`synthesise.py` writes the short spoken-style story shown at the top of a place page
(`site/data/story/{qid}.json`), from the Wikipedia leads of the place and its people, via the
local `claude` CLI on the subscription. Places with the best-known people go first; rerunning
only writes places that have no story yet. Delete a story file to redo it.

The raw pull is cached under `data/raw/` (gitignored); delete a file to refetch it. The box and
the relation set are at the top of `pull_wikidata.py`. Another city is a different box.

Alumni and staff relations (`studied`, `worked`) are pulled but do NOT admit a person to the set:
every UCL graduate and BBC employee would swamp the pins. They still appear on the timeline of
people admitted by some other relation.

## Run

Live at https://dans-sdna.github.io/strand/ — deployed by `.github/workflows/pages.yml` on every push to master.


Static site. `python -m http.server 5260 --directory site` (registered as `strand` in the
one v.2 `.claude/launch.json`). Wikipedia summaries and thumbnails are fetched by the page on
demand from the Wikipedia REST API; nothing of Wikipedia is stored here.

## On the page

- Every place has an icon chosen from its Wikidata types (`iconOf` in `index.html`): statue,
  grave, church, house, theatre, pub, station, park, street and so on. Brown square, black line.
- **Listen** reads the story, or a sentence built from the relations where there is none, with the
  phone's own speech engine (no audio files, no server). On Lead-me it asks for the compass and
  says "to your left" / "straight ahead" when a heading is known.

## Known gaps

- The place-specific anecdote (why this person matters *here*) is not structured data anywhere.
  The page shows the relation and dates, then the Wikipedia lead.
- Wikidata residence data is thin: ~1,000 dated `lived` rows for the whole box.
- Places are deduplicated by Wikidata item, so a plaque and the house it is on are two pins.
