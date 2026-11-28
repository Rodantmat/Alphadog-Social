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
- Pipelines: P2A 11-10 success (03:31-03:44 PT); P2A/P2B/P1/P3 11-09 all success; P3 11-09 no soft-step failures (P2A 11-10 note: soft-failed load-content-check). Scheduler tick 46s old.
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

## 2026-11-18 14:00 UTC ACTION
- Market term: review revert. audit_market_coverage (run 44318475729) VERDICT NOT READY, 28 dates pooled: coverage 14.9% (ref 64.3%), depth 1.86, >=4 books 13.7%, player match 12.3% (<95%). 11-17 alone: coverage 26.2%, depth 2.41. 11-17 window rungs 1,151, avg 2.41 books.
- Pipelines: P2A 11-18 success (03:32-03:43 PT); P2A/P2B/P3 11-17 all success (P3 claimed 13:17 PT, Afternoon Light). P3 11-17 soft-failed step: slips-screen-warm (run stays green). Scheduler tick 3s old. Outside the pipeline: NBA Friend Page Run failed 11-17 14:50 PT (next run 18:32 PT success).
- PP 11-17 (PLAY, $10 unit): 4 slips (P_B5_3power 3/3 +5u, P_T6_flex +2u, P_B3_3power -1u, P_B4_4flex -1u), 4u staked, 9u returned, net +5u, ROI +125%. Season: 120 slips, 120u, 167u, +47u, ROI +39.2%.
- UD live 11-17: 3 slips (T 2, C 1), 3u, 5.35u returned, +2.35u, ROI +78%. Season live T+C: 59 slips, 59u, +22.74u (profit column), ROI +38.5%; 1 T slip (11-01) payout still null.
- UD P5 (shadow) 11-17: 3 slips, 3u, 3.5u returned, +0.5u, ROI +16.7%. Season P5 (paper+shadow, stake>0, profit column): 93 slips, 87u, +16.25u, ROI +18.7%; 3 older slips (11-02, 11-06, 11-07) payout null.
- Strategies: no state/cap changes vs 11-16 on the 12 strategies; CLEAN 14->15 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). CHANGE: _ROTATION state normal -> rotation, live_cap 0 -> 1; steals ok -> cool (ewma 0.548 -> 0.466, trail10 0.475); turnovers ok (0.620).
- Edge monitors: PP z 2.37, UD z 2.25, both RUNNING (28 slates), no ALARM.
- Boards 11-18 (12 games, routine snapshot): PrizePicks 675, Underdog 411, Sleeper 221, Fliff 84. Betr and sportsbooks 0 so far (Betr only in P3 window; books after P2B ~08:06 PT).

## 2026-11-19 13:55 UTC ACTION
- Market term: review revert (carried). Could not run audit_market_coverage today: github_trigger_workflow returned 403 (token lacks actions:write). Last verdict 11-18 (run 44318475729) NOT READY, 28 dates. 11-18 window rungs 2,511, avg 2.40 books.
- Pipelines: P2A 11-19 success (03:31-03:47 PT); P2A/P2B/P3 11-18 all success (P3 claimed 13:17 PT, finished 13:35 PT). Scheduler tick 58s old. P3 11-18 soft-failed grep NOT done: run is outside the last-100-runs window of github_list_workflow_runs. Outside the pipeline: NBA Friend Page Run failed 11-18 17:56 PT.
- PP 11-18 (PLAY, $10 unit): 7 slips (P_B3_3power, P_B5_3power, P_B7_3power 0; P_F5_5flex 0.4u; void P_B4_4flex 0, P_B9_6flex 0.4u, P_FB_U6flex 0), 7u staked, 0.8u returned, net -6.2u (-$62), ROI -88.6%. Season: 127 slips, 127u, 167.8u, +40.8u, ROI +32.1%.
- UD P5 (paper+shadow) 11-18: 4 slips, 4u, +3u (profit col), ROI +75%. Season P5: 97 slips, 91u, +19.25u, ROI +21.2%.
- Strategies: no state/cap changes on the 12 strategies vs 11-17; CLEAN 15->16 on A_core_3power, A_regular_5power, A_wrebounds_4flex, A_wsteals_5flex, C_wstocks_4flex. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). CHANGE: _ROTATION state rotation -> normal, live_cap 1 -> 0; steals cool -> ok (ewma 0.466 -> 0.507, trail10 0.465); turnovers ok (0.607).
- Edge monitors: PP z 2.71, UD z 2.23, both RUNNING (29 slates), no ALARM.
- Boards 11-19 (4 games): 0 rows for every app so far (11-18 filled later: PrizePicks 38,011, Underdog 26,131, Sleeper 17,777, Betr 8,001, Fliff 10,102, 9 sportsbooks). Watch P2B ~08:06 PT.

