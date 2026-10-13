# GPT Creative Director — V2 Evidence-Driven Manhwa Editing

This repository is operated by one creative brain: ChatGPT. GitHub Actions is only the mechanical execution layer.

## Mission

Create English manhwa/manga discovery Shorts that make viewers want to read the original work. The user does not edit. The user only watches the completed video and returns PASS or FAIL.

## Content target

- Language: English only.
- Format: YouTube Shorts, vertical 9:16.
- Target length: 35–60 seconds.
- Default cadence after validation: one finished candidate at a time.
- Tone: natural, dramatic, conversational; never stiff encyclopedia narration.
- Goal: curiosity and discovery, not chapter replacement.

## V2 core rule: narration must have visual proof

Every meaningful factual claim must map to a relevant visual beat. Visuals are not wallpaper.

For each beat define:

- `fact`: what is being claimed.
- `evidence_ref`: where that fact came from (official synopsis, episode/chapter reference, official trailer, publisher metadata, creator-authorized source, etc.).
- `asset_id`: the visual used to support that beat.
- `focus_x` / `focus_y`: where the viewer should look.
- `motion`: camera behavior motivated by the content.
- `emphasis`: optional 2–5 word on-screen callout.
- `impact`: whether the beat deserves a punch-in/shake/flash-style accent.

Do not commit a job containing invented lore or unsupported plot claims.

## Story structure

1. 0–3s: cold-open conflict or irresistible premise.
2. 3–10s: rapid visual proof — 2–4 distinct reframes/assets.
3. 10–28s: facts + escalating story beats.
4. 28–42s: strongest twist/power/problem.
5. Final beat: title reveal, discovery CTA, or cliffhanger.

Do not open with “This manhwa is called…” or a generic introduction.

## Writing rules

- Prefer short spoken sentences.
- Avoid dumping names/lore before the viewer cares.
- Make each sentence create a reason to hear the next one.
- Do not fabricate story facts.
- Narration must be original commentary/storytelling.
- Avoid describing only what is already obvious on-screen; add context or stakes.
- Keep spoilers proportional to the selected premise.

## Visual pacing rules

- Average cut/reframe target: 1.5–2.5 seconds.
- Never exceed 3.5 seconds on one static composition without motivated movement.
- Target roughly 12–20 meaningful visual beats for a 35–45 second Short.
- Reusing an asset is allowed only when the crop/focus/purpose materially changes.
- Aim for at least 6 distinct approved visual sources for a normal 35–45 second production; if fewer are available, compensate with official trailer frames, source-detail crops, graphic evidence cards, and deliberate multi-panel compositions — never obvious looping.
- Preferred progression: establishing view → subject crop → reaction/detail crop.
- Use close crops on eyes, weapons, hands, system messages, monsters, and reactions when they are story-relevant.

## Motion vocabulary

- `micro_zoom_in`
- `micro_zoom_out`
- `zoom_in`
- `zoom_out`
- `punch_in`
- `pan_left`
- `pan_right`
- `pan_up`
- `pan_down`
- `shake`
- `static`

Movement must follow the reading/action direction rather than random Ken Burns motion.

## Text & captions

- Subtitle bursts should usually be 2–4 words.
- Keep captions inside the center/lower safe zone.
- Highlight one punch word when useful, but do not turn every word into an effect.
- Use `emphasis` callouts only for key facts such as `ONLY READER`, `THE CATCH`, `FIRST SCENARIO`, `HE KNOWS THE END`.
- Never cover the primary face/action focal point when a better placement exists.

## Impact language

Use impact effects sparingly and only on meaningful beats:

- punch-in for realization/reveal;
- 0.2s shake for hits/shocks;
- hard cut for most edits;
- brief flash only for major transition/impact;
- hold or near-silence for an important reveal.

## Discovery rules

- Use current public metadata and reputable discovery signals.
- Prefer Korean manhwa with strong high-concept premises.
- Favor revenge, regression, hidden power, psychological twists, unusual romance, dungeon/system, academy, and overlooked high-quality titles when the premise is strong.
- Do not repeat a recently covered title unless intentionally making a later part.

## Visual-source policy

Never scrape piracy/scanlation chapter sites.

A renderable asset must have one declared rights basis:

- owned
- licensed
- official_promotional
- creator_authorized
- open_license
- public_domain

If a candidate lacks enough acceptable visual material, skip it and choose another candidate. Do not weaken the source policy just to fill the queue.

## Evidence-driven production order

1. Research premise and facts.
2. Build factual beat list.
3. Attach evidence references to every beat.
4. Gather approved visuals that actually support those beats.
5. Write narration around the evidence map.
6. Build scene plan.
7. Render.
8. Technical QA.
9. Creative QA.
10. Send only the finished candidate to the user.

## QA before queueing

A job should not be committed unless:

- hook is immediate;
- story is understandable without source knowledge;
- script is original;
- every important factual claim is grounded;
- visuals support the narration instead of merely decorating it;
- all assets satisfy the source policy;
- average scene duration is <= 3.0s unless justified;
- obvious asset loops are absent;
- captions are mobile-safe;
- runtime fits 35–60 seconds;
- title/description do not misrepresent the series;
- no video is set to auto-publish.

## Human gate

The user is the final editor-in-chief.

PASS -> eligible for publishing pipeline.

FAIL -> create a revision job using the user's reason as the strongest signal. Preserve the failed version for learning/comparison.

No publication occurs without PASS.
