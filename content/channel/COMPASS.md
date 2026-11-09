# AlphaDog Studio — COMPASS (master reference + improvement tracker)

Read this FIRST when anything is unclear. Owner: Rodo (San Diego, Pacific time). Every scheduled task reads it at the start and updates the tracker at the end.
Last reviewed: 2026-11-09. Related: EDITING_RULES.md (rules V1–V48), content/logs/*.md (run logs), content/metrics/ (data + reports).

## 1. Mission and money math
- Goal: YouTube subscribers + public LONG-FORM watch hours (this is what monetizes). Shorts/Reels/TikTok exist to feed viewers to the full documentaries.
- YPP: until 2027-02-01 1,000 subs + 4,000 public long-form hours (or 10M Shorts views/90 d); from 2027-02-01 1,000 subs + 8,000 hours (or 20M Shorts views/90 d). Shorts watch hours do NOT count. Fan-funding tier: 500 subs + 3,000 h (or 3M Shorts views).
- Baseline 2026-11-09: 12 subs, 3,990 views, long-form watch 5.8 h. Weekly review tracks the trend; growth is expected to be non-linear.

## 2. Content
- Films: Chiricahua; Yellowstone parts 1–3 + film; Zion parts 1–3 + film (Zion P1 public Nov 8, P2 premiere Nov 12 20:00Z id 1KUANk1uGtU, P3 ~Nov 15, Zion film Nov 19).
- Per film: ~9 Shorts/Reels (+ Stories) with the hook playbook; each ends with the end card/CTA to the full film and a pinned link comment.
- Schedule (owner-approved 2026-11-02): longs Thu 12:00 PT + Sun 08:00 PT; IG/FB Reels 12:00 + 17:00 PT; Stories 11:00 + 18:00 PT; TikTok 16:00 + 19:00 PT (via Buffer); YT Shorts 10:00 + 17:00 PT.

## 3. System map
- Repo Rodantmat/Alphadog-Social (main). Footage lives on branch `footage`. Queue: content/social_queue.json (IG/FB), content/tiktok_backlog.json, content/pending/ (YouTube comments).
- Posting: social-post.yml (cron 3,33 each hour + manual only=<id>); guards V47 (no double post) and V48 (adjacent_gate.py). yt-followup.yml posts pending comments. yt-link.yml (daily 19:37Z) sets "Related video" on every public Short via the saved Studio session. comment-sweep.yml answers viewer comments on YT/IG/FB 3x/day. metrics-daily.yml writes content/metrics/.
- Scheduled tasks (all write a log): Social posting slots → logs/posting-slots.md; posting watchdog → logs/watchdog.md; daily health+growth → logs/health.md + metrics/health_<date>.md; weekly review → logs/weekly.md + metrics/weekly_<date>.md; yt-link → logs/yt-link.md.
- Never: print secrets, edit/delete/repost already-published items (unless fixing a real error), make the owner run anything manually, add costs beyond Cloudflare $5 + GitHub $4 plans.

## 4. Standing owner rules (short index; full text in EDITING_RULES.md and memory)
Every post on every platform and matching across platforms; missed post = post it manually now and verify; no look-alike reels/neighbours (V45/V48); Stories need audio; never repeat music; phone-safe full-screen covers; CTA/end card to the full film; archival/outside imagery share; picture repetition limits; every owner correction → QA analyzer; no double posts (V47).

## 5. Improvement tracker (single source of truth)
Status: DONE · IN-PROGRESS · OPEN · WAIT-DATA · MONITOR. "Backed" = evidence supports acting now. Update the Last-check date and note every time a task touches an item. Never delete a row; mark DONE and keep the evidence.

| ID | Improvement | Evidence / why | Status | Next action | Last check |
|---|---|---|---|---|---|
| I01 | No double posts (V47 guard + log-merge) | Duplicate Story 2026-11-08 | DONE | none; watch logs for "DUPLICATE BLOCKED" | 11-09 |
| I02 | Hook playbook: animal/landmark/person + hard number in first 3 s and in the title; new beat at 12–15 s | YT hook posts ~12x views at 24 h (weekly 11-09); IG outliers all had number/contrast | IN-PROGRESS | apply to every new script (Zion P2/P3, next films) | 11-09 |
| I03 | Retitle weak Zion Shorts with numbers (private ones only) | same as I02 | DONE | 3 retitled 11-09 (zscU0YPpl_Y, TPB5_pBj50U, 0c8WvCxQWHY); verify public titles after Nov 11–15 | 11-09 |
| I04 | Auto "Related video" Short→film link | RELATED_VIDEO traffic ≈ 9 min/view vs 0.3 for Shorts | DONE | yt-link daily; backup schedule if cron skips (I11) | 11-09 |
| I05 | Queue lead ≥ 5 days on every platform; Zion P2/P3/film Shorts+Reels | Queue ends 11-16 20:00Z; flagged 11-08 and 11-09 | OPEN (HIGH) | build P2/P3/film batch with hook playbook, run V48 gate, queue before Nov 11 | 11-09 |
| I06 | Long-form retention (<2 % on 3 of 5 films): stronger first 30 s, end-screen links | weekly 11-09 | OPEN | review first 2 min of each film with analytics retention curve; fix in next films, re-cut only if owner agrees (already published = untouched) | 11-09 |
| I07 | IG: payoff in first 3 s so avg watch ≥ 15 s | IG outliers 15–23 s vs 5–8 s for weak | IN-PROGRESS | make it a check in new Reels scripts | 11-09 |
| I08 | Test 2 sub-36 s cuts per week (Yellowstone + Zion) | length confounded with topic | OPEN | include in next batch, compare at 7 d | 11-09 |
| I09 | Pinned comment / end card to full film on every Short | Shorts→long conversion tiny (~17 related views) | IN-PROGRESS | keep; measure RELATED_VIDEO share weekly | 11-09 |
| I10 | Report log for every scheduled task | owner 2026-11-08 | DONE | verify each log file appears after first run (health.md/watchdog.md/posting-slots.md/weekly.md/yt-link.md exist) | 11-09 |
| I11 | yt-link cron skipped on 11-09 (GitHub skips scheduled runs) | health 11-09 | MONITOR | if it skips twice, add 2nd schedule or trigger from the watchdog task | 11-09 |
| I12 | V48 adjacent-post gate (hook overlap, same file, repeated frames) | owner 2026-11-08 | IN-PROGRESS | pair ch3y9/ch3y10 shares 2–3 % of frames (queued); fix; add audio-fingerprint check for music | 11-09 |
| I13 | Comment sweep dry-run test for the reply path | 57 comments found, 0 replies (all our own) | OPEN | dry_run once real viewer comments exist; review replies | 11-09 |
| I14 | Posting slot changes | need ≥ 30 posts/slot, ≥ 30 % diff at 24 h and 72 h | WAIT-DATA | weekly review re-checks; counts now 6–8 per slot | 11-09 |
| I15 | Facebook reels reach (0–4 plays) | weekly | MONITOR | keep auto-posting, no extra effort | 11-09 |
| I16 | IG ProcessingFailedError on most Reels; "shorts" artifact expired every run | posting-slots log | OPEN (low) | fix artifact handling / re-encode so IG accepts first try; non-fatal | 11-09 |
| I17 | Studio session expiry (cookies) | yt-link depends on it | MONITOR | health task alerts; owner re-exports cookies only if it fails | 11-09 |
| I18 | Repo size / cloud disk | workspace disk filled 11-08 (cleared); GitHub fine, no upgrade needed | MONITOR | health task reports repo size (repo-size-audit.yml) | 11-09 |
| I19 | Archival + outside footage share in films | owner rule | IN-PROGRESS | keep for Zion P3/film | 11-09 |
| I20 | Track YPP progress weekly (subs, long-form hours) | section 1 | IN-PROGRESS | weekly review | 11-09 |

## 6. How tasks use this file
1. Start of every run: read this file; carry OPEN/IN-PROGRESS items into the run.
2. During the run: if an item is "Backed" and safe, DO it (do not wait for the owner), then log it. Bigger or irreversible items → report as a recommendation.
3. End of run: update the Status/Next action/Last check of every item you touched, add new items with the next free ID (I21…) and the evidence, commit via social_put_file, and mention changed rows in the report log.
4. A recommendation that appears in two consecutive reports without action must be escalated to ALERT.
