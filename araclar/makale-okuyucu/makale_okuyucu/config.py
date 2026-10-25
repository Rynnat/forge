"""Yapılandırma. Tüm yazma yolları proje klasörünün içindedir."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"

FIELDS = [
    "problem", "katkilar", "yontem", "veri_setleri_ve_kaynaklar", "deney_kurulumu",
    "ana_sonuclar", "sinirliliklar", "gelecek_calisma", "kapsam_disi", "en_yakin_isler",
]

# alan başına kartta tutulacak en fazla madde
FIELD_CAPS = {
    "problem": 2, "katkilar": 5, "yontem": 4, "veri_setleri_ve_kaynaklar": 6,
    "deney_kurulumu": 4, "ana_sonuclar": 6, "sinirliliklar": 5, "gelecek_calisma": 3,
    "kapsam_disi": 5, "en_yakin_isler": 8,
}


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: PROJECT_DIR / "data")
    llm_backend: str = "claude_cli"  # claude_cli | anthropic_api | mock
    llm_model: str = "haiku"
    api_model: str = "claude-haiku-5-5"
    llm_timeout_s: float = 240.0
    llm_max_retries: int = 2
    claude_cli_path: str = ""
    llm_workers: int = 4
    chunk_chars: int = 12000
    passage_chars: int = 1500
    ask_top_k: int = 6
    md_max_tokens: int = 1500
    http_timeout_s: float = 60.0
    user_agent: str = "makale-okuyucu/0.1 (research tool; +local)"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "cache.db"

    @property
    def papers_dir(self) -> Path:
        return self.data_dir / "papers"

    @classmethod
    def from_env(cls, **over) -> "Config":
        cfg = cls(**over)
        if os.environ.get("MAKALE_LLM") and "llm_backend" not in over:
            cfg.llm_backend = os.environ["MAKALE_LLM"]
        return cfg


def pin_caches(data_dir: Path) -> None:
    """Olası kütüphane önbelleklerini proje içine yönlendir."""
    cache = Path(data_dir) / "hf_cache"
    for var in ("HF_HOME", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME", "TORCH_HOME", "XDG_CACHE_HOME"):
        os.environ.setdefault(var, str(cache))
    os.environ.setdefault("PIP_CACHE_DIR", str(Path(data_dir) / "pip_cache"))
