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
- Correction (11-21): the 11-20 conclusion that no Zion film was public was wrong. The metrics snapshot was stale; see the 11-21 entry.

## 2026-11-21
- Checked: Zion full film is public on YouTube (ugASzW14E9s, "Zion National Park: The Complete Story (Full Documentary)", published 2026-11-21 00:56Z, 33:54). The 11-20 metrics snapshot predated it. Release folder is yellowstone-release/zionfilm on the footage branch (there is no zion-release folder): full-film parts part00-part13, .sha256, desc_long.txt, meta_0_long.json, thumb.jpg, chapters.txt, SRTs. film_es.m4a is NOT in that folder.
- Spotify duplicate check: spotify-stats run 44937326806 (success). EN show 5K5ZytGhBYz2xJ8Iwvf8ss latest episode is the Yellowstone film (Nov 17). ES show 0Ylyy2y3qBkG0AUpAgGT7Q has the Yellowstone film and Chiricahua. No Zion film on either show.
- Posted EN: spotify-upload run 44937536102 (base=yellowstone-release, film=zionfilm, mode=publish, lang=en), success. The after-publish list shows "Zion National Park: The Complete Story (Full Documentary)" as Published 11/21/26, Video 33:54.
- Posted ES: nothing. Blocker: film_es.m4a is missing from the release folder, so no Spanish audio track and no Zion film_title_es.txt / film_desc_es.txt were written. The film went public on 11-21, one day after its 11-19 due date, so it is not yet 3 days overdue (threshold 11-22).
- Run ids: spotify-stats 44937326806 (success); spotify-upload 44937536102 (success, EN).
- COMPASS I30: NOT updated. The bridge write path targets a different repo and the file is too large to rewrite safely. The owner or next run should set I30 to: Zion full film posted EN 11-21 (run 44937536102); ES blocked pending film_es.m4a.
- Next step: when film_es.m4a is added to yellowstone-release/zionfilm, write the Spanish title and description files and dispatch spotify-upload with lang=es, es_title_file, es_desc_file, base=yellowstone-release, film=zionfilm, mode=publish. Then confirm Published on the ES show.

## 2026-11-22
- Checked: no new full film to sync. Zion full film (ugASzW14E9s, public since 2026-11-21) is already on the EN show (posted 11-21). Footage branch root: no other film release folder pending. Spanish audio check: yellowstone-release/zionfilm has no film_es.m4a (the only film_es.m4a on the footage branch is yellowstone-release/film/film_es.m4a, which belongs to the Yellowstone film). Zion ES title/desc files not written.
- Spotify duplicate check: not re-run, because nothing was posted this run. Last check: spotify-stats 44937326806 (2026-11-21, success).
- Posted: nothing. spotify-upload was not dispatched for EN or ES.
- Run ids: none for posting. Read-only checks only (footage tree, release folder listing, recent Actions runs; latest runs all success).
- Blockers: ES for Zion is still blocked on film_es.m4a (I32 open). Overdue rule: the film went public 2026-11-21, so it is not more than 3 days overdue from its YouTube release yet. If film_es.m4a is not added by 2026-11-24, the ES sync is overdue and should be flagged plainly.
- COMPASS I30 and I32 not changed in this run; the 11-21 entry already records the state (EN posted, ES blocked).

## 2026-11-23
- Checked: no new full film to sync. Footage branch release folders: yellowstone-release/film (Yellowstone, already on EN and ES), yellowstone-release/zionfilm (Zion, already on EN since 11-21), no other park film folder. yellowstone-release/zionfilm still has no film_es.m4a (listing via GitHub API on the footage branch: chapters.txt, desc_long.txt, film_cuts.json, meta_0_long.json, thumb.jpg, SRTs EN/ES/PT, zion_film_final.mp4.part00-part13, .sha256). No zion_film_es title/desc files written.
- Spotify duplicate check: not re-run, because nothing new to post. Last check: spotify-stats 44937326806 (2026-11-21, success).
- Posted: nothing. spotify-upload was not dispatched for EN or ES. The Zion ES sync stays blocked (I32).
- Run ids: none for posting. Read-only checks only.
- Blockers: ES for Zion still blocked on film_es.m4a. The film went public 2026-11-21 (YouTube due 2026-11-19), so the ES sync becomes overdue more than 3 days after the YouTube release on 2026-11-24 if film_es.m4a is not added by then; this will be flagged plainly in the next report.
- COMPASS I30 not updated: the bridge write path refuses content/channel/COMPASS.md (too large to rewrite through the bridge tool), as in the 11-20 and 11-21 runs. Owner or next run should set I30 to: Zion full film posted EN 11-21 (run 44937536102); ES blocked pending film_es.m4a (last checked 11-23).

