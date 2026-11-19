# Spotify film sync log

## 2026-11-18
- Checked: Zion film (YouTube release due 2026-11-19, not yet due). Release folder zion-release/film/ on the footage branch does not exist; content/zion has only p1/p2 files (no film assets).
- Posted: nothing (no new full film public on YouTube; no assets). Spotify duplicate check and uploads skipped.
- Run ids: none. Blockers: Zion film assets missing (see COMPASS I05/I29). Not overdue yet; overdue threshold is 2026-11-22.

## 2026-11-19
- Checked: Zion film (YouTube release due 2026-11-19). The footage branch (commit 45158d4, 2026-11-19 01:23Z) has no zion-release/ folder and no zion-release/film/ (no *_final.mp4.partNN, .sha256, desc_long.txt, meta_0_long.json, thumb.jpg or film_es.m4a). Zion Part 1 and Part 2 sit under yellowstone-release/zion1 and zion2. The latest metrics snapshot (content/metrics/latest.json, 2026-11-18 21:27Z) lists no Zion full film on YouTube, and Zion Part 3 is not on the channel even as private. content/zion has P3 script/segments/TTS but no film script or film assets.
- Spotify duplicate check (spotify-stats run 44591199884, success): EN show 5K5ZytGhBYz2xJ8Iwvf8ss has Yellowstone film (Published 2026-11-17) plus Yellowstone/Chiricahua video drafts; ES show 0Ylyy2y3qBkG0AUpAgGT7Q has Yellowstone film (Published 2026-11-17) and Chiricahua (audio, Published 2026-10-27). Nothing new to post.
- Posted: nothing. No full film is public on YouTube that is missing from Spotify, and its release folder and assets are missing, so spotify-upload was not dispatched for EN or ES.
- Run ids: spotify-stats 44591199884 (success).
- Blockers: Zion film not produced/released (no release folder, no film_es.m4a). Not overdue yet; the overdue threshold is 2026-11-22. Next check: next daily run; if the Zion film is public by then, run EN then ES as in the routine.
- Tooling note: the bridge tools cannot read the footage branch, so the check used the GitHub API on the footage tree.
