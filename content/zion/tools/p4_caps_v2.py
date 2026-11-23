#!/usr/bin/env python3
"""Research-based caption v2 for NOT-yet-posted Part 3 Shorts (IG/FB queue + TikTok backlog). Posted items are never touched.
Rules from 2026 research: keyword-first opening, specific hook, sends/saves CTA (IG: sends-per-reach; TikTok: saves/shares),
3-6 tiered hashtags (TikTok), caption 150-225 chars for TikTok, film link in first comment (IG/FB) / caption pointer."""
import json, re
spec={i["id"]:i for i in json.load(open("content/zion/tools/shorts_p4_spec.json"))["items"] if i["kind"]=="short"}
def first2(t):
    s=re.split(r'(?<=[.!?])\s+',t.strip()); return " ".join(s[:2])
IGTAGS="#ZionNationalPark #NationalParkHistory #UtahHistory #HiddenHistory #Zion"
TTTAGS="#zionnationalpark #nationalparks #history #utah #hiddenhistory"
ig_cta="Send this to someone who has hiked Zion, or is planning to. Save it for your trip."
Q=json.load(open("content/social_queue.json")); n=0
for e in Q:
    sid=e["id"].rsplit("_",1)[0]
    if sid in spec and not e.get("done") and e["platform"] in("instagram","facebook"):
        i=spec[sid]
        e["caption"]=f"Zion National Park history: {i['hook']}\n\n{first2(i['caption'])}\n\n{ig_cta}\n\n▶ Full documentary on YouTube (link in the first comment): the Zion documentary by AlphaDog Studio\n\n{IGTAGS}"; n+=1
json.dump(Q,open("content/social_queue.json","w"),indent=1,ensure_ascii=False)
B=json.load(open("content/tiktok_backlog.json")); m=0
for x in B:
    sid=x["file"].replace("zion_p4_","").replace(".mp4","")
    if sid in spec and not x.get("scheduled"):
        i=spec[sid]; t=f"Zion National Park history: {i['hook'].rstrip('.')}. Save this for your trip, full story on YouTube (AlphaDog Studio)."
        x["text"]=(t[:200]+"\\n\\n"+TTTAGS); m+=1
json.dump(B,open("content/tiktok_backlog.json","w"),indent=1,ensure_ascii=False)
print("queue entries",n,"tiktok",m)
