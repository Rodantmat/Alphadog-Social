# Health log

## 2026-11-10T22:58Z ALERT
- Stories lead is only to Nov 13 19:00Z (about 3 days, under 5): IG/FB Stories have 6 future items each and no Zion stories. IG/FB Reels (last Nov 21) and TikTok (Nov 21) are fine. Zion Part 3 (~Nov 15) and the Zion film (Nov 19) still do not exist; recommended three days running, so escalated.
- yt-link cron (19:37Z) skipped again (second day in a row); I dispatched it once (run 42918744862). Proposed a second schedule (I23).
- No failed runs in 24 h, no missed posts, no duplicates. 21 pending comments, none overdue; Zion P2 premiere comment is queued for Nov 12 20:05Z.
- YouTube 13 subs (12 yesterday, 8 on Nov 3), 4,057 views (3,990), long-form watch about 8.2 h of 8,000 (5.6 yesterday). RELATED_VIDEO is 38 views and 377 min, so the Short-to-film link works. Median public Short 19 views; "Shot twice, he crawled 12 miles" at 615 is the standout (person + number).
- Details: content/metrics/health_2026-11-10.md. COMPASS rows I05, I11 changed; I22 and I23 added.

## 2026-11-11T23:00Z ALERT
- Zion Part 3 (~Nov 15) and the Zion film (Nov 19) still have no script/assets in the repo (4th report, I05). Stories lead only to Nov 13 19:00Z (4 future items per platform, I22, 2nd report). Reels/TikTok lead to Nov 21 is fine.
- yt-link cron (19:37Z) skipped a third day; dispatched once (run 43115856683). Backup schedule (I23) still not implemented.
- No real failures in 24 h, 0 missed posts, no duplicates, 19 pending comments none overdue. Zion Short tb-0953M_T8 went public on time with title intact.
- YouTube 13 subs (flat), 4,434 views (+377), RELATED_VIDEO 43 views / 407 min; long-form about 8-9 h of 8,000. Best Short still "crawled 12 miles" 621; no new outliers. IG 131 followers, FB 152 flat. Repo .git 152 MB, fine.
- Details: content/metrics/health_2026-11-11.md. COMPASS rows I05, I11, I22, I23 updated.

## 2026-11-12T23:05Z ALERT
- yt-link failed: cron 19:37Z skipped a 4th day; my two dispatches (43324065641 KeyError 'videos' because metrics had no YouTube data; 43324513392 failed in step "Link", detail not retrievable, debug artifact uploaded). Last good run 01:47Z. Not retried further; owner cookie re-export only if it keeps failing (I25, I23 still not implemented).
- YouTube OAuth token died ~18:58Z (yt-followup failed 4x, metrics 20:54Z empty); owner re-authorized 22:25Z, yt-followup now OK, comments posted ~4 h late (I22).
- Zion Part 3 (~Nov 15) and Zion film (Nov 19) still have no script/assets (5th report, I05). Stories lead only to Nov 13 19:00Z (3rd report, I24). Reels/TikTok lead to Nov 21 OK. 0 missed posts, no duplicates; Zion P2 premiere 1KUANk1uGtU public on time.
- YouTube 14 subs (13), 4,871 views (+437), long-form about 10.5 h of 8,000. New best Short: "Three thousand elk in one winter" 1,328 views, 5 subs (about 30x median 39; animal + number). IG 133 followers, FB 152.
- Details: content/metrics/health_2026-11-12.md. COMPASS rows I02, I03, I05, I11, I22, I23, I24 (renumbered Stories), I25, I26 updated.

## 2026-11-13T23:00Z ALERT
- yt-link is down: Studio session logged out ("studio status: login", exit 2) in 4 runs since 11-13 00:41Z, incl. my single dispatch today (43523077497). Cron 19:37Z skipped a 5th day (I23 unbuilt). OWNER must re-export YT_STUDIO_SESSION / YT_GOOGLE_SESSION; not retried further (I17, I25).
- No IG/FB Stories queued at all (4th report, I24). Zion Part 3 (~11-15) and Zion film (11-19) still have no script/assets (6th report, I05). Reels lead to 11-21 OK; TikTok OK.
- No other failed runs, 0 missed posts, no duplicates, 14 pending comments none overdue; Zion Shorts zscU0YPpl_Y and 6sIg9L_rgX4 public with titles intact.
- YouTube 16 subs (+2), 5,621 views (+750), long-form about 11-12 h of 8,000. Kolob ledge Short 444 views at 24 h (9x median 47); elk still best at 1,328. IG top 1,822/1,809 (12x median 155), TikTok top 1,803; hard-number/news hooks win everywhere. IG 136 followers, FB 152.
- Details: content/metrics/health_2026-11-13.md. COMPASS rows I02, I05, I11, I17, I20, I23, I24, I25, I26 updated.

