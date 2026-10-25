"""Funnel muhasebesi: her aşama giren = çıkan + Σ düşen. Tutmazsa `UNACCOUNTED` sebebi
eklenir ve `ok=False` olur (sessiz kayıp yok). Kaynak durumları (OK / EKSİK / KAPALI)
ve bilgi sayaçları (API'nin kesip hiç göndermediği sonuçlar gibi) ayrı tutulur.
"""
from __future__ import annotations

import threading
from collections import Counter
from dataclasses import dataclass, field

OK = "OK"
EKSIK = "EKSİK"
KAPALI = "KAPALI"


@dataclass
class Stage:
    name: str
    giren: int
    cikan: int
    dusen: dict[str, int]
    not_: str = ""

    @property
    def ok(self) -> bool:
        return self.giren == self.cikan + sum(self.dusen.values())

    def as_dict(self) -> dict:
        return {"asama": self.name, "giren": self.giren, "cikan": self.cikan,
                "dusen": dict(self.dusen), "ok": self.ok, "not": self.not_}


@dataclass
class Funnel:
    stages: list[Stage] = field(default_factory=list)
    sources: dict[str, dict] = field(default_factory=dict)  # ad -> {durum, sebep, istek, kayit, ...}
    info: Counter = field(default_factory=Counter)  # muhasebe dışı bilgi sayaçları
    errors: Counter = field(default_factory=Counter)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def stage(self, name: str, giren: int, cikan: int, dusen: dict[str, int] | None = None,
              not_: str = "") -> Stage:
        d = {k: int(v) for k, v in (dusen or {}).items() if v}
        st = Stage(name, int(giren), int(cikan), d, not_)
        if not st.ok:
            gap = st.giren - st.cikan - sum(d.values())
            st.dusen["UNACCOUNTED"] = gap
        with self._lock:
            self.stages.append(st)
        return st

    def source(self, name: str, durum: str, sebep: str = "", **sayac) -> None:
        with self._lock:
            cur = self.sources.setdefault(name, {"durum": OK, "sebep": "", "istek": 0, "kayit": 0})
            # EKSİK yapışkandır: bir kez EKSİK olan kaynak OK'ye dönmez
            if cur["durum"] != EKSIK or durum == EKSIK:
                cur["durum"] = durum
                if sebep:
                    cur["sebep"] = sebep
            for k, v in sayac.items():
                if isinstance(v, (int, float)):
                    cur[k] = cur.get(k, 0) + v
                else:
                    cur[k] = v

    def bump(self, key: str, n: int = 1) -> None:
        with self._lock:
            self.info[key] += n

    def error(self, key: str, n: int = 1) -> None:
        with self._lock:
            self.errors[key] += n

    @property
    def eksik(self) -> list[str]:
        return [k for k, v in self.sources.items() if v["durum"] == EKSIK]

    @property
    def balanced(self) -> bool:
        return all(s.ok and "UNACCOUNTED" not in s.dusen for s in self.stages)

    def as_dict(self) -> dict:
        return {
            "durum": EKSIK if self.eksik else OK,
            "eksik_kaynaklar": self.eksik,
            "dengeli": self.balanced,
            "asamalar": [s.as_dict() for s in self.stages],
            "kaynaklar": self.sources,
            "bilgi": dict(self.info),
            "hatalar": dict(self.errors),
        }

    def table(self) -> str:
        rows = ["| aşama | giren | çıkan | düşen (sebep) |", "|---|---:|---:|---|"]
        for s in self.stages:
            d = ", ".join(f"{k} {v}" for k, v in sorted(s.dusen.items(), key=lambda x: -x[1])) or "–"
            rows.append(f"| {s.name} | {s.giren} | {s.cikan} | {d} |")
        return "\n".join(rows)