## 2026-11-20 13:58 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 again (token lacks actions:write). Last verdict 11-18 (run 44318475729) NOT READY, 28 dates. 11-19 window rungs 985, avg 2.40 books.
- Pipelines: P2A 11-20 success (03:31-03:42 PT); P2A/P2B/P3 11-19 all success (P3 claimed 13:17 PT, finished 13:28 PT). Scheduler tick 51s old. P3 11-19 soft-failed grep NOT done (run outside last-100-runs window).
- PP 11-19 (PLAY, 4 games... 3 slips): P_FB_U3power x2 (0 hits-short), P_FB_U4flex x1; 3u staked, 0 returned, net -3u, ROI -100%. Season: 130 slips, 130u, 167.8u, +37.8u, ROI +29.1%.
- UD live 11-19: T 1 slip +2.13u, C 1 slip -1u (net +1.13u). UD P5 shadow 11-19: 3 slips, -3u. Season live T+C: 61 slips, 61u, +22.87u, ROI +37.5%. Season P5 (paper+shadow, graded): 97 slips, 91.5u, +16.25u, ROI +17.8%.
- Strategies: no state/cap changes on the 12 strategies vs 11-18; CLEAN 16->17 on the five A/C strategies. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09). CHANGE: _ROTATION state normal -> rotation, live_cap 0 -> 1; steals ok -> cool (ewma 0.459, trail10 0.483); turnovers ok (0.634).
- Edge monitors: PP z 2.83 (UNDECIDED, 30 slates), UD z 1.95 (UNDECIDED, 30 slates), no ALARM.
- Boards 11-20 (slate day, 4+ games): PrizePicks 2,258, Underdog 901, Sleeper 346, Fliff 150. Betr and sportsbooks 0 so far (Betr only in P3 window; books after P2B ~08:06 PT) - same pattern as prior mornings.

## 2026-11-21 13:58 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), third day running. Last verdict 11-18 (run 44318475729) NOT READY, 28 dates. 11-20 window rungs 2,069, avg 2.44 books. Today is slate date 32 of the season.
- Pipelines: P2A 11-21 success (03:31-03:44 PT); P2A/P2B/P3 11-20 all success (P3 claimed 13:17 PT, finished 13:32 PT). Scheduler tick 31s old. P3 11-20 soft-failed grep NOT done (run outside last-100-runs window). Outside the pipeline: NBA Replay Downstream (parallel store) run 44910191119 failed 11-21 05:42 PT; later runs in progress/success.
- PP 11-20 (PLAY, $10 unit): 9 slips (6 graded_void, 3 graded; only H_P4/H_P5 etc. partial hits), 9u staked, 0 returned, net -9u (-$90), ROI -100%. Season: 139 slips, 139u, 167.8u, +28.8u, ROI +20.7%.
- UD P5 (shadow) 11-20: 3 slips, 3u, 3.5u returned, +0.5u, ROI +16.7%. Season P5 (stake>0, profit col): 103 slips, 97u, +16.75u, ROI +17.3%. UD live 11-20: H 9 slips (live) 9u, 3.5u returned, -5.5u; T 2 slips -1u and C 2 slips -1.75u (both shadow). Season live (T+C+H, status live/graded): 71 slips, 71u, +17.37u, ROI +24.5%.
- Strategies: no state/cap changes vs previous history; CLEAN 18 on the five A/C strategies. B_demon_3flex / B_demon_5flex still red (REQUAL HOLD 11-09, 0 slips). _ROTATION rotation (cap 1) unchanged: steals cool (ewma 0.399, trail10 0.434), turnovers ok (0.663). Ten H_P* strategies active, cap 1.
- Edge monitors: PP z 3.23, UD z 2.23, both RUNNING (31 slates), no ALARM.
- Boards 11-21 (6 games): 0 rows for every app so far (same pattern as prior mornings; 11-20 filled later: PrizePicks 32,929, Underdog 20,175, Sleeper 13,982, Betr 6,314, Fliff 8,004, 9 sportsbooks). Watch P2B ~08:06 PT.