## 2026-11-14T23:05Z ALERT
- Zion Part 3 (premiere ~11-15, tomorrow) and Zion film (11-19) still have no script/assets (7th report, I05). IG/FB Stories queue empty (5th report, I24b). Reels lead to 11-21 and TikTok OK.
- yt-link recovered: owner cookies renewed, run 20:45Z linked 6 Zion Shorts. 19:37Z cron skipped a 6th day; I added backup cron 03:41Z to yt-link.yml (fd122b2), verify 11-15.
- No failed runs, 0 missed posts, no duplicates, 12 pending comments none overdue.
- YouTube 17 subs (16), 6,547 views (+926; +3,504 in 7 d), long-form about 11.0 h of 8,000. New #2 Short: Zion dog-died 1,042 views (18x median 58, animal + hour). RELATED_VIDEO 48 views unchanged. Repo .git 152 MB.
- Details: content/metrics/health_2026-11-14.md. COMPASS rows I02, I05, I11, I17, I18, I20, I23b-I26b updated, I27 added.

## 2026-11-15T23:00Z ALERT
- Zion Part 3 (due ~11-15) is NOT public and content/zion has no p3/film files (8th report, I05); Zion film 11-19 also nothing. IG/FB Stories queue still empty (6th report, I24b). Reels lead to 11-21 OK.
- yt-link: no run since 11-14 20:56Z; backup cron 03:41Z did not fire and 19:37Z skipped a 7th day (I11). Dispatched once 22:53Z (run 43771798742, result unconfirmed). No cookie/login failure seen.
- 0 failed runs in 24 h, 0 missed posts, no duplicates, 10 pending comments (private Shorts) none overdue; Zion Shorts T5BjlD54g9Y, vfEdsxIDZZ0 public on time, titles intact.
- YouTube 17 subs (flat), 7,158 views (+611), long-form about 14-15 h of 8,000. RELATED_VIDEO 66 views/580 min. IG 146 followers; IG 1,364/1,463 and TikTok 1,638 outliers (8-9x median) on Angels Landing deaths/dog/5-tons-waste hooks; the same Angels deaths Short got only 13 YT views.
- Details: content/metrics/health_2026-11-15.md. COMPASS rows I02, I05, I11, I20, I23b, I24b updated.

## 2026-11-16T23:00Z ALERT
- Zion Part 3 (due ~11-15) still NOT public and content/zion has no p3/film files (9th report, I05, ESCALATED); Zion film 11-19 (3 days) has nothing. IG/FB Stories queue empty (7th report, I24b). Reels/TikTok lead only to 11-21 (4.9 days, under the 5-day bar), nothing queued after.
- yt-link: 19:37Z cron skipped an 8th evening (I11); dispatched once 22:54Z (run 43974385904, result unconfirmed). 02:49Z and 12:08Z runs were OK.
- 0 failed runs in 24 h, 0 missed posts, no duplicates, 8 pending comments none overdue; Zion Shorts lake-350-ft and mountain-fell public on time, titles intact.
- YouTube 19 subs (+7 in 7 d), 7,243 views (+3,253 in 7 d), long-form about 31 h of 8,000. RELATED_VIDEO 109 views/1,310 min. Public Shorts median 66; Zion lake 350 ft 1,134 views (17x) in <1 day, TikTok 5 tons waste 6,452 (38x median 171), IG 17 deaths 2,085 (12x). IG 160 followers, FB 152 flat.
- Details: content/metrics/health_2026-11-16.md. COMPASS rows I05, I11, I24b updated, I29 added.

## 2026-11-17T23:00Z ALERT
- Zion Part 3 (due ~11-15) still NOT public, no p3/film files (10th report, I05); Zion film 11-19 is 2 days away with nothing. IG/FB Reels last slot 11-21 20:00Z (3.9 days), TikTok 11-21 03:00Z (3.2 days), Stories queue empty (8th report): posting stops after Nov 21 without an owner decision (I29).
- yt-link: 19:37Z cron skipped a 9th evening (I11); dispatched once 22:53Z (run 44194425233, result unconfirmed). Last good run 12:34Z.
- 0 failed runs in 24 h, 0 missed posts, no duplicates, 6 pending comments none overdue; Zion Shorts Hoover Dams and 430-people public on time, titles intact.
- YouTube 20 subs (+1), 9,616 views (+2,373 in 24 h), long-form about 36.8 h of 8,000. RELATED_VIDEO 125 views/1,512 min. Hoover Dams Short 1,024 views in <1 day (14x median 72); TikTok 5 tons waste 7,663 (45x). IG 160 followers, FB 152 flat.
- Details: content/metrics/health_2026-11-17.md. COMPASS rows I02, I03, I05, I11, I20, I23, I24b, I29 updated.

