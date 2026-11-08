# AlphaDog Studio — Standing Editing Rules

Every owner critique becomes a rule here. Each rule has an ID. Rules marked **[AUTO]** are enforced in code by `qa_check.py`, which fails the build before anything is shown to the owner. Rules marked **[REVIEW]** go on the pre-delivery checklist and are checked against contact sheets.

Every episode inherits all rules. Never ask the owner to repeat one.

## Footage & imagery

| ID | Rule | Origin | Check |
|---|---|---|---|
| V1 | Real moving footage first (aerial/drone, hikers, places). Stills only for genuine historical photos. No "dancing photos", no Ken Burns paths over modern photos. | Owner, v1 | [AUTO] still share ≤ 20%, historical photos only |
| V2 | The picture must match the narration at that moment, with coherent sequence. No unrelated subject (e.g. a horse during the volcano part). | Owner, v1 | [REVIEW] per-shot sheet with the narration line |
| V3 | Never show the same image repeatedly in a short span. | Owner, v1 | [AUTO] same source+window not reused within 60 s, except deliberate recaps |
| V4 | **No flash shots.** No clip may show only a few frames before a cut. That covers cuts inside the source clip, not just our own cuts. Every visible scene lasts ≥ 2.5 s. | Owner, v2 | [AUTO] scene-cut detection on sources + final render; min visible scene 2.5 s |
| V5 | Maps, interviews and news clips play long enough to be fully seen. Maps play their whole animation plus a ≥ 1 s hold. Interviews play the full bite. | Owner, v2 | [AUTO] map shot ≥ animation length + 1 s |
| V6 | Scenery may be shorter, but not too short: target 4–8 s, minimum 3.5 s. | Owner, v2 | [AUTO] |
| V7 | Drone/FPV footage at a calm pace that matches the film (slowed to about 0.5–0.6×, smooth frames). | Owner, v2 | [AUTO] FPV/drone sources carry speed ≤ 0.6 |
| V8 | Less generic scenery (sunsets, skies, stars, clouds). Favour content: the actual place, the people, documents, maps, archival film. At most 1 generic shot per segment, and only when the line is atmospheric. | Owner, v2 | [AUTO] generic-tag share ≤ 10% of runtime; [REVIEW] |
| V9 | Interview/news clips as breaks from the narrator, grounded in sources. | Owner, v1 | [AUTO] ≥ 1 non-narrator voice per ~8 min |
| V10 | No faces of random vloggers, no creator overlays or end cards, no pillar/letterboxed phone video, no copyrighted film inside CC clips. Every source piece gets frame-reviewed safe windows. | Claude QA, v2 | [AUTO] shot must lie inside a reviewed SAFE window |
| V11 | Modern footage standing in for history is graded to period, and archival is never rapidly intercut with 4K. | Claude QA, v2 | [REVIEW] |
| V13 | When the narration describes something visual (e.g. the "face" in the mountain), the picture must clearly show it: the best real view, held long enough, with a subtle on-screen guide (outline/label) if needed. | Owner, v2 | [REVIEW] visual-claim list per script |
| V14 | The intro/teaser shows the most specific, best-matching imagery for each highlight it names (the actual people, places and events), never random scenery. Open on the best story with the best-matched images. Each chapter opens on its strongest matching image. | Owner, v2 | [AUTO] no generic-tag shot in cold open/teaser or as a chapter's first shot; [REVIEW] |
| S1 | Chapter order is grounded in audience-demand research: the strongest story is chapter 1, the second-strongest is saved for the last chapter (before the epilogue), and the rest run from stronger to weaker in between. Transitions are rewritten to fit. | Owner, v2 | [REVIEW] demand ranking with sources kept in the episode notes |
| V12 | No stereotyped "Native" imagery (Plains headdress stock, sham-battle films), no AI images of real people/events. | Research rubric | [REVIEW] banned-source list |

## Sound

| ID | Rule | Origin | Check |
|---|---|---|---|
| A1 | Sound effects and light background music, coherent with picture; nothing clashes. | Owner, v2 | [REVIEW] |
| A2 | −14 LUFS integrated, true peak ≤ −1 dB; music ≥ 18 dB under narration; ambience ≥ 18 dB under. | Research rubric | [AUTO] |
| A3 | Interview bites matched to narrator loudness (±2 LU). | Claude QA, v2 | [AUTO] |
| A4 | Picture/sound sync: inserts and cards start exactly with their audio. | Claude QA, v2 | [AUTO] offset = 0 |
| A5 | Names pronounced consistently and correctly. Transcribe the narration and check proper nouns; use inline IPA where needed. | Claude QA, v2 | [AUTO] transcript name check |

## Delivery

| ID | Rule | Origin | Check |
|---|---|---|---|
| D1 | Subtitles as selectable tracks (not burned in): English plus at least Spanish, timed to the voice. | Owner, v2 | [AUTO] en + es SRT present; cue timing anchored to speech pauses |
| D2 | Before calling an episode final, critique it through the audience personas and score it, grounded in research. | Owner, v2 | [REVIEW] scorecard |
| D3 | Credits for every CC/PD asset (title, author, link, license): pinned comment < 10,000 chars, overflow in the description (< 5,000); AI narration disclosed. | Research rubric | [AUTO] every used source has a credit |

## V47 — No double post (owner 2026-11-08, hard rule)
A story/caption may exist ONCE per platform. social_post.py refuses to publish when another queue item on the same platform with the same normalized caption is already logged as posted, or the same caption is already live on the platform (Graph API read; if the read fails the item is blocked, never posted blind). Rebuilt/re-released items count as the same story. The post log is merged onto the newest origin queue (scripts/merge_queue_log.py) so a rebase conflict can never lose a "done" entry (that loss caused the 2026-11-08 double post of ch2 y10). Never delete a reel by an id from the queue without opening it first and verifying caption/permalink.

## Hook playbook for new Shorts/Reels (from the 2026-11-08 reach sweep; applies to future items only)
Data (IG/YT, 26 reels): winners were animal / famous landmark-or-person / myth-bust + a hard number (3,000 elk 1,806 views; Roosevelt arch 1,799; "never afraid of geysers" 1,203; bison law 950). Dry chronology/obscure-name hooks (nine tourists, Nez Perce timeline) sat at 130-250.
- First 3 s: animal, landmark or famous name + one number; no obscure proper nouns first.
- Put a new visual or surprising fact at ~12-15 s (IG average watch time is ~15 s of 45 s).
- Zion order already leads with numbers (z1 7 canyoneers, z6 17 deaths, z9 4,000 to 5 million); keep that for Parts 2/3.
- Shorts drive ~2,750 views but only ~17 related-video views to the longs: every Short keeps the end card + link comment to the full film; long-form views stay small until that conversion improves.
- Facebook reels average 0-4 plays: keep auto-posting, spend no extra effort.

## Related video link (Short -> full film)
No public API. Done in the cloud by .github/workflows/yt-link.yml (scripts/yt_studio_link.py, saved Studio session), once a day at 19:37 UTC for every public Short, film parsed from the Short's own "Full documentary (...)" description line. Never accept a Short as the related video (#Shorts titles are excluded). Studio's UI language in the cloud session is Portuguese; selectors are language-tolerant.
