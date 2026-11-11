# NBA morning monitor log

## 2026-11-09 13:59 UTC ACTION
- Market term: review revert. audit_market_coverage (run 42630063382) VERDICT NOT READY, 19 dates: coverage 8.7% (ref 64.3%), depth 1.43 (ref 2.11), player match 15.2% (<95%). 11-08 window rungs 1,335, avg 1.82 books.
- Pipelines: P2A 11-09 success (04:31-04:46 PT). P2A 11-08 FAILED (Daily delta ingestion, run 42476056225), recovered by today's catch-up (11-07 graded 04:43 PT today). P2B/P3 11-08 success, P3 no soft-step failures. Scheduler tick 52s old.
- PP 11-08: 5 slips, staked 5u, returned 0.4u, net -4.6u, ROI -92%. (11-07 late grade: 2 slips, +5.5u.) Season: 81 slips, 81u staked, 120u returned, +39u, ROI +48.1%.
- UD P5 (shadow) 11-08: 4 slips, 4u, returned 0, net -4u, ROI -100% (11-07: 3 slips, -2u). Season P5: 63 slips, 57u staked, +12.8u, ROI +22.4%.
- UD live (T+C) 11-08: 3 slips, -3u (11-07 T: 2 slips, -2u). Season T+C: 34 slips, +4.5u, ROI +13.3%.
- Strategies: no state/cap changes vs 11-07; CLEAN 5->6 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD since 11-02).
- Edge monitors: PP z 2.10, UD z 1.04, both RUNNING (19 slates), no ALARM.
- Boards 11-09 (8 games): 0 rows yet - expected, first capture is P2B ~08:06 PT.

## 2026-11-10 13:58 UTC ACTION
- Market term: review revert. audit_market_coverage (run 42828974614) VERDICT NOT READY, 20 dates pooled: coverage 9.8% (ref 64.3%), depth 1.47 (ref 2.11), player match 14.6% (<95%). 11-09 alone: coverage 30.3%, depth 1.72. 11-09 window rungs 1,903, avg 1.72 books.
- Pipelines: P2A 11-10 success (03:31-03:44 PT); P2A/P2B/P1/P3 11-09 all success; P3 11-09 no soft-step failures. Scheduler tick 46s old.
- PP 11-09: 6 slips, 6u staked, 0 returned, net -6u, ROI -100%. Season: 87 slips, 87u, 120u returned, +33u, ROI +37.9%.
- UD P5 (shadow) 11-09: 3 slips, 3u, 0 returned, -3u, ROI -100%. Season P5: 66 slips, 60u, 67.27u, +7.27u, ROI +12.1%.
- UD live (T+C) 11-09: 3 slips, 3u, 5.22u returned, +2.22u, ROI +74%. Season T+C: 37 slips, 37u, 42.74u, +5.74u, ROI +15.5%.
- Strategies: no state/cap changes vs 11-08; CLEAN 6->7 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD re-dated 11-02 -> 11-09). Rotation steals ewma 0.768 -> 0.652 (ok).
- Edge monitors: PP z 2.02, UD z 1.01, both RUNNING (20 slates), no ALARM.
- Boards 11-10 (6 games, routine snapshot): PrizePicks 965, Underdog 774, Sleeper 303, Fliff 140, novig 187, prophetx 148. Betr 0 so far (Betr is captured only in the P3 window, as on 11-09: 4,739).

## 2026-11-11 13:57 UTC ACTION
- Market term: review revert. audit_market_coverage (run 43033372214) VERDICT NOT READY, 21 dates pooled: coverage 10.7% (ref 64.3%), depth 1.52 (ref 2.11), player match 14.2% (<95%). 11-10 alone: coverage 36.3%, depth 1.90. 11-10 window rungs 1,691, avg 1.90 books.
- Pipelines: P2A 11-11 success (03:31-03:42 PT); P2A/P2B/P3 11-10 all success; P3 11-10 no soft-step failures (P2A 11-10 note: soft-failed load-content-check). Scheduler tick 46s old.
- PP 11-10 (PLAY): 2 slips (P_FB_U3power, 1 graded 3/3 + 1 graded_void), 2u staked, 6u returned, net +4u, ROI +200%. Season: 89 slips, 89u, 126u, +37u, ROI +41.6%.
- UD P5 (shadow) 11-10: 3 slips, 3u, 3.5u returned, +0.5u, ROI +16.7%. Season P5 (graded, stake>0): 69 slips, 63u, 86.45u, +23.45u, ROI +37.2%.
- UD live (T+C) 11-10: 3 slips, 3u, 0 returned, -3u, ROI -100%. Season T+C: 40 slips, 40u, 42.74u, +2.74u, ROI +6.9%.
- Strategies: no state/cap changes vs 11-09; CLEAN 7->8 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). Rotation steals ewma 0.652 -> 0.637 (ok).
- Edge monitors: PP z 2.34, UD z 1.21, both RUNNING (21 slates), no ALARM.
- Boards 11-11 (10 games, routine snapshot): PrizePicks 1,163, Underdog 447. Sleeper/Fliff/Betr/sportsbooks 0 so far (P2B ~08:06 PT not yet run; Betr only in P3 window).
