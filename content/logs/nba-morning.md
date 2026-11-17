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

## 2026-11-12 13:56 UTC ACTION
- Market term: review revert. audit_market_coverage (run 43231638155) VERDICT NOT READY, 22 dates pooled: coverage 11.9% (ref 64.3%), depth 1.59 (ref 2.11), player match 13.8% (<95%). 11-11 alone: coverage 36.1%, depth 1.99. 11-11 window rungs 2,417, avg 1.99 books.
- Pipelines: P2A 11-12 success (03:31-03:42 PT); P2A/P2B/P3 11-11 all success; P3 11-11 no soft-step failures. Scheduler tick 48s old.
- PP 11-11 (PLAY): 6 slips, 6u staked, 18.5u returned, net +12.5u, ROI +208% (P_B9_6flex +9u, P_FB_U3power +4u). Season: 95 slips, 95u, 144.5u, +49.5u, ROI +52.1%.
- UD P5 (shadow) 11-11: 4 slips, 4u, 7u returned, +3u, ROI +75%. Season P5 (graded, stake>0): 70 slips, 64.5u, 93.45u, +28.95u, ROI +44.9%.
- UD live (T+C) 11-11: 6 slips, 6u, 21.42u returned, +15.42u, ROI +257%. Season T+C (graded): 45 slips, 45u, 64.16u, +19.16u, ROI +42.6%.
- Strategies: no state/cap changes vs 11-10; CLEAN 8->9 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex; H5 "opening-weeks" hurdle cleared from all five. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). Rotation steals ewma 0.637 -> 0.676 (ok).
- Edge monitors: PP z 2.43, UD z 1.48, both RUNNING (22 slates), no ALARM.
- Boards 11-12 (4 games, routine snapshot): PrizePicks 259, Underdog 467. Sleeper/Fliff/Betr/sportsbooks 0 so far (P2B ~08:06 PT not yet run; Betr only in P3 window).

## 2026-11-14 13:57 UTC ACTION
- Market term: review revert. audit_market_coverage (run 43601986214) VERDICT NOT READY, 24 dates pooled: coverage 13.3% (ref 64.3%), depth 1.71 (ref 2.11), player match 13.6% (<95%). 11-13 alone: coverage 36.3%, depth 2.33. 11-13 window rungs 2,510, avg 2.33 books.
- Pipelines: P2A 11-14 success (03:31-03:43 PT); P2A/P2B/P3 11-13 all success (P3 claimed 13:16 PT, workflow_dispatch); P3 11-13 no soft-step failures. Scheduler tick 48s old.
- PP 11-13 (PLAY): 5 slips (all graded_void: P_B3_3power, P_B4_4flex, P_B9_6flex, P_F5_5flex, P_FB_U6flex), 5u staked, 0 returned, net -5u, ROI -100%. Season: 102 slips, 102u, 144.5u, +42.5u, ROI +41.7%.
- UD P5 (shadow) 11-13: 4 slips, 4u, 2.25u returned, -1.75u, ROI -43.8%. Season P5 (stake>0): 80 slips, 74u, 99.2u, +25.2u, ROI +34.1%.
- UD live 11-13: C 2 slips, 2u, 0 returned, -2u (T was shadow, 2 slips, +1.03u). Season T+C live: 51 slips, 51u, 71.36u, +20.36u, ROI +39.9%.
- Units: per_app flat from 11-13 (owner): PP/Sleeper $10, UD/Fliff/Betr $5.
- Strategies: no state/cap changes vs 11-12; CLEAN 10->11 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). Rotation steals ewma 0.696 -> 0.628 (ok).
- Edge monitors: PP z 2.70, UD z 1.96, both RUNNING (24 slates), no ALARM.
- Boards 11-14 (5 games): 0 rows for every app so far (latest board date in table 11-13). Prior mornings had a routine PP/UD snapshot by now - watch P2B ~08:06 PT.

## 2026-11-15 13:58 UTC ACTION
- Market term: review revert. audit_market_coverage (run 43721481469) VERDICT NOT READY, 25 dates pooled: coverage 13.6% (ref 64.3%), depth 1.74 (ref 2.11), player match 13.5% (<95%). 11-14 alone: coverage 25.0%, depth 2.37. 11-14 window rungs 1,035, avg 2.37 books.
- Pipelines: P2A 11-15 success (04:16-04:29 PT, ~45 min later than usual); P2A/P2B/P3 11-14 all success (P3 claimed 13:16 PT, workflow_dispatch); no soft-step failures in P3 11-14 or P2A 11-15. Scheduler tick 6s old. Outside the pipeline: "NBA Underdog Login (one-time token)" failed twice 11-14 (12:40, 15:08 PT); one "NBA UD Live (paper)" failure at 14:32 PT, re-run succeeded a minute later.
- PP 11-14 (PLAY): 4 slips (P_B7_3power 3/3 +5u, P_T6_flex +2u, P_B4_4flex -1u, P_B5_3power -1u), 4u staked, 9u returned, net +5u, ROI +125%. Season: 106 slips, 106u, 153.5u, +47.5u, ROI +44.8%.
- UD P5 (shadow) 11-14: 3 slips, 3u, 12.33u returned, +9.33u, ROI +311%. Season P5 (graded, stake>0): 80 slips, 74.5u, net +21.35u (profit column), ROI +28.7%; 3 older slips (11-02, 11-06, 11-07) still ungraded. Note: payout on half-stake rows is not scaled, so payout-based totals overstate returns; this season figure does not match the 11-14 entry (+25.2u).
- UD live 11-14: C 1 slip, 1u, 3.78u returned, +2.78u, ROI +278%. Season live: 51 slips, 51u, 75.14u, +24.14u, ROI +47.3%.
- Strategies: no state/cap changes vs 11-13; CLEAN 11->12 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). Rotation steals ewma 0.679, turnovers 0.690 (both ok).
- Edge monitors: PP z 2.83, UD z 2.21, both RUNNING (25 slates), no ALARM.
- Boards 11-15 (9 games): 0 rows for every app so far, same as 11-14 at this hour (11-14 later filled: window 24,282 rows, 14 books incl. PP/UD/Sleeper/Betr/Fliff). Watch P2B ~08:06 PT.

