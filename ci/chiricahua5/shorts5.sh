#!/usr/bin/env bash
# Episode 1 Shorts (v5 engine): render 3 vertical Shorts, QA frames, metadata; upload (scheduled) when PUBLISH=true.
set -euo pipefail
WS="$GITHUB_WORKSPACE"; D=/home/claude/doc/chiricahua; REL=$D/release_shorts; Q=/tmp/qa/qa/chiricahua-shorts-v5
cp "$WS/ci/chiricahua5/make_shorts.py" $D/make_shorts.py
md5sum $D/make_shorts.py
cd $D && python3 make_shorts.py 2>&1 | tee shorts.log
if grep -q SHORT_CAPACITY shorts.log; then echo "a shot cannot fill its phrase"; exit 1; fi
mkdir -p $REL $Q
for s in sh1 sh2 sh3; do
  f=shorts/chiricahua_$s.mp4; cp $f $REL/
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f); echo "$s $d"; python3 -c "assert float('$d') < 59.6"
  ffmpeg -v error -y -i $f -vf "fps=2,scale=180:-2,tile=10x12" -frames:v 1 -q:v 5 $Q/${s}_sheet.jpg
  ffmpeg -v error -y -i $f -vf scale=360:-2 -c:v libx264 -preset veryfast -b:v 400k -c:a aac -b:a 64k $Q/${s}_proxy.mp4
done
python3 - "$REL" <<'PY'
import json, sys
R = sys.argv[1]; LONG = "https://youtu.be/LfoM0KAi8Yo"
TAGS = ["chiricahua national park", "chiricahua", "64th national park", "newest national park", "arizona", "national parks", "history", "documentary"]
SH = [("sh1", "Who Killed Johnny Ringo? The Old West's Unsolved Death", "2026-10-26T18:30:00Z",
       "Found dead under an oak in 1882, boots missing, scalp cut away. The jury said suicide. Almost nobody believes it.",
       "#JohnnyRingo #WildWest #Tombstone #History #Shorts", ["johnny ringo", "tombstone", "wild west"]),
      ("sh3", "America's Newest National Park Was Made by a Super-Eruption", "2026-10-27T23:30:00Z",
       "Chiricahua just became America's 64th national park: rock spires from an eruption 1,000x bigger than Mount St. Helens, a face in the mountains, and a wild jaguar.",
       "#Chiricahua #NationalParks #Arizona #Geology #Shorts", ["geology", "hoodoos", "jaguar"]),
      ("sh2", "He Jumped From a Prison Train and Walked Home", "2026-10-29T01:30:00Z",
       "In 1886 the Army shipped the Chiricahua Apache east as prisoners of war. Massai jumped from the train and made his way back across hundreds of miles.",
       "#Apache #History #NativeAmericanHistory #Arizona #Shorts", ["massai", "apache", "chiricahua apache"])]
for sid, title, when, blurb, tags, extra in SH:
    open(f"{R}/desc_{sid}.txt", "w").write(f"{blurb}\n\nFull documentary: {LONG}\n\n{tags}")
    json.dump({"file": f"chiricahua_{sid}.mp4", "title": title, "description_file": f"desc_{sid}.txt", "tags": TAGS + extra, "category": "27",
               "privacy": "private", "publish_at": when, "made_for_kids": False, "synthetic": False, "language": "en",
               "playlist_title": "America's National Parks: The Hidden History"}, open(f"{R}/meta_{sid}.json", "w"), ensure_ascii=False, indent=1)
print("shorts meta ok")
PY
cp $REL/*.txt $REL/*.json $Q/
if [ "${PUBLISH:-false}" = "true" ]; then
  LOG="$WS/content/published/chiricahua_ep1.json"; cd $REL
  for s in sh1 sh3 sh2; do
    done_id=$(python3 -c "import json;print(json.load(open('$LOG')).get('meta_$s',''))")
    if [ -n "$done_id" ]; then echo "$s already uploaded: $done_id"; continue; fi
    python3 "$WS/scripts/yt_upload.py" meta_$s.json 2>&1 | tee up_$s.log
    vid=$(grep -oP '^VIDEO_ID=\K[\w-]{11}' up_$s.log | head -1); [ -n "$vid" ] || { echo "upload failed $s"; exit 1; }
    python3 -c "import json;p='$LOG';d=json.load(open(p));d['meta_$s']='$vid';json.dump(d,open(p,'w'),indent=1)"
  done
  cat "$LOG"
fi
echo SHORTS5_OK
