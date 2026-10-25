"""Regresyon: hakemin 19 ajani. (1) hakem anlik goruntusu (agents.json) ile ARACIN, transkriptleri
hakem anlik goruntusu zamanina (ana'nin son ts'i) KESILMIS bir kopyada calistirilmis ciktisi,
(2) ayni goruntu ile bu betigin kendi bagimsiz sayimi, (3) kesilmemis canli veri.
Aracin kodu calistirilir (subprocess) ama dogrulama sayimi burada ayri yazilmistir."""
import json, os, re, shutil, subprocess, sys, glob
HAKEM = r"C:\Users\LENOVO\AppData\Local\Temp\claude\C--Users-LENOVO\76053f18-2f05-4b54-95dc-6d814aa601eb\scratchpad\hakem\agents.json"
KOK = os.path.expanduser(r"~\.claude\projects\C--Users-LENOVO")
OT = "76053f18-2f05-4b54-95dc-6d814aa601eb"
ARAC = r"C:\Users\LENOVO\Projeler\forge\araclar\maliyet-sayaci\maliyet_sayaci.py"
TMP = sys.argv[1]  # gecici dizin
h = json.load(open(HAKEM, encoding="utf8"))
hk = {a["ajan"]: a for a in h["ajanlar"]}
SNAP = max(a["son"] for a in h["ajanlar"])           # hakem goruntusunun sonu
tot = lambda a: a["input"] + a["output"] + a["cw5m"] + a["cw1h"] + a["cache_read"]
# kesilmis kopya
kopya = os.path.join(TMP, "projects", "C--Users-LENOVO")
if os.path.exists(os.path.join(TMP, "projects")): shutil.rmtree(os.path.join(TMP, "projects"))
os.makedirs(kopya)
def kes(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, encoding="utf8", errors="replace") as f, open(dst, "w", encoding="utf8") as g:
        for ln in f:
            try: d = json.loads(ln)
            except Exception: continue
            ts = d.get("timestamp")
            if ts and ts > SNAP: continue
            g.write(ln)
kes(os.path.join(KOK, OT + ".jsonl"), os.path.join(kopya, OT + ".jsonl"))
for p in glob.glob(os.path.join(KOK, OT, "subagents", "**", "agent-*.jsonl"), recursive=True):
    kes(p, os.path.join(kopya, os.path.relpath(p, KOK)))
for p in glob.glob(os.path.join(KOK, OT, "subagents", "**", "agent-*.meta.json"), recursive=True):
    d = os.path.join(kopya, os.path.relpath(p, KOK)); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy(p, d)
def arac(root):
    r = subprocess.run([sys.executable, ARAC, "--root", root, "agents", "--session", "76053f18", "--json"],
                       capture_output=True, text=True, encoding="utf8"); return json.loads(r.stdout)
def bagimsiz(root):
    """aracdan bagimsiz: dosya basina message.id tekillestir (alan max), ajan basina topla"""
    out = {}
    files = [(OT, os.path.join(root, OT + ".jsonl"))] + [(re.search(r"agent-([0-9a-f]+)\.jsonl$", p.replace("\\","/")).group(1), p)
             for p in glob.glob(os.path.join(root, OT, "subagents", "**", "agent-*.jsonl"), recursive=True)]
    for aid, p in files:
        m = {}
        for ln in open(p, encoding="utf8", errors="replace"):
            try: d = json.loads(ln)
            except Exception: continue
            if d.get("type") != "assistant": continue
            mm = d.get("message") or {}; u = mm.get("usage")
            if not isinstance(u, dict): continue
            c = m.setdefault(mm.get("id") or d.get("requestId") or ln[:50], [0,0,0,0])
            for i, k in enumerate(("input_tokens","output_tokens","cache_creation_input_tokens","cache_read_input_tokens")):
                c[i] = max(c[i], u.get(k) or 0)
        out["ana" if aid == OT else aid] = (len(m), sum(sum(v) for v in m.values()))
    return out
res = {"snap": SNAP, "satirlar": []}
for ad, root in (("kesik", os.path.join(TMP, "projects")), ("canli", os.path.expanduser(r"~\.claude\projects"))):
    t = arac(root); ta = {a["ajan"]: a for a in t["ajanlar"]}
    b = bagimsiz(os.path.join(root, "C--Users-LENOVO"))
    ht = hs = tl = bs = 0; n_ok = 0
    for aid, a in hk.items():
        x = ta.get(aid); y = b.get(aid)
        tt = (x["input"] + x["output"] + x["cache_write"] + x["cache_read"]) if x else None
        res["satirlar"].append({"mod": ad, "ajan": aid, "hakem": tot(a), "arac": tt, "bagimsiz": y[1] if y else None,
                                "hakem_msj": a["mesaj"], "arac_msj": x["mesaj"] if x else None, "bag_msj": y[0] if y else None})
        ht += tot(a); tl += tt or 0; bs += y[1] if y else 0
    res[ad] = {"hakem_toplam": ht, "arac_toplam": tl, "bagimsiz_toplam": bs,
               "sapma_arac_pct": 100*(tl-ht)/ht, "sapma_bag_pct": 100*(bs-ht)/ht}
print(json.dumps(res, indent=1))
