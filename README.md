# AlphaDog Social

Automated Instagram + TikTok NBA picks account fed by the AlphaDog NBA system.

- `scripts/fetch_clip.py` - download an official post (NBA / team account), trim a 3-7 s clip, strip metadata, log credit in `clips/manifest.json`.
- `.github/workflows/fetch-clips.yml` - runs the above on `workflow_dispatch`.

All times Pacific. Clips are short, credited, and used only inside original graphics with commentary.
