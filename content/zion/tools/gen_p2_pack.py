import json, re
D="/home/claude/doc/zion"; FILM="1KUANk1uGtU"; URL=f"https://youtu.be/{FILM}"
spec={r["id"]:r for r in json.load(open(f"{D}/reels_z2.json"))["reels"]}
txt={x["id"]:x["text"] for x in json.load(open(f"{D}/shorts_p2_script.json"))}
T={ # en title (with number), es, pt, hashtags
"w1":("A lake 350 feet deep once stood where Zion Lodge is","Un lago de 350 pies cubrió donde hoy está Zion Lodge","Um lago de 350 pés cobria onde hoje fica o Zion Lodge","#Zion #ZionLodge #History #NationalParks"),
"w2":("A mountain fell in about a minute: 112 mph, 4,800 years ago","Una montaña cayó en un minuto: 180 km/h, hace 4.800 años","Uma montanha caiu em um minuto: 180 km/h, há 4.800 anos","#Zion #Landslide #Geology #NationalParks"),
"w3":("Rebuilding Zion's fallen mountain would take 90 Hoover Dams of concrete","Reconstruir la montaña caída de Zion requeriría 90 presas Hoover de concreto","Reconstruir a montanha caída de Zion exigiria 90 represas Hoover de concreto","#Zion #HooverDam #Landslide #NationalParks"),
"w4":("430 people cut off, one road gone: Zion, April 1995","430 personas aisladas y una carretera perdida: Zion, abril de 1995","430 pessoas isoladas e uma estrada perdida: Zion, abril de 1995","#Zion #Landslide #History #NationalParks"),
"w5":("265,000 board feet of lumber came down a wire to Zion Lodge","265.000 pies tablares de madera bajaron por un cable a Zion Lodge","265 mil pés de madeira desceram por um cabo até o Zion Lodge","#Zion #ZionLodge #History #NationalParks"),
"w6":("3,000 feet up, a slab let go: Zion's Cable Mountain, 2019","A 900 metros de altura, una losa cedió: Cable Mountain, Zion, 2019","A 900 metros de altura, uma laje cedeu: Cable Mountain, Zion, 2019","#Zion #Rockfall #CableMountain #NationalParks"),
"w7":("Zion Lodge burned in 1966 and was rebuilt in 108 days","Zion Lodge se incendió en 1966 y se reconstruyó en 108 días","O Zion Lodge pegou fogo em 1966 e foi reconstruído em 108 dias","#Zion #ZionLodge #History #NationalParks"),
"w8":("80 deer became 600: the Zion cougar mystery","80 ciervos se volvieron 600: el misterio de los pumas de Zion","80 cervos viraram 600: o mistério das onças de Zion","#Zion #Wildlife #Ecology #NationalParks"),
"w9":("5,000 tons of rock fell in Zion in 1968","5.000 toneladas de roca cayeron en Zion en 1968","5.000 toneladas de rocha caíram em Zion em 1968","#Zion #Rockfall #History #NationalParks"),
"w10":("A lake lasted 700 years, then filled itself in","Un lago duró 700 años y luego se llenó solo","Um lago durou 700 anos e depois se encheu sozinho","#Zion #Geology #History #NationalParks")}
CUT=["Here's why","Full documentary","Watch The Day","The full story"]
def body(i):
    t=txt[i]; k=min([t.index(m) for m in CUT if m in t]+[len(t)]); return t[:k].strip()
YT=["2026-11-16T01:00:00Z","2026-11-16T18:00:00Z","2026-11-17T01:00:00Z","2026-11-17T18:00:00Z","2026-11-18T01:00:00Z","2026-11-18T18:00:00Z","2026-11-19T01:00:00Z","2026-11-19T18:00:00Z","2026-11-20T01:00:00Z","2026-11-20T18:00:00Z"]
IG=["2026-11-17T01:00:00Z","2026-11-17T20:00:00Z","2026-11-18T01:00:00Z","2026-11-18T20:00:00Z","2026-11-19T01:00:00Z","2026-11-19T20:00:00Z","2026-11-20T01:00:00Z","2026-11-20T20:00:00Z","2026-11-21T01:00:00Z","2026-11-21T20:00:00Z"]
TK=["2026-11-17T00:00:00Z","2026-11-17T03:00:00Z","2026-11-18T00:00:00Z","2026-11-18T03:00:00Z","2026-11-19T00:00:00Z","2026-11-19T03:00:00Z","2026-11-20T00:00:00Z","2026-11-20T03:00:00Z","2026-11-21T00:00:00Z","2026-11-21T03:00:00Z"]
import datetime as dt
metas={}; qi=[]; tk=[]
for n,i in enumerate(sorted(spec,key=lambda s:int(s[1:]))):
    en,es,pt,tags=T[i]; b=body(i); f=f"zion_p2_{i}.mp4"
    desc=f"{b}\n\n▶ Full documentary (Zion, Part 2: The Day the Mountain Fell: Zion's Lost Lake): {URL}\n\n#Shorts "+tags.replace("#Shorts","")
    pa=dt.datetime.fromisoformat(YT[n].replace("Z","+00:00"))+dt.timedelta(minutes=6)
    loc=lambda t:{"title":t+" #Shorts","description":desc}
    metas[i]={"file":f,"title":en+" #Shorts","description":desc,"tags":["Zion","national parks","Zion National Park","Shorts"]+[h[1:] for h in tags.split()[1:3]],
      "category":"27","privacy":"private","publish_at":YT[n],"made_for_kids":False,"synthetic":True,"language":"en",
      "queue_comment":{"after":pa.strftime("%Y-%m-%dT%H:%M:%SZ"),"text":f"▶ Watch the full documentary here: {URL}\nZion, Part 2 of our national parks series."},
      "localizations":{"es":loc(es),"pt":loc(pt)}}
    cap=f"{b}\n\n▶ The full documentary is on YouTube: search AlphaDog Studio, Zion Part 2 — link in the first comment 👇\n\n{tags}"
    cm=f"▶ Full documentary on YouTube: {URL}"
    qi.append({"id":f"zn2{i}_ig","platform":"instagram","file":f.replace(".mp4","_ig.mp4"),"at":IG[n],"thumb_ms":1200,"caption":cap,"comment":cm,**({"trial":True} if IG[n].endswith("20:00:00Z") else {})})
    qi.append({"id":f"zn2{i}_fb","platform":"facebook","file":f,"at":IG[n],"caption":cap,"comment":cm})
    tk.append({"mode":"post","artifact":"release:ys-shorts","file":f,"due":TK[n],"service":"tiktok","text":b+"\\n\\n▶ Full documentary on YouTube: search AlphaDog Studio, Zion Part 2\\n\\n"+tags})
json.dump({"metas":metas,"queue":qi,"tiktok":tk},open("/tmp/p2_pack.json","w"),indent=1,ensure_ascii=False)
for i in metas: print(i,metas[i]["publish_at"],metas[i]["title"])
