"""Ana test: gorulmemis ajanlar. Girdi: bagimsiz_dogrulama.py ana ciktisi (JSON dosyasi). Aracin --json ciktisi ile karsilastirir."""
import json, sys, re, subprocess, os
ARAC = r"C:\Users\LENOVO\Projeler\forge\araclar\maliyet-sayaci\maliyet_sayaci.py"
HAKEM = r"C:\Users\LENOVO\AppData\Local\Temp\claude\C--Users-LENOVO\76053f18-2f05-4b54-95dc-6d814aa601eb\scratchpad\hakem\agents.json"
rows = json.load(open(sys.argv[1], encoding="utf-8-sig"))
hak = {a["ajan"] for a in json.load(open(HAKEM, encoding="utf8"))["ajanlar"]}
cache = {}
out = []
for x in rows:
    parts = x["yol"].replace("\\", "/").split("/"); i = parts.index("projects"); proje, oturum = parts[i+1], parts[i+2]

    if oturum not in cache:
        r = subprocess.run([sys.executable, ARAC, "agents", "--session", oturum[:8], "--proje", proje, "--json"] if False else
                           [sys.executable, ARAC, "agents", "--session", oturum[:8], "--json"], capture_output=True, text=True, encoding="utf8")
        cache[oturum] = {a["ajan"]: a for a in json.loads(r.stdout)["ajanlar"]}
    ta = cache[oturum].get(x["ajan"])
    off = max(x["bildirimler"], key=lambda b: b[0])[1]
    tv = ta["son_baglam_cikti"] if ta else None
    out.append({"ajan": x["ajan"], "oturum": oturum[:8], "ilk": x["ilk"], "hakem_goruntusunde": x["ajan"] in hak,
                "resmi_son_bildirim": off, "arac": tv, "bagimsiz": x["son_baglam_cikti"],
                "sapma_arac_pct": None if tv is None else round(100*(tv-off)/off, 3),
                "sapma_bagimsiz_pct": round(100*(x["son_baglam_cikti"]-off)/off, 3), "n_bildirim": len(x["bildirimler"])})
for o in out: print(o)
