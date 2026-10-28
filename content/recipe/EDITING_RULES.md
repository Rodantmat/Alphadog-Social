# AlphaDog Studio — Standing Editing Rules

Every owner critique becomes a rule here. Each rule has an ID. Rules marked **[AUTO]** are enforced in code by `qa_check.py`, which fails the build before anything is shown to the owner. Rules marked **[REVIEW]** go on the pre-delivery checklist and are checked against contact sheets.

Every episode inherits all rules. Never ask the owner to repeat one.

## Footage & imagery

| ID | Rule | Origin | Check |
|---|---|---|---|
| V1 | Real moving footage first (aerial/drone, hikers, places). Stills only for genuine historical photos. No "dancing photos", no Ken Burns paths over modern photos. | Owner, v1 | [AUTO] still share ≤ 20%, historical photos only |
| V2 | The picture must match the narration at that moment, with coherent sequence. No unrelated subject (e.g. a horse during the volcano part). | Owner, v1 | [REVIEW] per-shot sheet with the narration line |
| V3 | Never show the same image repeatedly in a short span. | Owner, v1 | [AUTO] same source+window not reused within 60 s, except deliberate recaps |
| V4 | **No flash shots.** No clip may show only a few frames before a cut. That covers cuts inside the source clip, not just our own cuts. Every visible scene lasts ≥ 2.5 s. Only exception: a closing recap montage where each image matches its spoken phrase (≥ 2.0 s each). Archival films: skip their intertitle text cards. | Owner, v2 | [AUTO] scene-cut detection on sources + final render; min visible scene 2.5 s |
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
| V15 | **Smooth motion, no micro-stutter.** No moving shot may contain repeated/dropped frames. Sources below 29.5 fps average (iPhone variable frame rate, low light, 24 fps AI clips) or with duplicated frames are motion-interpolated to a true 30 fps before use. | Owner, Yellowstone Ch1 review (2026-10-28) | [AUTO] prep2.py Q-FPS fixes; analyzer F1 flags any shot with > 3% repeated frames |
| V16 | **No frozen tails.** A shot never lasts longer than its real footage (no held last frame). Durations are re-balanced inside the segment; if footage is short, pick more footage. | Owner, Yellowstone Ch1 review | [AUTO] build2.py Q-LEN hard check; analyzer F2 freeze detection on video shots |
| V17 | **No over-zoomed vertical clips.** Vertical phone video is never cropped to 16:9 (max upscale 1.35× for any crop). In long videos vertical clips appear as 2–3 full-height panels side by side; they are the first choice for Shorts. | Owner, Yellowstone Ch1 review | [AUTO] build2.py (type multi); analyzer F3 upscale/crop check |
| V18 | **Calm camera.** No whip pans or sudden fast camera moves inside a used window (pan speed ≤ ~270 px/s at 1080p); the calmest window near the wanted moment is used; internal edit points never inside a window. | Owner, Yellowstone Ch1 review | [AUTO] prep2.py Q-CALM; analyzer F4 |
| V19 | **Strong first shot.** The opening shot is the best, clearest image for the first line — never a short/low-quality clip or time-lapse fragment. | Owner, Yellowstone Ch1 review | [REVIEW] + analyzer F5 (first shot ≥ 4 s, sharp, calm) |
| V20 | **"Us" moments are short and varied:** 2–6 quick clips of the owner, Jessi and family, mixed places, each ~2.5–3.5 s; never one long single clip of one person. | Owner, Yellowstone Ch1 review | [REVIEW] |
| V21 | **End screen uses the real AlphaDog Studio logo and real imagery** (our footage behind, the next episode's real image in the next-video slot). Never an invented logo or an empty "NEXT" box. | Owner, Yellowstone Ch1 review | [AUTO] end_card.py is the only end-card source; analyzer F6 OCR/logo check |
| V22 | **Chapter cards show the chapter NAME only** — no "Chapter One/Two" numbering (numbering makes standalone parts feel incomplete). | Owner, Yellowstone Ch1 review | [AUTO] analyzer F7 OCR: no "CHAPTER <number>" text |
| V12 | No stereotyped "Native" imagery (Plains headdress stock, sham-battle films), no AI images of real people/events. | Research rubric | [REVIEW] banned-source list |

## Sound

| ID | Rule | Origin | Check |
|---|---|---|---|
| A1 | Sound effects and light background music, coherent with picture; nothing clashes. | Owner, v2 | [REVIEW] |
| A2 | −14 LUFS integrated, true peak ≤ −1 dB; music ≥ 18 dB under narration; ambience ≥ 18 dB under. | Research rubric | [AUTO] |
| A3 | Interview bites matched to narrator loudness (±2 LU). | Claude QA, v2 | [AUTO] |
| A4 | Picture/sound sync: inserts and cards start exactly with their audio. | Claude QA, v2 | [AUTO] offset = 0 |
| A5 | Names pronounced consistently and correctly. Transcribe the narration and check proper nouns; use inline IPA where needed. | Claude QA, v2 | [AUTO] transcript name check |
| A6 | **No people talking in the background.** Our own clips' natural sound is used only if no human speech is detected (VAD), and always low (≈ −10 dB vs. the ambience bed). | Owner, Yellowstone Ch1 review (2026-10-28) | [AUTO] prep2.py Q-VOICE; analyzer F8 speech detection outside narration/inserts |


## Delivery

| ID | Rule | Origin | Check |
|---|---|---|---|
| D1 | Subtitles as selectable tracks (not burned in): English plus at least Spanish, timed to the voice. | Owner, v2 | [AUTO] en + es SRT present; cue timing anchored to speech pauses |
| D2 | Before calling an episode final, critique it through the audience personas and score it, grounded in research. | Owner, v2 | [REVIEW] scorecard |
| D3 | Credits for every CC/PD asset (title, author, link, license): pinned comment < 10,000 chars, overflow in the description (< 5,000); AI narration disclosed. | Research rubric | [AUTO] every used source has a credit |
