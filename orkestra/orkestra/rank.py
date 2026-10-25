"""Damıtıcı sıralama: BM25 + embedding hibrit (RRF), atıf sayısı, tohum yakınlığı, kümeleme.

Embedding: MiniLM (sentence-transformers, gapmine'ın yerel önbelleği) varsa o; yoksa
TF-IDF + SVD yedeği. Hangisinin kullanıldığı funnel'a yazılır (sessiz düşüş yok).
MiniLM 256 token görür: metin başlık + özetin ilk `embed_words` kelimesi; kesilen kayıt sayılır.
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter

import numpy as np

_TOK = re.compile(r"[a-z0-9][a-z0-9_\-]*")
STOP = set("""a an the of for and or in on to with by using via is are be from at as into its their that this we
our these those which can such also than more most based new not no it was were has have been show results paper
propose proposed approach method methods study""".split())


def toks(s: str) -> list[str]:
    return [t for t in _TOK.findall((s or "").lower()) if t not in STOP and len(t) > 1]


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.4, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.N = len(docs)
        self.avg = (sum(len(d) for d in docs) / self.N) if self.N else 0.0
        df = Counter(t for d in docs for t in set(d))
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}
        self.tf = [Counter(d) for d in docs]

    def scores(self, q: list[str]) -> np.ndarray:
        out = np.zeros(self.N, dtype=np.float64)
        qset = set(q)
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in qset:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / (self.avg or 1)))
            out[i] = s
        return out


def doc_text(r: dict, words: int) -> tuple[str, bool]:
    ab = (r.get("abstract") or "").split()
    return f"{r.get('title') or ''}. {' '.join(ab[:words])}", len(ab) > words


class Embedder:
    def __init__(self, cfg):
        self.cfg = cfg
        self.name = None
        self._m = None

    def _try_minilm(self) -> bool:
        if self.cfg.embed_backend == "tfidf":
            return False
        try:
            hf = self.cfg.hf_cache
            if hf and os.path.isdir(hf):
                os.environ.setdefault("HF_HOME", hf)
                if os.path.isdir(os.path.join(hf, "hub", "models--" + self.cfg.embed_model.replace("/", "--"))):
                    os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer
            self._m = SentenceTransformer(self.cfg.embed_model, device="cpu",
                                          cache_folder=os.path.join(hf, "hub") if hf and os.path.isdir(hf) else None)
            self.name = "minilm"
            return True
        except Exception as exc:  # paket/model yok → açıkça yedeğe düş ve kaydet
            if self.cfg.embed_backend == "minilm":
                raise
            self.err = f"{type(exc).__name__}: {exc}"[:200]
            return False

    def fit_encode(self, docs: list[str], queries: list[str]) -> tuple[np.ndarray, np.ndarray]:
        if self._m is None and self.name is None:
            if not self._try_minilm():
                self.name = "tfidf_svd(yedek)"
        if self.name == "minilm":
            d = self._m.encode(docs, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
            q = self._m.encode(queries, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(d, dtype=np.float32), np.asarray(q, dtype=np.float32)
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(sublinear_tf=True, stop_words="english", min_df=1)
        X = vec.fit_transform(docs + queries)
        k = max(2, min(128, X.shape[0] - 1, X.shape[1] - 1))
        Z = TruncatedSVD(n_components=k, random_state=0).fit_transform(X)
        Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9
        return Z[: len(docs)].astype(np.float32), Z[len(docs):].astype(np.float32)


def _rank_of(scores: np.ndarray) -> np.ndarray:
    order = np.argsort(-scores, kind="stable")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(order))
    return ranks


def _norm(x: np.ndarray) -> np.ndarray:
    lo, hi = float(np.min(x)) if len(x) else 0.0, float(np.max(x)) if len(x) else 0.0
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def query_texts(soru: str, subs: list[dict]) -> list[str]:
    return [soru] + [f"{s['soru']} {' '.join(s.get('sorgular') or [])}" for s in subs]


def score(recs: list[dict], soru: str, subs: list[dict], cfg, embedder: Embedder, funnel=None,
          use_rel: bool = False) -> np.ndarray:
    """Her kayda `skor`, `bm25_sira`, `emb_sira`, `emb` (vektör) yazar; skor dizisini döner."""
    if not recs:
        return np.zeros(0)
    texts, cut = zip(*(doc_text(r, cfg.embed_words) for r in recs))
    if funnel is not None:
        funnel.info["embed.kesilen_metin(son)"] = int(sum(cut))
    qs = query_texts(soru, subs)
    bm = BM25([toks(t) for t in texts])
    bm_s = np.max(np.stack([bm.scores(toks(q)) for q in qs]), axis=0)
    D, Q = embedder.fit_encode(list(texts), qs)
    em_s = np.max(D @ Q.T, axis=1)
    if funnel is not None:
        funnel.info["embed.backend=" + str(embedder.name)] = 1
    rb, re_ = _rank_of(bm_s), _rank_of(em_s)
    hybrid = 1.0 / (60 + rb) + 1.0 / (60 + re_)
    cites = np.array([math.log1p(r["citations"]) if isinstance(r.get("citations"), int) else 0.0 for r in recs])
    prox = np.array([min(len(r.get("seed_of") or []), 5) / 5 for r in recs])
    anchor = np.array([1.0 if r.get("anchor") else 0.0 for r in recs])
    multi = np.array([min(len(set(r.get("sources") or [])), 4) / 4 for r in recs])
    if use_rel:
        rel = np.array([(r["rel"] / 3) if isinstance(r.get("rel"), int) else 0.5 for r in recs])
    else:
        rel = np.full(len(recs), 0.5)
    s = (0.35 * _norm(hybrid) + 0.20 * rel + 0.15 * _norm(cites) + 0.12 * prox + 0.12 * anchor + 0.06 * multi)
    for i, r in enumerate(recs):
        r["skor"] = float(s[i])
        r["bm25_sira"] = int(rb[i])
        r["emb_sira"] = int(re_[i])
    for i, r in enumerate(recs):
        r["_emb"] = D[i]
    return s


def cluster(recs: list[dict], k: int) -> None:
    if len(recs) < 4:
        for r in recs:
            r["kume"] = 0
        return
    from sklearn.cluster import KMeans
    X = np.stack([r["_emb"] for r in recs])
    k = max(2, min(k, len(recs) // 4))
    lab = KMeans(n_clusters=k, n_init=4, random_state=0).fit_predict(X)
    for r, l in zip(recs, lab):
        r["kume"] = int(l)


def top_with_cap(recs: list[dict], n: int, cap_frac: float) -> list[dict]:
    """Skora göre ilk n; tek kümeden en çok ⌈n·cap_frac⌉ (yer kalırsa atlananlarla doldurulur)."""
    order = sorted(recs, key=lambda r: -r["skor"])
    cap = max(1, math.ceil(n * cap_frac))
    per: Counter = Counter()
    out, skipped = [], []
    for r in order:
        if len(out) >= n:
            break
        if per[r.get("kume", 0)] >= cap:
            skipped.append(r)
            continue
        per[r.get("kume", 0)] += 1
        out.append(r)
    for r in skipped:
        if len(out) >= n:
            break
        out.append(r)
    return out
