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

## 2026-11-20
- Checked: Zion film (YouTube release was due 2026-11-19, now 1 day late; overdue threshold 2026-11-22). Footage branch has no zion-release/ folder and no zion-release/film/ assets. The latest metrics snapshot (content/metrics/latest.json, 2026-11-20 07:58Z) lists no Zion full film on YouTube. Zion Part 3 was built (zion3 release, footage commit 2026-11-20 18:26Z, workflow zion-p3-build run 44790277705, success) and uploaded by yt-publish run 44793421469 (success, 18:30Z, video 30zzYRt_Mgk). That is a Part, not the full film, so it is excluded from Spotify.
- Spotify duplicate check: not run, because there was no full film to post (last check: spotify-stats run 44591199884 on 2026-11-19, success).
- Posted: nothing. spotify-upload was not dispatched for EN or ES.
- Run ids: yt-publish 44793421469 (success, Zion P3, not a film); yt-publish 44792847725 (failure at 18:27Z, FileNotFoundError on zion_ch3_final.mp4, superseded by the 18:30Z run); zion-p3-build 44790277705 (success).
- Blockers: Zion film not produced or released (no release folder, no film_es.m4a, no film_title_es.txt or film_desc_es.txt). Not yet overdue (overdue after 2026-11-22). Next check: next daily run. If the Zion film is public by then, run EN then ES as in the routine.
- Tooling note: COMPASS row I30 could not be updated in this run. The session's GitHub write path was refused for content/channel/COMPASS.md (too large to rewrite through the bridge tool). Owner or next run should set I30 Last check to 11-20 and add the note above.

## 2026-11-21
- Checked: Zion full film is public on YouTube (ugASzW14E9s, "Zion National Park: The Complete Story (Full Documentary)", published 2026-11-21 00:56Z, 33:54). The 11-20 metrics snapshot predated it, so the earlier "no film" conclusion was wrong. Release folder is yellowstone-release/zionfilm on the footage branch (there is no zion-release folder): full-film parts part00-part13, .sha256, desc_long.txt, meta_0_long.json, thumb.jpg, chapters.txt, SRTs. film_es.m4a is NOT in that folder.
- Spotify duplicate check: spotify-stats run 44937326806 (success). EN show 5K5ZytGhBYz2xJ8Iwvf8ss latest episode is the Yellowstone film (Nov 17). ES show 0Ylyy2y3qBkG0AUpAgGT7Q has the Yellowstone film and Chiricahua. No Zion film on either show.
- Posted EN: spotify-upload run 44937536102 (base=yellowstone-release, film=zionfilm, mode=publish, lang=en), success. The after-publish list shows "Zion National Park: The Complete Story (Full Documentary)" as Published 11/21/26, Video 33:54.
- Posted ES: nothing. Blocker: film_es.m4a is missing from the release folder, so no Spanish audio track and no Zion film_title_es.txt / film_desc_es.txt were written. The film went public on 11-21, one day after its 11-19 due date, so it is not yet 3 days overdue (threshold 11-22).
- Run ids: spotify-stats 44937326806 (success); spotify-upload 44937536102 (success, EN).
- Next step: when film_es.m4a is added to yellowstone-release/zionfilm, write the Spanish title and description files and dispatch spotify-upload with lang=es, es_title_file, es_desc_file, base=yellowstone-release, film=zionfilm, mode=publish. Then confirm Published on the ES show.
- Note: the 11-20 "no film" conclusion came from a stale metrics snapshot and is superseded by this entry. COMPASS I30 was updated in this run.
