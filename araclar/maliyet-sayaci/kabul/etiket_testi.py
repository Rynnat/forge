"""Etiket katmani: son 7 gunde (simdi=argv[1] ISO UTC) etiketsiz pay'i bagimsiz hesapla. Aracin kodunu kullanmaz."""
import csv, glob, json, os, re, sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict
KOK = os.path.expanduser(r"~\.claude\projects")
CSV = r"C:\Users\LENOVO\Projeler\forge\araclar\maliyet-sayaci\etiketler.csv"
simdi = datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00")) if len(sys.argv) > 1 else datetime.now(timezone.utc)
bas = simdi - timedelta(days=7)
kurallar = []
for ln in open(CSV, encoding="utf8"):
    ln = ln.strip()
    if not ln or ln.startswith("#") or ln.startswith("oturum_onek"): continue
    o, a, e = (ln.split(",") + ["", "", ""])[:3]
    kurallar.append((o.strip(), a.strip(), e.strip()))
def etiket(oturum, ajan):   # ajan: 'ana' ya da ajan id
    best = None
    for o, a, e in kurallar:
        if not oturum.startswith(o) or not o: continue
        if a and not (a == ajan or (a != "ana" and ajan.startswith(a))): continue
        key = (1 if a else 0, len(o), len(a))
        if best is None or key > best[0]: best = (key, e)
    return best[1] if best else "etiketsiz"
msgs = {}   # id -> (oturum, ajan, ts, tokens)  global tekillestirme: alan basina max
for p in glob.glob(os.path.join(KOK, "**", "*.jsonl"), recursive=True):
    q = p.replace("\\", "/")
    m = re.search(r"/([0-9a-f-]{36})(?:/subagents/(?:workflows/[^/]+/)?agent-([0-9a-f]+))?\.jsonl$", q) or \
        re.search(r"/([0-9a-f-]{36})/subagents/(?:workflows/[^/]+/)?agent-([0-9a-f]+)\.jsonl$", q)
    if not m: continue
    oturum, ajan = m.group(1), (m.group(2) or "ana")
    with open(p, encoding="utf8", errors="replace") as f:
        for ln in f:
            if '"type":"assistant"' not in ln.replace('": "', '":"'): continue
            try: d = json.loads(ln)
            except Exception: continue
            if d.get("type") != "assistant": continue
            mm = d.get("message") or {}; u = mm.get("usage")
            if not isinstance(u, dict) or mm.get("model") == "<synthetic>": continue
            ts = d.get("timestamp")
            if not ts: continue
            k = mm.get("id") or d.get("requestId") or f"{p}:{ln[:40]}"
            v = [u.get(x) or 0 for x in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")]
            if k in msgs:
                o = msgs[k]; o[3] = [max(a, b) for a, b in zip(o[3], v)]; o[2] = min(o[2], ts)
            else: msgs[k] = [oturum, ajan, ts, v]
pay = defaultdict(int); eo = defaultdict(int)
for oturum, ajan, ts, v in msgs.values():
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if not (bas <= t <= simdi): continue
    e = etiket(oturum, ajan); pay[e] += sum(v)
    if e == "etiketsiz": eo[oturum[:8]] += sum(v)
tot = sum(pay.values())
print(json.dumps({"pencere": [bas.isoformat(), simdi.isoformat()], "toplam_token": tot,
                  "paylar_pct": {k: round(100*v/tot, 2) for k, v in pay.items()},
                  "etiketsiz_oturumlar_token": dict(eo)}, indent=1))
