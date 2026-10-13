# GPT Job Contract

A ChatGPT production run creates exactly one new JSON file under `jobs/`.
Creating that file triggers `.github/workflows/auto-produce.yml` automatically.

## Required behavior for GPT

1. Discover a promising Korean manhwa/manga title using current public metadata/research.
2. Prefer a strong premise suitable for a 35–60 second English Short.
3. Never scrape or download unauthorized chapter scans.
4. Only attach visual assets that have one of these declared rights bases:
   - `owned`
   - `licensed`
   - `official_promotional`
   - `creator_authorized`
5. Write an original English narration designed to make viewers want to discover/read the work rather than replace it.
6. Use a strong cold-open hook; do not start with the title.
7. End with the title reveal or a natural discovery CTA.
8. Build 8–18 scenes using the available approved assets. Assets may repeat with different crops/motion.
9. Target 35–60 seconds.
10. Create a unique `video_id`; never overwrite an older job.

## Job JSON

```json
{
  "video_id": "2026-10-14-series-slug-001",
  "series": "Series Name",
  "source_page": "https://...",
  "angle": "One-sentence creative angle",
  "youtube_title": "Curiosity-driven YouTube title",
  "description": "Short original description with series title and discovery context.",
  "script": "Full English narration...",
  "assets": [
    {
      "id": "cover",
      "url": "https://.../official-image.jpg",
      "rights_basis": "official_promotional",
      "source_url": "https://official-publisher.example/..."
    }
  ],
  "scenes": [
    {
      "asset_id": "cover",
      "duration": 2.4,
      "motion": "zoom_in",
      "caption": "HE SHOULD HAVE DIED."
    }
  ],
  "review_status": "awaiting_render"
}
```

## V1 motion values

- `static`
- `zoom_in`
- `zoom_out`
- `pan_left`
- `pan_right`

## Review lifecycle

The user is the only publication gate.

- PASS: preserve the render and mark it approved for publishing.
- FAIL: create a new revision job. Do not overwrite the failed render.
- FAIL feedback should modify only the necessary elements (hook, pacing, narration, visuals, etc.) unless the user requests a full restart.

No video should auto-publish before the user's PASS.