## 2026-11-18T23:00Z ALERT
- Lead time: IG/FB Reels last slot 11-21 20:00Z (3.0 days), TikTok 11-21 03:00Z (2.2 days), Stories queue empty (10th report): posting stops after Nov 21 without owner decision (I05/I29). Progress: Zion P3 production started today (script, TTS, media list, AI stills committed); P3 and Zion film (11-19) not on YouTube yet.
- yt-link: 19:37Z cron skipped a 10th evening (I11); dispatched once 22:56Z (run 44416234536). Last good run 12:24Z.
- 0 failed runs in 24 h, 0 missed posts, no duplicates, 4 pending comments none overdue; lumber and Cable Mountain Shorts public on time, titles intact.
- YouTube 23 subs (+3), 9,658 views, long-form about 39.9 h of 8,000. RELATED_VIDEO 143 views/1,836 min. Zion lumber-on-a-wire Short 1,146 views in <1 day (16x median 72). TikTok metrics fetch errored (I31). Repo .git 152 MB.
- Details: content/metrics/health_2026-11-18.md. COMPASS rows I02, I03, I05, I11, I20, I23, I24b, I29 updated, I31 added.

## 2026-11-19T23:00Z ALERT
- Lead time: IG/FB Reels last slot 11-21 20:00Z (1.9 days), TikTok 11-21 03:00Z (1.2 days), Stories queue empty (11th report): posting stops after Nov 21 without new items (I05/I29, 4th report). Zion film (due today 11-19) and P3 are NOT on YouTube; P3 script/TTS files exist, no film files.
- yt-link: 19:37Z cron skipped an 11th evening (I11); dispatched once 22:54Z (run 44632836299, result unconfirmed). Last good run 12:18Z.
- 0 failed runs in last 40, 0 missed posts, no duplicates, 2 pending comments (private Shorts) none overdue; Lodge-burned and deer/cougar Shorts public on time, titles intact.
- YouTube 23 subs (flat), 11,908 views (+2,250 in 24 h), long-form about 46.6 h of 8,000 (+6.7 h). RELATED_VIDEO 164 views/2,155 min. Public Shorts median 82; lumber wire 1,148, lake 1,142, dog 1,062; deer/cougar 366 at 5 h. TikTok fetch recovered (I31 closed).
- Details: content/metrics/health_2026-11-19.md. COMPASS rows I02, I03, I05, I11, I20, I23, I24b, I29, I30, I31 updated.

## 2026-11-20T23:00Z ALERT
- Lead time: IG/FB Reels last slot 11-21 20:00Z (~21 h), TikTok last 11-21 03:00Z (~4 h), Stories queue empty (12th report): posting stops after Nov 21 (I05/I29, 5th report). PROGRESS: Zion Part 3 "The Impossible Tunnel" (30zzYRt_Mgk, 10:37) went public 18:31Z, but no Shorts/Reels/Stories exist for it and the Zion film (due 11-19) is still missing.
- yt-link: 19:37Z cron skipped a 12th evening (I11); dispatched once 22:56Z (run 44832983199, in progress). Last good run 12:21Z. yt-publish 18:26Z and zion-p3-build 18:00Z failed once, both fixed and green on re-run.
- 0 missed posts, no duplicates, comment sweeps and followups OK, no viewer comments.
- YouTube 25 subs (+2), 13,316 views (+1,408), long-form about 51.2 h of 8,000 (+4.6 h). RELATED_VIDEO 174 views/2,368 min. Public Shorts median 85; "80 deer became 600" 982 (11.5x). IG 161 followers, median 166, Cable Mountain 1,533; FB 152 flat; TikTok median 168. Repo .git 159 MB.
- Details: content/metrics/health_2026-11-20.md. COMPASS rows I02, I03, I05, I11, I20, I23, I24b, I29, I30 updated.

