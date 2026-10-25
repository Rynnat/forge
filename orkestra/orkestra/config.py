"""Yapılandırma: varsayılanlar + isteğe bağlı `orkestra.toml` + ortam değişkenleri.

OpenAlex anahtarı: `orkestra.toml` içindeki `openalex_api_key` ya da `OPENALEX_API_KEY`.
S2 anahtarı: `s2_api_key` ya da `S2_API_KEY`.
Anahtar yoksa OpenAlex yalnız günlük istek bütçesiyle (dosyada kalıcı sayaç) kullanılır;
bütçe biterse kaynak EKSİK işaretlenir.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # forge/orkestra


@dataclass
class SourceLimits:
    min_interval_s: float = 1.0
    max_retries: int = 4
    backoff_s: tuple[float, ...] = (10.0, 30.0, 60.0, 120.0)  # Retry-After'sız 429 için
    max_wait_s: float = 300.0  # Retry-After bundan büyükse kota bitti sayılır
    es_zamanli: int = 1  # aynı anda uçuşta en çok N istek (1 = sıralı)


DEFAULT_LIMITS = {
    "arxiv": SourceLimits(min_interval_s=3.1),
    "crossref": SourceLimits(min_interval_s=0.6),
    "dblp": SourceLimits(min_interval_s=1.0, max_retries=2, backoff_s=(15.0, 45.0)),
    "openalex": SourceLimits(min_interval_s=0.3),
    "s2": SourceLimits(min_interval_s=1.2, max_retries=2, backoff_s=(10.0, 30.0)),
    "oc_index": SourceLimits(min_interval_s=0.5, max_retries=3, backoff_s=(10.0, 30.0, 60.0), es_zamanli=3),
    "oc_meta": SourceLimits(min_interval_s=0.5, max_retries=3, backoff_s=(10.0, 30.0, 60.0), es_zamanli=3),
}


@dataclass
class Config:
    # modeller
    sef_model: str = "opus"
    isci_model: str = "haiku"
    claude_cli_path: str = ""
    llm_timeout_s: float = 900.0
    llm_max_retries: int = 1
    # dizinler
    data_dir: Path = ROOT / "data"
    log_dir: Path = ROOT / "logs"
    # kaynaklar
    sources: tuple[str, ...] = ("arxiv", "crossref", "dblp", "openalex", "web", "atif")
    openalex_api_key: str = ""
    s2_api_key: str = ""  # Semantic Scholar (ücretsiz başvuru); yoksa anahtarsız paylaşımlı havuz
    openalex_mailto: str = ""
    crossref_mailto: str = ""
    openalex_nokey_daily_budget: int = 80  # anahtarsız günlük istek (IP paylaşımlı)
    openalex_nokey_per_run: int = 12
    # arXiv kademeleri
    arxiv_and_max: int = 100
    arxiv_majority_max: int = 100
    arxiv_or_max: int = 200
    arxiv_enough: int = 30  # bir kademe bu kadar toplam verirse sonraki kademeye geçilmez
    crossref_rows: int = 100
    dblp_limit: int = 200
    openalex_per_page: int = 100
    max_queries_per_subq: int = 5
    dblp_queries_per_subq: int = 1
    # web işçileri
    web_workers: int = 3
    web_max_budget_usd: float = 0.10
    # atıf takibi
    snowball_seeds: int = 8
    snowball_refs_max: int = 400  # tüm tohumlar toplamı (ortak atıf sayısına göre)
    snowball_cites_max: int = 300
    # okuyucu
    reader_max: int = 1200
    reader_batch: int = 30
    reader_parallel: int = 8
    abstract_words_reader: int = 140
    # Özetsiz adaylar için anahtarsız arXiv önbaskı yedeği: okuyucuya gidecek özetsiz kayıtlardan
    # ön sıralamada en üstteki bu kadarı başlıkla aranır (arXiv 3.1 sn aralığı; 6 başlık/istek).
    # 0 = kapalı. Eşleşme: başlık benzerliği >= 0.90 ve çakışma yok.
    arxiv_ozet_k: int = 150
    # damıtıcı
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_cache: str = r"C:\Users\LENOVO\Projeler\akademik-bosluk\gapmine\data\hf_cache"
    embed_backend: str = "auto"  # auto | minilm | tfidf
    embed_words: int = 170  # MiniLM 256 token sınırına sığsın; aşan sayılır
    chef_cards: int = 80
    cluster_cap_frac: float = 0.35
    final_n: int = 30
    ozet_token_cap: int = 4000
    http_timeout_s: float = 60.0
    limits: dict[str, SourceLimits] = field(default_factory=lambda: dict(DEFAULT_LIMITS))

    def limits_for(self, source: str) -> SourceLimits:
        return self.limits.get(source, SourceLimits())

    @property
    def cost_log(self) -> Path:
        return self.log_dir / "maliyet.jsonl"


def load_config(path: str | Path | None = None, **overrides) -> Config:
    cfg = Config()
    p = Path(path) if path else ROOT / "orkestra.toml"
    if p.exists():
        with open(p, "rb") as f:
            data = tomllib.load(f)
        names = {f.name for f in fields(Config)}
        for k, v in data.items():
            if k in names and k != "limits":
                cur = getattr(cfg, k)
                if isinstance(cur, Path):
                    v = Path(v)
                elif isinstance(cur, tuple):
                    v = tuple(v)
                setattr(cfg, k, v)
    if os.environ.get("OPENALEX_API_KEY"):
        cfg.openalex_api_key = os.environ["OPENALEX_API_KEY"]
    if os.environ.get("S2_API_KEY"):
        cfg.s2_api_key = os.environ["S2_API_KEY"]
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg
