# Improvements applied (owner request 2026-11-20)

## 2026-11-20 08:07Z
- I11 / I23b (yt-link cron skipped 11 evenings): the posting watchdog task prompt now dispatches yt-link.yml once on its 18:35 PT run when no successful yt-link run exists in the last 12 h (skips if one is queued/in progress), and reports it. Tracker rows I11 and I23b: IN-PROGRESS -> DONE if the 2026-11-21 02:35Z watchdog log shows the dispatch or a success within 12 h; health/weekly tasks should verify and then update the rows.
- Scheduled-task models lowered (owner request 2026-11-18): posting slots, watchdog, Spotify film sync, Styles checker, Styles auto-scheduler, NBA text backup, NBA morning monitor, support assistant now run on Haiku 5.5; health loop, weekly review and Styles generator stay on Sonnet 5.5.

## Still open, not fixable from here without new media
- I05 / I29 / I24b: no queued posts after 2026-11-21 and 0 Stories; needs Zion P3 / film assets (build in progress, plan at content/zion/p3_plan2.txt).
- I26b / I02: build new Shorts with object/animal + hard number hooks (10-15x median) from P3 once it exists.
