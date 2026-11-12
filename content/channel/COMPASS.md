# AlphaDog Studio — COMPASS (master reference + improvement tracker)

Read this FIRST when anything is unclear. Owner: Rodo (San Diego, Pacific time). Every scheduled task reads it at the start and updates the tracker at the end.
Last reviewed: 2026-11-12. Related: EDITING_RULES.md (rules V1–V48), content/logs/*.md (run logs), content/metrics/ (data + reports).

## 1. Mission and money math
- Goal: YouTube subscribers + public LONG-FORM watch hours (this is what monetizes). Shorts/Reels/TikTok exist to feed viewers to the full documentaries.
- YPP: until 2027-02-01 1,000 subs + 4,000 public long-form hours (or 10M Shorts views/90 d); from 2027-02-01 1,000 subs + 8,000 hours (or 20M Shorts views/90 d). Shorts watch hours do NOT count. Fan-funding tier: 500 subs + 3,000 h (or 3M Shorts views).
- Baseline 2026-11-09: 12 subs, 3,990 views, long-form watch 5.8 h. 2026-11-10: 13 subs, 4,057 views, long-form ~8.2 h. 2026-11-11: 13 subs, 4,434 views, long-form ~8-9 h. 2026-11-12: 14 subs, 4,871 views, long-form ~10.5 h. Weekly review tracks the trend; growth is expected to be non-linear.

## 2. Content
- Films: Chiricahua; Yellowstone parts 1–3 + film; Zion parts 1–3 + film (Zion P1 public Nov 8, P2 premiered Nov 12 20:00Z id 1KUANk1uGtU, P3 ~Nov 15, Zion film Nov 19).
- Per film: ~9 Shorts/Reels (+ Stories) with the hook playbook; each ends with the end card/CTA to the full film and a pinned link comment.
- Schedule (owner-approved 2026-11-02): longs Thu 12:00 PT + Sun 08:00 PT; IG/FB Reels 12:00 + 17:00 PT; Stories 11:00 + 18:00 PT; TikTok 16:00 + 19:00 PT (via Buffer); YT Shorts 10:00 + 17:00 PT.

## 3. System map
- Repo Rodantmat/Alphadog-Social (main). Footage lives on branch `footage`. Queue: content/social_queue.json (IG/FB), content/tiktok_backlog.json, content/pending/ (YouTube comments).
- Posting: social-post.yml (cron 3,33 each hour + manual only=<id>); guards V47 (no double post) and V48 (adjacent_gate.py). yt-followup.yml posts pending comments. yt-link.yml (daily 19:37Z) sets "Related video" on every public Short via the saved Studio session (reads video ids from content/metrics/latest.json; fails with KeyError 'videos' if metrics YouTube section is an error). comment-sweep.yml answers viewer comments on YT/IG/FB 3x/day. metrics-daily.yml writes content/metrics/.
- Scheduled tasks (all write a log): Social posting slots → logs/posting-slots.md; posting watchdog → logs/watchdog.md; daily health+growth → logs/health.md + metrics/health_<date>.md; weekly review → logs/weekly.md + metrics/weekly_<date>.md; yt-link → logs/yt-link.md.
- Never: print secrets, edit/delete/repost already-published items (unless fixing a real error), make the owner run anything manually, add costs beyond Cloudflare $5 + GitHub $4 plans.

## 4. Standing owner rules (short index; full text in EDITING_RULES.md and memory)
Every post on every platform and matching across platforms; missed post = post it manually now and verify; no look-alike reels/neighbours (V45/V48); Stories need audio; never repeat music; phone-safe full-screen covers; CTA/end card to the full film; archival/outside imagery share; picture repetition limits; every owner correction → QA analyzer; no double posts (V47).

## 5. Improvement tracker (single source of truth)
Status: DONE · IN-PROGRESS · OPEN · WAIT-DATA · MONITOR. "Backed" = evidence supports acting now. Update the Last-check date and note every time a task touches an item. Never delete a row; mark DONE and keep the evidence.

| ID | Improvement | Evidence / why | Status | Next action | Last check |
|---|---|---|---|---|---|
| I01 | No double posts (V47 guard + log-merge) | Duplicate Story 2026-11-08 | DONE | none; watch logs for "DUPLICATE BLOCKED" | 11-12 |
| I02 | Hook playbook: animal/landmark/person + hard number in first 3 s and in the title; new beat at 12–15 s | YT hook posts ~12x views at 24 h (weekly 11-09); IG outliers all had number/contrast. 11-10: "Shot twice, he crawled 12 miles" 615 views (32x median 19), 621 on 11-11. 11-12: "Three thousand elk in one winter" 1,328 views, 68 % avg view, 5 subs gained (about 30x median 39, best Short so far; animal + hard number) | IN-PROGRESS | apply to every new script (Zion P2/P3, next films); elk/bison/animal+number is the proven pattern | 11-12 |
| I03 | Retitle weak Zion Shorts with numbers (private ones only) | same as I02 | DONE | 3 retitled 11-09 (zscU0YPpl_Y, TPB5_pBj50U, 0c8WvCxQWHY); all 20 private Zion Shorts have number titles 11-10; tb-0953M_T8 public 11-11 with title intact; 11-12 three more Zion Shorts public with titles intact (0c8WvCxQWHY 351 views); verify remaining public titles after Nov 13–20 | 11-12 |
| I04 | Auto "Related video" Short→film link | RELATED_VIDEO traffic ≈ 9.3 min/view vs 0.3 for Shorts (11-12: 47 views, 439 min) | DONE | yt-link daily; backup schedule (I23); see I25 | 11-12 |
| I05 | Queue lead ≥ 5 days on every platform; Zion P2/P3/film Shorts+Reels | Queue ended 11-16; flagged 11-08 and 11-09 | IN-PROGRESS | DONE 11-09: Zion P2 Shorts w1–w10 built, uploaded to YouTube (private, scheduled 11-16 01:00Z → 11-20 18:00Z, link comments queued), IG/FB queued 11-17 01:00Z → 11-21 20:00Z, TikTok 11-17 → 11-21. STILL OPEN (5th report 11-12 => ALERT): Zion Part 3 (~Nov 15) and the Zion film (Nov 19) DO NOT EXIST YET (content/zion has only p1/p2 files; no p3/film script or assets) so no Shorts can be built; Reels/TikTok lead to Nov 21 (9 days, OK); Part 3 production (research, script, AI scenes, film) must start now; reuse pipeline content/zion/tools (make_reels_z.py, reels_z2.json, gen_p2_pack.py) | 11-12 |
| I06 | Long-form retention (<2 % on 3 of 5 films): stronger first 30 s, end-screen links | weekly 11-09; 11-12 only Chiricahua has real watch time (93 views, 571 min); Yellowstone film 24 views/20 min, Zion P1 14/15, Yellowstone P1 11/14, Nez Perce and Cavalry ≈0; Zion P2 premiered 11-12 (1 view after 3 h) | OPEN | review first 2 min of each film with analytics retention curve; fix in next films, re-cut only if owner agrees (already published = untouched) | 11-12 |
| I07 | IG: payoff in first 3 s so avg watch ≥ 15 s | IG outliers 15–23 s vs 5–8 s for weak; 11-12 batch 6–12 s (Zion flash flood 6.8 s) | IN-PROGRESS | make it a check in new Reels scripts | 11-12 |
| I08 | Test 2 sub-36 s cuts per week (Yellowstone + Zion) | length confounded with topic | OPEN | include in next batch, compare at 7 d | 11-10 |
| I09 | Pinned comment / end card to full film on every Short | Shorts→long conversion tiny (~17 related views at 11-09, 47 on 11-12) | IN-PROGRESS | keep; measure RELATED_VIDEO share weekly | 11-12 |
| I10 | Report log for every scheduled task | owner 2026-11-08 | DONE | all five logs exist (health, watchdog, posting-slots, weekly, yt-link) | 11-12 |
| I11 | yt-link cron skipped on 11-09, 11-10, 11-11 and 11-12 (GitHub skips scheduled runs) | health 11-09..11-12 (19:37Z run missing every day) | IN-PROGRESS | skipped 4 days => implement I23 now; health task re-dispatches manually meanwhile. 11-12: both dispatches FAILED (see I25) | 11-12 |
| I12 | V48 adjacent-post gate (hook overlap, same file, repeated frames) | owner 2026-11-08 | IN-PROGRESS | pair ch3y9/ch3y10 shares 2–3 % of frames (queued); fix; add audio-fingerprint check for music | 11-10 |
| I13 | Comment sweep dry-run test for the reply path | 57 comments found, 0 replies (all our own); 11-12 comment-sweep success, still only own comments | OPEN | dry_run once real viewer comments exist; review replies | 11-12 |
| I14 | Posting slot changes | need ≥ 30 posts/slot, ≥ 30 % diff at 24 h and 72 h | WAIT-DATA | weekly review re-checks; counts now 6–8 per slot | 11-10 |
| I15 | Facebook reels reach (0–4 plays) | weekly; 11-12 FB followers flat at 152, reactions 0–1 | MONITOR | keep auto-posting, no extra effort | 11-12 |
| I16 | IG ProcessingFailedError on most Reels; "shorts" artifact expired every run | posting-slots log (11-11/12: download-artifact "shorts"/"promo" not found, footage-branch fallback succeeds; IG trial-reel fallback to normal reel non-fatal) | OPEN (low) | fix artifact handling / re-encode so IG accepts first try; non-fatal | 11-12 |
| I17 | Studio session expiry (cookies) | yt-link depends on it; 11-12 yt-link "Link" step failed twice, cause not yet confirmed (I25) | MONITOR | health task alerts; owner re-exports cookies only if it keeps failing | 11-12 |
| I18 | Repo size / cloud disk | workspace disk filled 11-08 (cleared); 11-11 .git 152 MB, tree 157 MB; GitHub fine, no upgrade needed | MONITOR | health task reports repo size (repo-size-audit.yml) | 11-11 |
| I19 | Archival + outside footage share in films | owner rule | IN-PROGRESS | keep for Zion P3/film | 11-09 |
| I20 | Track YPP progress weekly (subs, long-form hours) | section 1 | IN-PROGRESS | weekly review | 11-12 |
| I21 | V49 animation strictness gate (anim_gate.py; regenerate rejects) | EDITING_RULES V49 | DONE (gate, analyzer-linked) | gate every new clip batch (Zion P3/film) | 11-10 |
| I22 | YouTube API refresh token dead 11-12 (yt-followup failed 4x 18:58–20:36Z, metrics-daily 20:54Z had no YouTube data) -> re-authorized 22:25Z, yt-followup 22:26Z OK, comments posted ~4 h late | section 3 | DONE; MONITOR 7-day expiry (OAuth app in Testing?) | if it dies again about 11-19, move OAuth app out of Testing (owner, one time) | 11-12 |
| I24 | Stories lead < 5 days: IG/FB Stories queued only to 2026-11-13T19:00Z (2 future items per platform at 11-12; formerly numbered I22) | health 11-10, 11-11, 11-12 queue check (3rd consecutive report => ALERT) | OPEN (ALERT) | build/queue Zion Stories s11+ (Zion P1/P2 material) to extend lead to ≥ Nov 20 | 11-12 |
| I23 | Backup trigger for yt-link (2nd cron or watchdog dispatch) | I11 skipped four days | OPEN (ALERT) | add second schedule (e.g. 01:37Z) in yt-link.yml or have the watchdog dispatch it when no run in 20 h | 11-12 |
| I25 | yt-link robustness: yt_studio_link.py reads ids from latest.json and crashes (KeyError 'videos') when metrics YouTube part is an error; 11-12 re-dispatch after metrics fix still failed in step "Link" (no log detail; debug artifact link-43324513392) | health 11-12 | OPEN | read artifact/step log, make script fetch ids itself with fallback to cached list; owner cookie re-export only if login/challenge confirmed | 11-12 |
| I26 | Repeat the elk/animal+number pattern: Shorts with animal or person plus a hard number drive 10–30x median and subs (elk 1,328 views, 5 subs) | health 11-12 | OPEN | build Zion P3/film Shorts with animal/number hooks (cougars/deer 780 culled, 800 dead? only with facts from script) | 11-12 |

## 6. How tasks use this file
1. Start of every run: read this file; carry OPEN/IN-PROGRESS items into the run.
2. During the run: if an item is "Backed" and safe, DO it (do not wait for the owner), then log it. Bigger or irreversible items → report as a recommendation.
3. End of run: update the Status/Next action/Last check of every item you touched, add new items with the next free ID (I27…) and the evidence, commit via social_put_file, and mention changed rows in the report log.
4. A recommendation that appears in two consecutive reports without action must be escalated to ALERT.
