# Strand — ideas and future features

Logged for later; none of this is being built yet. Newest at the top.

## Meet-up tours (logged 09/11/2026, operator)

Say which tour you are doing, when and where it starts, and others can join and walk it with you.

**Core**
- Post a meet-up against an existing tour: start stop, date and time, expected length, group size cap.
- Join / leave; the organiser sees numbers, never other people's details beyond a display name.
- A meeting point is always the tour's first stop, a public place. Never a home or hotel.

**Enhancements suggested**
- **Guide-led meet-ups.** The guides whose shorts are in the app (Living London History, Look Up London,
  Joolz Guides…) can list paid walks on their own tours. Their videos are the shop window, the meet-up is
  the product, and it is the symbiosis that justifies asking creators for their blessing.
- **Safety first.** Daytime by default, minimum group of three before it is confirmed, report and block,
  optional verified organisers (a guide badge), no live location of anyone except the organiser during the
  walk, and only if they switch it on. Meet-ups disappear after they end.
- **Language of the walk** (English, Spanish, Italian…) as a filter: visitors look for people to walk with
  in their own language.
- **Pace and accessibility** tags taken from the tour (step-free, steep, length) so nobody is surprised.
- **"Join me now"**: an open meet-up starting within the hour near where you are, for solo travellers.
- **Shared progress**: the group's tour advances together; the organiser taps Next stop and everyone's
  phone shows the story (and can Listen) at the same time.
- **Pub at the end** as a standard option, linked to the food and drink layer.
- **After the walk**: rate the tour (taps only), keep it, follow the organiser for their next one.

**Needs**: accounts (sign in with Apple/Google), a small server (Cloudflare Worker + D1), moderation of
display names, terms of use. Same back end as published tours and the AI tier.

## Published tours

Today tours are private to the phone, shareable by link, and curated ones ship in `site/data/tours.json`.
Proposed model when a server exists (see the reply of 09/11):
- Publishing shares the **stop list and fixed tags only**; the description is written for it from the
  stops (no free text from the public, so nothing to moderate but the choice of stops).
- **Near-duplicates fold**: a tour sharing most of its stops with an existing one becomes a variant of it,
  not a new entry.
- **Promotion by use**: a published tour is only listed once people other than its author have walked or
  kept it; lists rank by completions. The operator can still feature or hide any tour.

## Food and drink

Only ~40 historic pubs, hotels and cafés come from Wikidata. Plan: an OpenStreetMap layer (free, ODbL)
of cafés, pubs, bars and restaurants, with historic and famous pubs flagged; planner options "a coffee
stop every couple of hours" and "end at a famous pub". Ratings (4.5★ default) need a paid provider
(Google Places or Tripadvisor) and their caching rules.

## AI

- Build time (free on the subscription, already used for stories and video placement): translations of
  every story, a children's version, link narration between consecutive stops.
- Live, per user (paid tier, needs an API key and a server): plan from a sentence, ask a question on the
  spot, re-plan when it rains or you are tired, narrate the walk from where you actually are.
