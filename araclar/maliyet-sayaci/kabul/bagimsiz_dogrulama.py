"""Bagimsiz kabul dogrulamasi (maliyet-sayaci). Aracin kodunu IMPORT ETMEZ.
Yalniz json + stdlib. Transkriptler salt okunur.
Cikti: JSON -> stdout. Kullanim: python bagimsiz_dogrulama.py ana|reg"""
import json, re, sys, glob, os
from collections import defaultdict
KOK = os.path.expanduser(r"~\.claude\projects")
KESIM = "2026-10-25T10:00:00"   # ONKAYIT: UTC
def ajan_id(path):
    m = re.search(r"agent-([0-9a-f]+)\.jsonl$", path.replace("\\", "/"))
    return m.group(1) if m else None
def oku(path):
    """-> (mesajlar{id:usage(max)}, sirali [(ts, id)], ilk_ts, bozuk)"""
    msgs = {}; ts_of = {}; first = None; bad = 0; order = {}
    with open(path, "r", encoding="utf8", errors="replace") as f:
        for n, ln in enumerate(f):
            ln = ln.strip()
            if not ln: continue
            try: d = json.loads(ln)
            except Exception: bad += 1; continue
            if not isinstance(d, dict): bad += 1; continue
            ts = d.get("timestamp")
            if ts and (first is None or ts < first): first = ts
            if d.get("type") != "assistant": continue
            m = d.get("message") or {}
            if m.get("model") == "<synthetic>": continue
            u = m.get("usage")
            if not isinstance(u, dict): continue
            mid = m.get("id") or d.get("requestId") or f"_{path}:{n}"
            cur = msgs.setdefault(mid, {"i": 0, "o": 0, "cc": 0, "cr": 0})
            for k, a in (("i", "input_tokens"), ("o", "output_tokens"),
                         ("cc", "cache_creation_input_tokens"), ("cr", "cache_read_input_tokens")):
                cur[k] = max(cur[k], u.get(a) or 0)
            if mid not in ts_of or (ts and ts < ts_of[mid]): ts_of[mid] = ts or ""
            order.setdefault(mid, n)
    return msgs, ts_of, order, first, bad
def son_toplam(msgs, ts_of, order):
    if not msgs: return None, 0
    # en gec zaman; esitlikte dosyada sonra gelen
    mid = max(msgs, key=lambda k: (ts_of[k], order[k]))
    u = msgs[mid]; return u["i"] + u["o"] + u["cc"] + u["cr"], sum(1 for _ in msgs)
def tum_ajan_dosyalari():
    out = {}
    for p in glob.glob(os.path.join(KOK, "**", "agent-*.jsonl"), recursive=True):
        out.setdefault(ajan_id(p), []).append(p)
    return out
NOT = re.compile(r"<task-id>([0-9a-f]+)</task-id>.*?<subagent_tokens>(\d+)</subagent_tokens>", re.S)
def bildirimler():
    """task-id -> [(ts, tokens, oturum_dosyasi)] (yalniz ana oturum jsonl'leri, satirdaki timestamp)"""
    res = defaultdict(list)
    for p in glob.glob(os.path.join(KOK, "*", "*.jsonl")):
        with open(p, "r", encoding="utf8", errors="replace") as f:
            for ln in f:
                if "subagent_tokens" not in ln: continue
                try: d = json.loads(ln)
                except Exception: continue
                if d.get("type") != "queue-operation": continue   # kaynak: kuyruk bildirimi
                c = d.get("content")
                if not isinstance(c, str): continue
                for tid, tok in NOT.findall(c):
                    res[tid].append((d.get("timestamp"), int(tok), os.path.basename(p)))
    return res
if __name__ == "__main__":
    mod = sys.argv[1]
    dosyalar = tum_ajan_dosyalari(); bil = bildirimler()
    rows = []
    for aid, paths in sorted(dosyalar.items()):
        # ayni ajan birden fazla yolda olabilir (hard link); ilkini al, hepsini tekillestir
        allm, allts, allo = {}, {}, {}; first = None
        for p in paths:
            m, t, o, f0, _ = oku(p)
            for k, v in m.items():
                allm.setdefault(k, v); allts.setdefault(k, t[k]); allo.setdefault(k, o[k])
            if f0 and (first is None or f0 < first): first = f0
        son, n = son_toplam(allm, allts, allo)
        rows.append({"ajan": aid, "ilk": first, "n_mesaj": n, "son_baglam_cikti": son,
                     "bildirimler": bil.get(aid, []), "yol": paths[0]})
    if mod == "ana":
        rows = [r for r in rows if r["ilk"] and r["ilk"] >= KESIM and r["bildirimler"]]
    print(json.dumps(rows, indent=1, ensure_ascii=False))