## 2026-11-22 13:55 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 4th day running. Last verdict 11-18 NOT READY, 28 dates. 11-21 window rungs 1,249, avg 3.10 books. Slate date 33.
- Pipelines: P2A 11-22 success (03:31-03:43 PT); P2A/P2B/P3 11-21 all success (P3 claimed 09:32 PT, finished 09:57 PT). P3 11-21 soft-failed step: slips-screen-warm (run green; also 11-17). Scheduler tick 22s old. Outside the pipeline: one NBA Research Run failed 05:51 PT (others in progress).
- PP 11-21 (PLAY): 9 slips, 9u staked, 3.6u returned, net -5.4u, ROI -60% (H_P4 +2u, six others 0-0.4u). Season: 148 slips, 148u, 171.4u, +23.4u, ROI +15.8%.
- UD P5 (shadow) 11-21: 3 slips, 2.5u staked, +1.0u (profit col). Season P5 (stake>0, profit col): 106 slips, 99.5u, +17.75u, ROI +17.8%. UD live 11-21: H 9 slips (live) 9u, +30.1u; T 1 and C 1 shadow (-1u, +0.4u); P4 shadow 3 slips +1.67u.
- Strategies: no state/cap changes vs 11-21 history; A_wsteals_5flex yellow cap 4 (9 slips, +2.2u), A_regular_5power yellow cap 1 (-2u), A_wrebounds_4flex yellow cap 1, A_core_3power yellow cap 1 (+3u); C_wstocks_4flex paper (-3u). B_demon_3flex / B_demon_5flex red (REQUAL HOLD 11-09). Rotation: steals cool (ewma 0.399), turnovers ok (0.656).
- Edge monitors: PP z 3.12 (32 slates), UD z 2.53 (32 slates), both RUNNING, no ALARM.
- Boards 11-22 (7 games): 0 rows for PrizePicks, Underdog, Sleeper, Betr, Fliff so far; 9 sportsbooks present (e.g. draftkings 73,611). Same early-morning pattern as prior days (apps fill later, P2B ~08:06 PT).

## 2026-11-23 13:58 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 5th day running. Last verdict 11-18 NOT READY, 28 dates. 11-22 window rungs 1,403, avg 2.50 books. Slate date 34 (33 slate dates completed).
- Pipelines: P2A 11-23 success (03:31-03:46 PT); P2A/P2B/P3 11-22 all success (P3 claimed 12:02 PT, finished 12:20 PT). Scheduler tick 46s old. P3 11-22 soft-failed grep NOT done (P3 run not in the visible GitHub run window). Outside the pipeline: ~8 NBA Research Run failures 07:48-07:49 UTC window (00:48 PT), later runs success.
- PP 11-22 (PLAY): 9 slips, 9u staked, 1.2u returned, net -7.8u, ROI -86.7%. Season: 157 slips, 157u, 172.6u, +15.6u, ROI +9.9%.
- UD P5 (shadow) 11-22: 3 slips, 3u, 3.5u returned, +0.5u, ROI +16.7%. Season P5 (paper+shadow, stake>0, profit col): 109 slips, 102.5u, +18.25u, ROI +17.8%. (UD live T/C/H 11-22 not queried.)
- Strategies: no state/cap changes vs 11-22 history. A_wsteals_5flex yellow cap 4 (9 slips, +2.2u), A_core_3power / A_regular_5power / A_wrebounds_4flex yellow cap 1, C_wstocks_4flex paper (-3u). B_demon_3flex / B_demon_5flex red (0 slips). Ten H_P* + H_FB1 active cap 1.
- Edge monitors: PP z 3.09 (33 slates), UD z 2.66 (33 slates), both RUNNING, no ALARM.
- Boards 11-23 (10 games): 0 rows for every app and sportsbook so far (11-22 filled later: PrizePicks 21,857, Underdog 14,392, Sleeper 10,129, Betr 4,431, Fliff 5,790, 10 sportsbooks). Unlike 11-22, sportsbooks are also empty at 05:53 PT. Watch P2B ~08:06 PT.

