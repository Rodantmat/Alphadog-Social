# QA rules added 2026-11-20 (Zion Part 3)
- Title/overlay text must fit the frame (thumbnail title was clipped at the right edge: auto-fit text width; check any text bbox <= width-120).
- Plan stills per segment against the real picture content (contact sheet), never blind assignment (culvert photos over the tunnel cold open).
- Repetition gate: each picture <=2 uses (important historical <=3), <=3 different repeated pictures per video; Shorts/Stories use pictures disjoint from each other.
- Captions must not split on abbreviations (St., Mr., Dr.).
- Every Short/Story must carry an audio stream; end card to the full film is phone-safe.

## 2026-11-22 — text glyph defect (owner screenshot of IG Story)
- Never use ffmpeg drawtext with multi-line text (textfile/newlines render as tofu boxes). All hook/caption/end-card text is drawn with PIL into PNG overlays; ffmpeg only overlays them.
- Every rendered Short/Story must be checked on real frames (t=2 s and t=6 s minimum) before queueing: no tofu boxes, no clipped text, no black scan borders (stills are pre-cropped 4.5% per side).
- Safe area for 1080x1920: hook below y=288, captions end at y<=1440 (asserted in build_shorts_p3.py), no text in outer 108 px side margins.
- Long caption sentences are split at commas/conjunctions to <=95 chars; never a 6+ line box.
- Fixing a scheduled YouTube Short = upload the new one with the same publish_at (yt-p3-replace.yml), keep old private with publishAt cleared, drop old queued comment. Verify with yt-delete mode=list that old ones show publishAt None.

## 2026-11-25 Shorts length rule (data-driven)
- Zion-era public Shorts >=48 h old (n=22): <30 s median 986 views, 73% avg viewed; 30-40 s median 576, 60%; 40-60 s n=1. The three Part 3 Shorts at 40-47 s earned 159 / 0 / 0 views on YouTube.
- Rule: every new Short is 24-30 s (about 45-55 spoken words incl. hook), a numeric or object hook in the first line, and an end card. Stories 15-25 s. A Short over 32 s must be cut before queueing (QA analyzer: length gate).
- Replacement procedure now carries the queued link comment over to the new video (yt-p3-replace / yt-p4-replace).