## 2026-11-21T23:00Z ALERT
- Lead time: IG/FB Reels last slot 11-26 20:00Z (4.9 days), TikTok 11-27 00:00Z (5.1 d), Stories last 11-25 02:00Z (3.1 d). All queued items are Zion P3 Shorts; nothing exists for the Zion film (public 11-21 00:56Z, 27 views) and nothing after 11-27 (I29, 6th report, I33 new).
- Spotify: Zion film posted on EN; ES blocked, film_es.m4a missing (I32).
- yt-link: 19:37Z cron skipped a 13th evening (I11); dispatched once 22:56Z (run 44959285290). Runs 01:07Z and 11:54Z OK.
- 0 real failures, 0 missed posts, no duplicates, 10 pending comments none overdue, no viewer comments.
- YouTube 26 subs (+1), 14,540 views (+1,224; +7,993 in 7 d), long-form about 55.0 h of 8,000 (+3.8 h). RELATED_VIDEO 182 views/2,553 min (14 min/view). Median Short 85; lake-700-years 1,030 (12x). IG 163 followers, FB 152 flat, TikTok median 171 (top 8,387).
- Details: content/metrics/health_2026-11-21.md. COMPASS rows I02, I03, I05, I11, I20, I23, I24b, I29, I30 updated; I32, I33 added.

## 2026-11-22T22:40Z ALERT
- Lead time: IG/FB Reels last slot 11-26 20:00Z (3.9 days, under 5), Stories last 11-25 02:00Z (2.1 d), TikTok 11-27 00:00Z (5.1 d). All queued items are Zion P3; nothing for the Zion FILM (63 views, P3 18) and nothing after 11-27 (I29, 7th report; I33).
- yt-link: 19:37Z cron skipped a 14th evening (I11); dispatched once ~22:35Z. Last good run 12:07Z. GRAWb3Xymmw and NNK2KmB2RIg await linking.
- 0 real failures, 0 missed posts, no duplicates, 8 pending comments none overdue, no viewer comments. Spotify ES for the film still blocked (I32).
- YouTube 28 subs (+2), 15,992 views (+1,452; +8,834 in 7 d), long-form about 58.9 h of 8,000 (+3.9 h). RELATED_VIDEO 205 views/2,835 min (13.8 min/view). Median Short 85; "146 tons of dynamite" 648 (7.6x). IG 165 followers, FB 152 flat, TikTok median 170.
- Details: content/metrics/health_2026-11-22.md. COMPASS rows I02, I05, I11, I20, I23, I24b, I29, I33 updated.

## 2026-11-23T23:00Z ALERT
- Lead time: IG/FB Reels last 11-29 20:00Z (5.9 d OK), Stories 11-27 02:00Z (3.1 d, under 5), TikTok backlog 11-29 22:00Z. Nothing exists for the Zion FILM or after Part 4 (I29/I33, 9th report).
- yt-link: 19:37Z cron skipped a 15th evening (I11); dispatched once 22:56Z (run 45284327457). Last good 13:48Z.
- 0 real failures, 0 missed posts, no duplicates, 12 pending comments none overdue, no viewer comments. Fixed adjacent_gate false positives (shared "Zion National Park history:" prefix; gate now PASS, commit fe739b9). Spotify ES for film still blocked (I32).
- YouTube 28 subs (flat), 16,858 views (+866), long-form 68.0 h of 8,000. RELATED_VIDEO 255 views/3,336 min (13.1 min/view). Median Short 91.5; dynamite 777 (8.5x), dog-on-wire 718 (7.8x). IG 164 followers, FB 152 flat, TikTok median 169.
- Details: content/metrics/health_2026-11-23.md. COMPASS rows I11, I12, I20, I24b, I29, I33 updated; I35 added.

## 2026-11-24T23:00Z ALERT
- Lead time: Stories last 11-27 02:00Z (~2.1 d, 5 IG + 5 FB pending, under 5); IG/FB Reels last 11-29 20:00Z (5.9 d OK); TikTok last due 11-29 22:00Z but 3 Part 4 items still without Buffer id. Nothing exists for the Zion FILM or after Part 4 (I29/I33, 10th report).
- yt-link: 19:37Z cron skipped a 16th evening (I11); dispatched once 22:54Z (run 45505256141, in progress at write time). Runs 04:37Z and 14:25Z OK. metrics-daily dispatched (latest.json was ~22 h old), success.
- 0 real failures in last 30 runs, 0 missed posts, no duplicates, 10 pending comments none overdue, no viewer comments. Spotify ES for the film still blocked (I32, 4th report). COMPASS file not rewritten this run (35 KB round trip too large); tracker deltas are in the health report.
- YouTube 29 subs (+1), 18,951 views (+2,093), long-form 72.0 h of 8,000 (+4.0 h). RELATED_VIDEO 269 views/3,497 min (13.0 min/view). Median Short 92; dog-on-wire 823, 1.1 miles/6 windows 724 at ~27 h (7.9x). Zion film 91 views, 23 % avg view (Yellowstone film 63 %). IG 164 followers, median 202; FB 152 flat; TikTok median 171.
- Details: content/metrics/health_2026-11-24.md.