## 2026-11-24 13:55 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 6th day running. Last verdict 11-18 NOT READY, 28 dates. 11-23 window rungs 1,984, avg 2.46 books. Slate date 35.
- Pipelines: P2A 11-24 success (03:31-03:47 PT); P2A/P2B/P3 11-23 all success (P3 claimed 13:17 PT, finished 13:31 PT; P1 11-23 "success/cancelled"). Scheduler tick 6s old. P3 11-23 soft-failed grep NOT done (run outside the last-100-runs window). Outside the pipeline: NBA Honest Referee failed 11-23 16:18 PT; NBA Friend Page Run failed 11-23 18:06 PT and 11-23 20:54 PT.
- PP 11-23 (PLAY): 4 slips (H_P1 +5u, H_P10 +2u, H_P3 +0.5u, H_P11 -1u), 4u staked, 10.5u returned, net +6.5u, ROI +162%. Season: 161 slips, 161u, 183.1u, +22.1u, ROI +13.7%.
- UD 11-23: H live 2 slips, 2u, +1.5u. P5 (shadow) 4 slips, 4u, -3u (profit col). Season P5 (paper+shadow): 113 slips, 106.5u, +15.25u, ROI +14.3%. Season live (T+C+H): 89 slips, 89u, +39.5u, ROI +44.3%.
- Strategies: no cap changes. A_wsteals_5flex yellow cap 4, A_core_3power / A_regular_5power / A_wrebounds_4flex yellow cap 1, C_wstocks_4flex paper (CLEAN 21), B_demon_3flex / B_demon_5flex red (REQUAL HOLD 11-09). _ROTATION normal (cap 0): steals ok (ewma 0.506), turnovers ok (0.631).
- Edge monitors: PP z 2.97 (34 slates), UD z 2.39 (34 slates), both RUNNING, no ALARM.
- Boards 11-24 (3 games): 0 rows for every app and sportsbook so far (same early-morning pattern as prior days). Watch P2B ~08:06 PT.

## 2026-11-25 13:55 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 7th day running. Last verdict 11-18 NOT READY, 28 dates. 11-24 window rungs 609, avg 2.53 books (3-game slate).
- Pipelines: P2A 11-25 success (03:31-03:42 PT); P2A/P2B/P3 11-24 all success (P3 claimed 13:17 PT, finished 13:26 PT). Scheduler tick ~1 min old. P3 11-24 soft-failed grep NOT done (P3 run outside the visible GitHub run window). Outside the pipeline: NBA Friend Page Run failed 11-24 15:50 PT (later runs success); NBA Honest Referee failed 11-24 14:44 PT.
- PP 11-24 (PLAY): 1 slip (H_P10_3power_top3, 3/3), 1u staked, 6u returned, net +5u, ROI +500%. Season: 162 slips, 162u, 189.1u, +27.1u, ROI +16.7%.
- UD P5 (shadow) 11-24: 2 slips, 2u, 0 returned, -2u, ROI -100%. Season P5 payout-based (stake>0, graded): 115 slips, 108.5u, 133.93u (payout overstates half-stake rows; profit column not re-queried).
- Strategies: no state/cap changes on the 12 strategies vs 11-23 history. A_wsteals_5flex yellow cap 4 (9 slips, +2.2u), A_core_3power / A_regular_5power / A_wrebounds_4flex yellow cap 1, C_wstocks_4flex paper (cap 2, -3u), B_demon_3flex / B_demon_5flex red (REQUAL HOLD 11-09). CHANGE: _ROTATION state normal -> rotation, live_cap 0 -> 1 (steals ok -> cool, ewma 0.430, trail10 0.338; turnovers ok 0.686).
- Edge monitors: PP z 3.08 (35 slates, look 0), UD z 1.49 (35 slates), both RUNNING (information only), no ALARM.
- Boards 11-25 (9 games): PrizePicks 2,744, Underdog 2,223, Sleeper 1,333, Fliff 602. Betr 0 and all sportsbooks 0 so far (Betr is P3-window only; sportsbooks empty at this hour as on 11-23/11-24). Watch P2B ~08:06 PT.

## 2026-11-26 13:55 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 8th day running. Last verdict 11-18 NOT READY, 28 dates. 11-25 window rungs 1,371, avg 2.74 books.
- Pipelines: P2A 11-26 success (03:31-03:46 PT); P2A/P2B/P3 11-25 all success (P3 claimed 13:17 PT, finished 13:29 PT). Scheduler tick 6s old. P3 11-25 soft-failed grep NOT done (run outside visible run window). Outside the pipeline: several NBA Research Run failures 11-26 ~00:25-00:51 PT, later runs success.
- PP 11-25 (PLAY): 2 slips (H_P1 +0.4u, H_P3 +0.4u), 2u staked, 0.8u returned, net -1.2u, ROI -60%. Season: 164 slips, 164u, 189.9u, +25.9u, ROI +15.8%.
- UD 11-25: live 2 slips, 2u, 0 returned, -2u; shadow 10 slips, 10u, +38.99u (profit col). Season P5 (stake>0, profit col): 118 slips, 111.5u, +25.97u, ROI +23.3%.
- Strategies: no state/cap changes vs 11-25 (A_wsteals_5flex yellow cap 4; A_core_3power/A_regular_5power/A_wrebounds_4flex yellow cap 1; C_wstocks_4flex/D_points/A_core_5flex paper; B_demon_3flex/5flex red; _ROTATION rotation cap 1; H_* active cap 1).
- Edge monitors: PP z 2.83 (look 30, UNDECIDED), UD z 1.95 (look 30, UNDECIDED), no ALARM. Note: latest look row is 30 (decided 11-20), lower than the 35 slates logged 11-25.
- Boards 11-26: no games on the slate (Thanksgiving; next slate 11-27) - 0 rows expected.

