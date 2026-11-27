#!/usr/bin/env python3
"""Zion Part 3 pack: --metas DIR writes YouTube Shorts metas; --queue appends IG/FB/story queue + TikTok backlog entries to content/ (idempotent)."""
import json, sys, datetime as dt
SPEC=json.load(open("content/zion/tools/shorts_p6_spec.json"))["items"]; Y="https://youtu.be/ugASzW14E9s"; OFF=0; SOFF=0
START=dt.datetime(2026,12,2,20,0,tzinfo=dt.timezone.utc); SSTART=dt.datetime(2026,11,28,19,0,tzinfo=dt.timezone.utc)
shorts=[i for i in SPEC if i["kind"]=="short"]; stories=[i for i in SPEC if i["kind"]=="story"]
def z(d): return d.strftime("%Y-%m-%dT%H:%M:%SZ")
def slot(n):   # Shorts alternate 20:00Z and 01:00Z (next day) starting at START
    return (START+dt.timedelta(days=(n+1)//2)).replace(hour=20 if n%2==0 else 1)
def sslot(n):  # Stories alternate 19:00Z and 02:00Z (next day) starting at SSTART
    return (SSTART+dt.timedelta(days=(n+1)//2)).replace(hour=19 if n%2==0 else 2)
TAGS="#Zion #ZionNationalPark #History #NationalParks"
CR="Video: the channel's own footage from Zion (2021). Photos: NPS, HABS/HAER, NARA (Beaman/Hillers) and Wikimedia Commons (public domain, CC0)."
def cap(i): return f"{i['caption']}\n\n{CR}\n\n▶ The full documentary is on YouTube: search AlphaDog Studio, Zion — link in the first comment 👇\n\n{TAGS}"
if "--metas" in sys.argv:
    out=sys.argv[sys.argv.index("--metas")+1]
    for n,i in enumerate(shorts):
        t=slot(n+OFF); title=i["hook"].rstrip(".")+" #Shorts"
        m={"file":i["file"],"title":title,"description":f"{i['caption']}\n\n{CR}\n\n▶ Full Zion documentary: {Y}\n\n#Shorts #Zion #History #NationalParks","tags":["Zion","national parks","Zion National Park","Shorts","history","hiking","Utah",*({"z6s1":["Angels Landing"],"z6s2":["Angels Landing","Walter's Wiggles"],"z6s3":["Zion Narrows","Virgin River"]}.get(i["id"],[]))],"category":"27","privacy":"private","publish_at":z(t),"made_for_kids":False,"synthetic":False,"language":"en",
           "queue_comment":{"after":z(t+dt.timedelta(minutes=6)),"text":f"▶ Watch the full documentary here: {Y}\nThe full Zion documentary, with the history behind these places."}}
        json.dump(m,open(f"{out}/meta_{i['id']}.json","w"),ensure_ascii=False,indent=1)
if "--queue" in sys.argv:
    q=json.load(open("content/social_queue.json")); have={x["id"] for x in q}; tb=json.load(open("content/tiktok_backlog.json"))
    for n,i in enumerate(shorts):
        t=slot(n+OFF); c=cap(i); cm=f"▶ Full documentary on YouTube: {Y}"
        for plat,suf in (("instagram","ig"),("facebook","fb")):
            iid=f"{i['id']}_{suf}"
            if iid in have: continue
            e={"id":iid,"platform":plat,"file":i["file"],"at":z(t),"caption":c,"comment":cm}
            if plat=="instagram": e["thumb_ms"]=1200
            q.append(e)
        due=t+dt.timedelta(hours=2) if n%2==0 else (t+dt.timedelta(hours=4))
        if not any(b["file"]==i["file"] for b in tb):
            tb.append({"mode":"post","artifact":"release:ys-shorts","file":i["file"],"due":z(due),"service":"tiktok","text":f"{i['caption']}\\n\\n{CR}\\n\\n▶ Full documentary on YouTube: search AlphaDog Studio, Zion\\n\\n{TAGS}"})
    for n,i in enumerate(stories):
        t=sslot(n+SOFF)
        for plat,suf in (("instagram_story","ig"),("facebook_story","fb")):
            iid=f"{i['id']}_{suf}"
            if iid in have: continue
            q.append({"id":iid,"platform":plat,"file":i["file"],"at":z(t),"story_v2":f"{i['hook']} | zion6"})
    json.dump(q,open("content/social_queue.json","w"),ensure_ascii=False,indent=1); json.dump(tb,open("content/tiktok_backlog.json","w"),ensure_ascii=False,indent=1)
    print("queue",len(q),"backlog",len(tb))
