# Health log

## 2026-11-10T22:58Z ALERT
- Stories lead is only to Nov 13 19:00Z (about 3 days, under 5): IG/FB Stories have 6 future items each and no Zion stories. IG/FB Reels (last Nov 21) and TikTok (Nov 21) are fine. Zion Part 3 (~Nov 15) and the Zion film (Nov 19) still do not exist; recommended three days running, so escalated.
- yt-link cron (19:37Z) skipped again (second day in a row); I dispatched it once (run 42918744862). Proposed a second schedule (I23).
- No failed runs in 24 h, no missed posts, no duplicates. 21 pending comments, none overdue; Zion P2 premiere comment is queued for Nov 12 20:05Z.
- YouTube 13 subs (12 yesterday, 8 on Nov 3), 4,057 views (3,990), long-form watch about 8.2 h of 8,000 h (5.6 yesterday). RELATED_VIDEO is 38 views and 377 min, so the Short-to-film link works. Median public Short 19 views; "Shot twice, he crawled 12 miles" at 615 is the standout (person + number).
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