## 2026-11-27 13:58 UTC ACTION
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 9th day running. Last verdict 11-18 NOT READY, 28 dates. 11-26 window rungs 0 (no slate, Thanksgiving - not a flag by itself).
- Pipelines: P2A 11-27 success (03:31-03:41 PT); P2A/P2B/P3 11-26 all success (P3 claimed 13:17 PT, finished 13:21 PT, despite no slate 11-26). No failures, no missing P2A. Scheduler tick 12s old. P3 11-26 soft-failed grep NOT done (run outside visible window).
- Yesterday (11-26): no slate (slate_games has 0 games 11-26; 9 on 11-25, 11 today, 5 on 11-28) - no new PP/UD slips to grade. Season totals carried from 11-26 entry: PP 164 slips, +25.9u, ROI +15.8%; UD P5 118 slips, +25.97u, ROI +23.3%.
- Strategies: no state/cap changes vs 11-26 entry (24 strategies: A_wsteals_5flex yellow cap 4; A_core_3power/A_regular_5power/A_wrebounds_4flex yellow cap 1; C_wstocks_4flex cap 2, D_points_3power cap 2, W_core_3power cap 3 paper; B_demon_3flex/5flex red; _ROTATION rotation cap 1; ten H_P* + H_FB1 active cap 1).
- Edge monitors: PP z 3.10 (36 slates, RUNNING information only), UD z 1.95 (36 slates, RUNNING), no ALARM.
- Boards 11-27 (11 games): PrizePicks 4,246, Underdog 3,458, Sleeper 2,077, Betr 1,125, Fliff 1,040. No app empty. Sportsbooks 0 so far (same early-morning pattern; not an app).

## 2026-11-28 13:55 UTC ACTION
- Pipelines: P3 11-27 status CANCELLED (claimed 13:16 PT, finished 14:02 PT; slate day, 11 games) - the only failed/non-success run; P2A 11-27 success, P2B 11-27 success, P2A 11-28 success (03:44-03:56 PT). Scheduler tick 11s old. P3 soft-failed grep NOT done (log not pulled).
- Market term: review revert (carried). audit_market_coverage not run: github_trigger_workflow 403 (token lacks actions:write), 10th day running. Last verdict 11-18 NOT READY, 28 dates. 11-27 window rungs 2,630, avg 2.33 books (non-zero).
- PP 11-27 (PLAY): 4 slips (graded), 4u staked, 0.8u returned, net -3.2u, ROI -80%. (47 graded_shadow slips, 46u staked, 42.2u payout - not PLAY.) Season: 168 slips, 168u, 190.7u, +22.7u, ROI +13.5%.
- UD P5 (shadow) 11-27: 3 slips, 3u, 0 returned, -3u, ROI -100%. Season P5 (stake>0): 121 slips, 114.5u, payout 148.65u (payout-based; overstates half-stake rows). UD live T/C/H not queried.
- Strategies: no state/cap changes vs 11-27 history. A_wsteals_5flex yellow cap 4; A_core_3power/A_regular_5power/A_wrebounds_4flex yellow cap 1; C_wstocks_4flex paper cap 2 (-3u); B_demon_3flex/5flex red (REQUAL HOLD 11-09); _ROTATION rotation cap 1 (steals cool ewma 0.457, turnovers ok 0.637). H_NP16/NP2/NP3/NP4 rows updated 11-27 21:46 UTC (active cap 1).
- Edge monitors: PP z 3.27 (37 slates, RUNNING information only), UD z 2.14 (37 slates), no ALARM.
- Boards 11-28 (5 games): 0 rows for every app and sportsbook so far (same early-morning pattern as prior days; 11-27 filled later: PP 43,088, UD 27,772, Sleeper 19,271, Betr 9,051, Fliff 11,174, 10 sportsbooks).
