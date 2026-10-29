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

- Once location is allowed, the home page is **Around you**: places by distance with a one-line
  story teaser, so nothing needs typing. ◎ refreshes it.
- **☰** holds the switches: which kinds of place to show (filters pins, Nearby and Lead-me, kept
  on the phone) and **Walk with me**, which watches your position and, within about 80 m of an
  unvisited place with a story or a well-known person, vibrates, shows a card and says one line.
  At most one alert per 40 seconds. Works while the page is open; phones suspend web pages when
  the screen locks, so background alerts would need a native wrapper.

- The current place pulses red on the map, above the clusters, so a tap in the panel can be found on the map.
- **Tours** are ordered lists of places, numbered on the map with a dashed line and leg distances.
  Build one from any place page (**+ Tour**), reorder in ☰ → Tours, save it on the phone with a name
  (40 characters) and a description (100 words). **Share link** carries the whole tour in the URL,
  so nothing is uploaded anywhere and the recipient can keep it. Curated tours ship in
  `site/data/tours.json` (`tools/seed_tours.py` writes examples); adding one is a commit, which is
  the approval step. There is no server, so there is no public user content to moderate.

- **Settings** (☰): which kinds of place may raise a walk alert, whose places (anyone / well known /
  famous, by Wikipedia sitelink count), only places with a story, alert distance, minimum gap,
  speak and vibrate switches, voice speed. All kept on the phone (`strand.settings`).
- **Offline** is opt-in. `sw.js` always keeps the app shell, the indexes and whatever has been seen
  (map tiles up to 4,000, Wikimedia images and summaries up to 1,500). The **Keep London on this
  phone** switch downloads every person and story file (about 30 MB) through ordinary fetches the
  worker stores; turning it off removes them and the tile cache but keeps the shell. Leaflet and
  markercluster are vendored under `site/vendor/` for the same reason. Map tiles are only cached as
  looked at; bulk tile download is against the OpenStreetMap tile policy.

- **Installable.** `manifest.webmanifest` + icons (`site/icons/`, drawn by Pillow in a one-off
  script); on Android/desktop Chrome the menu shows **Install Strand** once the browser offers
  it; on iPhone the menu explains Share → Add to Home Screen. Installed, it opens full-screen,
  keeps its caches and settings, and the walk screen-lock survives better.

## Licences (what we use, and what releasing an app needs)

- **Wikidata** (places, people, relations, dates): CC0. No conditions.
- **Wikipedia** text (leads shown on person pages, and the material the stories are written
  from): CC BY-SA 4.0. Attribution and share-alike: the stories are derived works and are
  released under CC BY-SA 4.0 with the source article credited (the page says so under each).
- **Wikimedia Commons** images: each file has its own licence (mostly CC BY-SA, CC BY or public
  domain), attribution per image. The page links the file; an app must show the credit.
- **OpenStreetMap** data: ODbL, attribution required (shown on the map). The **tile servers** at
  tile.openstreetmap.org are run by the OSM Foundation for the community; their policy forbids
  bulk download and heavy or app-distributed use. A released app needs its own tiles: a
  commercial provider (MapTiler, Stadia, Thunderforest) or self-hosted vector tiles (Protomaps).
- **Leaflet** (BSD-2) and **Leaflet.markercluster** (MIT): keep the notices.
- **Wikipedia/Wikidata APIs**: free to call with a descriptive User-Agent and reasonable rate.

## Known gaps

- The place-specific anecdote (why this person matters *here*) is not structured data anywhere.
  The page shows the relation and dates, then the Wikipedia lead.
- Wikidata residence data is thin: ~1,000 dated `lived` rows for the whole box.
- Places are deduplicated by Wikidata item, so a plaque and the house it is on are two pins.
