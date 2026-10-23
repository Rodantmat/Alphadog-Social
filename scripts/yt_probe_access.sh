#!/usr/bin/env bash
# Try several yt-dlp strategies against one public CC video and report which ones can read metadata + download a few seconds.
VID="${1:-fuZI24Ncioc}"
URL="https://www.youtube.com/watch?v=$VID"
try() {
  name="$1"; shift
  if timeout 120 yt-dlp -4 --no-warnings "$@" -j --skip-download "$URL" > /tmp/meta.json 2>/tmp/err.txt; then
    lic=$(python3 -c "import json;print(json.load(open('/tmp/meta.json')).get('license'))")
    if timeout 300 yt-dlp -4 --no-warnings "$@" -f "bv*[height<=1080]" --download-sections "*10-16" -o "/tmp/t_$name.%(ext)s" "$URL" >/dev/null 2>/tmp/err2.txt; then
      echo "RESULT $name META_OK DL_OK license=$lic file=$(ls /tmp/t_$name.* 2>/dev/null | head -1)"
    else
      echo "RESULT $name META_OK DL_FAIL $(tail -c 200 /tmp/err2.txt | tr '\n' ' ')"
    fi
  else
    echo "RESULT $name META_FAIL $(tail -c 160 /tmp/err.txt | tr '\n' ' ')"
  fi
}
try default
try tv --extractor-args "youtube:player_client=tv"
try web_embedded --extractor-args "youtube:player_client=web_embedded"
try mweb --extractor-args "youtube:player_client=mweb"
try android_vr --extractor-args "youtube:player_client=android_vr"
try tv_simply --extractor-args "youtube:player_client=tv_simply"
try web_safari --extractor-args "youtube:player_client=web_safari"
try ios --extractor-args "youtube:player_client=ios"
echo "--- with bgutil PO token provider ---"
try pot_default --extractor-args "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416"
try pot_mweb --extractor-args "youtube:player_client=mweb;youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416"
try pot_web --extractor-args "youtube:player_client=web;youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416"
echo "--- invidious / piped style mirrors via plain curl ---"
for h in inv.nadeko.net yewtu.be invidious.nerdvpn.de; do
  code=$(curl -s -o /tmp/inv.json -w "%{http_code}" --max-time 20 "https://$h/api/v1/videos/$VID?fields=title,formatStreams,adaptiveFormats,license")
  echo "RESULT invidious_$h http=$code $(head -c 150 /tmp/inv.json | tr '\n' ' ')"
done