## 2026-11-16 13:58 UTC ACTION
- Market term: review revert. audit_market_coverage (run 43880398308) VERDICT NOT READY, 26 dates pooled: coverage 14.1% (ref 64.3%), depth 1.80 (ref 2.11), player match 13.0% (<95%). 11-15 alone: coverage 26.0%, depth 2.48. 11-15 window rungs 1,799, avg 2.48 books.
- Pipelines: P2A 11-16 success (03:31-03:47 PT); P2A/P2B/P3 11-15 all success (P3 claimed 12:21 PT, workflow_dispatch "P3 Afternoon Light"; Post-Tip Rebuild owner override 12:58 PT success); P3 11-15 no soft-step failures. Scheduler tick 37s old. Outside the pipeline: "NBA Underdog Login (one-time token)" failed 11-15 22:40 PT ("no pending code step - run once without otp first"); UD Token Refresh 04:02 PT success.
- PP 11-15 (PLAY): 5 slips (4 graded + 1 graded_void), 5u staked, 9u returned, net +4u, ROI +80%. Season: 111 slips, 111u, 162.5u, +51.5u, ROI +46.4%.
- UD P5 (shadow) 11-15: 4 slips, 4u, 1.4u returned, -2.6u, ROI -65%. Season P5 (graded, stake>0, profit column): 87 slips, 81u, +18.75u, ROI +23.1%; 3 older slips still ungraded.
- UD live 11-15: C 2 slips, 2u, 0.25u returned, -1.75u (T shadow only, 2 slips, +0.83u). Season live T+C: 54 slips, 54u, +22.39u, ROI +41.5%.
- Units: per_app flat - PP/UD/Sleeper/Fliff $10 (UD $10 from 11-15), Betr $5.
- Strategies: no state/cap changes vs 11-14; CLEAN 12->13 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). Rotation steals ewma 0.679 -> 0.642, turnovers 0.690 -> 0.719 (both ok).
- Edge monitors: PP z 2.95, UD z 2.30, both RUNNING (26 slates), no ALARM.
- Boards 11-16 (8 games): PrizePicks 5,883, Sleeper 3,535, Betr 2,930. Underdog, Fliff and sportsbooks 0 so far - watch P2B ~08:06 PT (Underdog had a routine snapshot by this hour on 11-10..11-12).

## 2026-11-17 13:58 UTC ACTION
- Market term: review revert. audit_market_coverage (run 44097426549) VERDICT NOT READY, 27 dates pooled: coverage 14.6% (ref 64.3%), depth 1.84, player match 12.5% (<95%). 11-16 alone: coverage 26.2%, depth 2.39. 11-16 window rungs 1,816, avg 2.39 books.
- Pipelines: P1 11-16 FAILED (pipeline_runs "failure/failure"; NBA P1 Weekly Static run 43936799906, step "Verify unacknowledged loads": nba-static-shotquality - player_shot_quality_delta / player_shot_zone_profile not written since 11-09). A later P1 Weekly Static run 11-16 18:13 PT shows success. P2A 11-17 success (03:31-03:45 PT); P2B/P3 11-16 success (P3 claimed 13:17 PT, Afternoon Light), P3 no soft-step failures. Scheduler tick 17s old. Outside the pipeline: NBA Friend Page Run failed 11-16 15:42 PT (next run 19:03 PT success).
- PP 11-16 (PLAY): 5 slips (P_B3_3power, P_B4_4flex, P_B5_3power, P_B9_6flex, P_FB_U6flex), 5u staked, 0 returned, net -5u, ROI -100%. Season: 116 slips, 116u, 158u, +42u, ROI +36.2%.
- UD P5 (shadow) 11-16: 3 slips, 3u, 0 returned, -3u, ROI -100%. Season P5 (stake>0, profit column): 90 slips, 84u, +15.75u, ROI +18.8%; all 90 graded.
- Strategies: no state/cap changes vs 11-15; CLEAN 13->14 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD). Rotation steals ewma 0.642 -> 0.548, turnovers 0.719 -> 0.611 (both still ok).
- Edge monitors: PP z 2.20, UD z 2.27, both RUNNING (27 slates), no ALARM.
- Boards 11-17 (5 games): 0 rows for every app so far (11-16 filled later: PP 32,971, UD 19,967, Sleeper 15,618, Betr 8,484, Fliff 6,800, 9 sportsbooks). Watch P2B ~08:06 PT.
