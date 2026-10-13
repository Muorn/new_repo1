# Style Reference V2 — Evidence-Driven Manhwa Recap

References analyzed:

- Manhwa Fresh — “He Copies the Skills of Any Hunter with a Single Touch! - Manhwa Recap”.
- YouTube Short `63bSa-7EJpo` supplied by the user as a short-form editing benchmark.

This file captures reusable editing principles only. Do not copy script wording, assets, music, or branding.

## What makes the references work

### 1. Immediate proof

The first seconds do not rely on one poster. The hook is visually validated by several relevant action/reaction images.

### 2. Narration and visual alignment

When narration mentions a character reaction, power, threat, named entity, or lore point, the corresponding visual appears immediately. The art functions as evidence, not decoration.

### 3. Short-form cadence is faster than long recap cadence

For Shorts, target **1.0–1.8 seconds per visual beat** most of the time. Action/list sequences can go to 0.8–1.2s; emotional/reveal frames may hold 1.8–2.2s.

Hard rule: no visual should remain unchanged for more than 2.2s without a meaningful punch-in, reframe, pan, or new cut.

### 4. Three-stage panel treatment

When one approved image contains enough information, treat it as multiple purposeful shots:

1. establishing/full context;
2. subject crop;
3. reaction/detail crop.

The crop must communicate a different fact or emotion each time.

### 5. Motivated motion

- subtle 1.03–1.12x drift on calm frames;
- directional pan follows action/reading direction;
- punch-in on realization/reveal;
- brief shake on impact;
- zoom-out for a reveal or scale change.

### 6. Vertical background treatment

When a useful panel is horizontal or narrow, do not stretch it. Use:

1. blurred/color-matched duplicate as a full 9:16 background;
2. sharp original panel centered on top;
3. motion applied primarily to the sharp foreground panel.

This avoids black bars and preserves artwork quality.

### 7. Typography hierarchy

Narration captions should normally be **1–2 words**, with occasional 3–4 word bursts when needed for readability. Separate editorial callouts are reserved for important facts and should never become constant clutter.

Examples:

- ONLY READER
- THE CATCH
- FIRST SCENARIO
- HE KNOWS THE END

Keep captions center-locked slightly above the lower third so YouTube UI does not cover them.

### 8. Audio rhythm

Most transitions should be hard cuts. SFX should align with an actual visual event. Music must stay below narration and can change mood with the story arc.

Suggested mix target:

- narration: dominant, roughly -1 dB peak target;
- BGM: roughly -18 to -22 dB under voice;
- SFX: roughly -12 dB and used selectively.

### 9. Short-form narrative arc

A useful 45–55 second structure:

1. Hook / core trauma or impossible premise.
2. Rapid factual proof.
3. Escalation / conflict.
4. Relief or contrast beat when available.
5. Twist / cliffhanger at the peak.
6. End without a long outro; loop cleanly into the opening.

## V2 benchmarks

- 40–55 seconds preferred while the format is being learned.
- 18–30 meaningful visual beats for a ~45–55 second Short.
- 1.0–1.8 second average shot/reframe duration.
- <=2.2 seconds without a cut or meaningful reframe.
- >=8 distinct approved visual sources where practical.
- no single asset should dominate the video.
- 1–2 words per subtitle burst by default.
- editorial callouts in <=35% of scenes.
- every major factual beat requires an `evidence_ref`.
- every named entity in narration should map to a relevant asset/focal crop where possible.

## What we will do better than the references

- visible evidence discipline: every major claim is grounded before scripting;
- less redundant narration: voice adds context/stakes instead of merely describing the picture;
- stronger mobile-safe compositions;
- fewer repetitive flashes;
- deliberate source-quality checks before deep crops;
- automated creative QA before the user ever sees a candidate;
- scene metadata records the fact and evidence source for later auditing.

## Reject conditions

Do not send a candidate to the user if:

- visuals obviously loop;
- two posters are stretched across the whole runtime;
- narration and visuals frequently disagree;
- a claim has no evidence reference;
- captions cover the focal subject;
- average visual beat exceeds 2.2s without a clear reason;
- horizontal panels are stretched instead of framed intelligently;
- the renderer technically succeeded but the edit still feels like a slideshow.