## 2026-11-25T23:00Z ALERT
- Lead time: Stories last 11-28 02:00Z (2.1 d, under 5; 16th report). IG/FB Reels last 12-02 01:00Z (6.1 d OK), TikTok last 12-02 03:00Z (5 Part 5 items not yet in Buffer). Nothing exists for the Zion FILM (108 views) or after Part 5 (I29/I33, 11th report).
- yt-link: 19:37Z cron skipped a 17th evening (I11); dispatched once 22:53Z (run 45717019811). Runs 03:22Z and 13:38Z OK.
- 0 real failures (zion-p5-shorts one-off, re-run green), 0 missed posts, no duplicates, 13 pending comments none overdue, no viewer comments. Spotify ES for the film still blocked (I32, 5th report).
- YouTube 29 subs (+6 in 7 d), 19,358 views (+9,700 in 7 d), long-form 74.5 h of 8,000 (+34.6 h in 7 d). RELATED_VIDEO 281 views/3,633 min. Median Short 85; 1.1 miles/6 windows 930, dog-on-wire 835; Part 3 Shorts at 44-47 s got 0 views (I35). IG median 200 (top 2,106), FB 152 flat, TikTok median 173 (top 8,396). .git 164 MB.
- Details: content/metrics/health_2026-11-25.md. COMPASS rows I02, I06, I11, I20, I24b, I29, I32, I33 updated; I38 added.

## 2026-11-26T23:00Z ALERT
- Lead time: Stories last 11-28 02:00Z (1.1 d, 3 IG + 3 FB, under 5; 17th report). IG/FB Reels last 12-02 01:00Z (5.1 d OK), TikTok last 12-02 03:00Z. Nothing for the Zion FILM (108 views) or after Part 5 (I29/I33, 12th report).
- yt-link: 19:37Z cron skipped an 18th evening (I11); dispatched once (run 45907867463). Runs 02:38Z, 13:18Z OK.
- 0 real failures in last 30 runs, 0 missed posts, no duplicates, 11 pending comments none overdue, no viewer comments. Spotify ES for the film still blocked (I32, 6th report).
- YouTube 29 subs (flat), 19,648 views (+290 in 24 h, sharp slowdown, I39), long-form 75.6 h of 8,000 (+1.1 h). RELATED_VIDEO 286 views/3,716 min. Median Short 86, no new outliers. IG median 200 (top 2,106), FB 152 flat, TikTok median 168 (top 8,396). .git 164 MB.
- Details: content/metrics/health_2026-11-26.md. COMPASS rows I02, I11, I20, I24b, I29, I32, I33, I38 updated; I39 added.

## 2026-11-27T23:00Z ALERT
- Lead time: Stories last 11-28 19:00Z (0.8 d, 2 IG + 2 FB, under 5; 18th report). IG/FB Reels last 12-03 20:00Z (5.9 d OK), TikTok last 12-03 22:00Z (5 items not yet in Buffer). Nothing for the Zion FILM (108 views, 22 % avg view) or after Part 6 (I29/I33, 13th report).
- yt-link: 19:37Z cron skipped a 19th evening (I11); dispatched once (run 46079336491, in progress at write time). Runs 02:36Z, 13:16Z OK.
- 0 failed runs in last 30, 0 missed posts, no duplicates, 12 pending comments (private Shorts) none overdue, no viewer comments. Part 4 Short Y3ztJLv8Igg public on time, title intact. Spotify ES for the film still blocked (I32, 7th report).
- YouTube 29 subs (flat), 20,718 views (+1,070 in 24 h, slowdown reversed), long-form 77.4 h of 8,000 (+1.8 h; +26.2 h in 7 d). RELATED_VIDEO 296 views/3,776 min. Median Short 98; 25-30 s re-cut "Taller than 11 ft 4 in" 1,026 views at ~21 h (10.5x) vs 0-5 for 44-47 s Shorts. IG median 199 (top 2,106), FB 152 flat, TikTok median 173 (top 8,396).
- Details: content/metrics/health_2026-11-27.md. COMPASS rows I02, I11, I20, I24b, I29, I30, I32, I33, I35, I38, I39 updated; EDITING_RULES growth log appended.