## 2026-11-24
- Checked: no new full film to sync. Footage branch: yellowstone-release/film (Yellowstone, on EN and ES) and yellowstone-release/zionfilm (Zion, on EN since 11-21); no zion-release/ or chiricahua-release/ film folder exists. yellowstone-release/zionfilm still has no film_es.m4a (GitHub API listing on the footage branch: chapters.txt, desc_long.txt, film_cuts.json, meta_0_long.json, thumb.jpg, SRTs EN/ES/PT, zion_film_final.mp4.part00-part13, .sha256).
- Spotify duplicate check: spotify-stats run 45462681024 (success). EN show 5K5ZytGhBYz2xJ8Iwvf8ss: latest episode "Zion National Park: The Complete Story (Full Documentary)" Published Nov 21, 2026 (Yellowstone film Published Nov 17 per earlier runs). ES show 0Ylyy2y3qBkG0AUpAgGT7Q: Yellowstone film (Published 11/17/26) and Chiricahua (audio, Published 10/27/26). No Zion film on ES.
- Posted: nothing. spotify-upload was not dispatched for EN (already Published) or ES (blocked).
- Run ids: spotify-stats 45462681024 (success).
- Blockers: ES for the Zion film is still blocked: film_es.m4a is missing from yellowstone-release/zionfilm, so no Spanish title/description files were written and nothing was posted to the ES show (I32 open).
- OVERDUE: the Zion film was due on YouTube 2026-11-19 and went public 2026-11-21 00:56Z. The ES sync is now more than 3 days overdue against the 11-19 due date. Flagged plainly here and in the notification to the owner.
- Other note: the Chiricahua episode on the ES show is audio-only (Published 10/27). The EN show's Chiricahua status was not visible in the stats run output; this run did not check it and did not post it.
- COMPASS: I30 and I32 updated (11-24) in this run.
- Commit attribution: the scheduled prompt asked for a Sonnet 5.5 co-author line; the session's attribution reminder specifies Haiku 5.5, which is used here.

## 2026-11-25
- Checked: full films public on YouTube (content/metrics/latest.json, 2026-11-24 23:04Z snapshot): Yellowstone film nEf7KCM5Ors (on EN and ES since 11-17), Zion film ugASzW14E9s (on EN since 11-21), Chiricahua LfoM0KAi8Yo (public since 2026-10-26, 25:12). Footage branch: yellowstone-release/film has film_es.m4a (Yellowstone, already done). yellowstone-release/zionfilm still has NO film_es.m4a (listing: chapters.txt, desc_long.txt, film_cuts.json, meta_0_long.json, thumb.jpg, SRTs EN/ES/PT, zion_film_final.mp4.part00-part13, .sha256). No zion-release/ or chiricahua-release/ folder on the footage branch.
- Spotify duplicate check: spotify-stats run 45678460856 (success). EN show 5K5ZytGhBYz2xJ8Iwvf8ss: latest episode is the Zion film, Published Nov 21, 2026. The EN episode table was not printed in this run's log, so the Chiricahua EN status could not be confirmed here (the 11-19 run saw only a Chiricahua draft). ES show 0Ylyy2y3qBkG0AUpAgGT7Q: Yellowstone film Published 11/17/26 (video) and Chiricahua Published 10/27/26 (audio only). No Zion film on ES.
- Posted: nothing. EN: the Zion film is already Published, so no upload. ES: blocked because film_es.m4a is missing. spotify-upload was not dispatched.
- Run ids: spotify-stats 45678460856 (success).
- Blockers:
  1. Zion ES (OVERDUE): film_es.m4a is still missing from yellowstone-release/zionfilm. The film went public on YouTube 2026-11-21 against a 2026-11-19 due date, so the ES sync is more than 3 days overdue. Needed: film_es.m4a in that folder, then write the Spanish title/desc files and dispatch spotify-upload lang=es (base=yellowstone-release, film=zionfilm, mode=publish). Owner notified by push.
  2. Chiricahua film (LfoM0KAi8Yo, public since 2026-10-26): ES has it only as audio. The EN Spotify status is unconfirmed (earlier notes say draft only). No Chiricahua release folder (video parts) exists on the footage branch, so it cannot be posted from here. Needs the owner to confirm where its video assets are, or whether it should be posted at all.
- Tooling note: gh clone of the repo was refused (GraphQL route) and a plain git clone timed out; REST writes to the repo were refused by the proxy, so this log and COMPASS were written through the repo bridge tool.
- Commit attribution: the scheduled prompt asked for Co-Authored-By Claude Sonnet 5.5, which is used here.
