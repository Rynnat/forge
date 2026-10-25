import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orkestra.config import Config  # noqa: E402
from orkestra.records import new_record  # noqa: E402


@pytest.fixture
def cfg(tmp_path):
    return Config(data_dir=tmp_path / "data", log_dir=tmp_path / "logs", embed_backend="tfidf",
                  reader_batch=10, reader_parallel=2, chef_cards=20, final_n=8, snowball_seeds=2,
                  web_workers=1, arxiv_ozet_k=0,  # arxiv_ozet_k=0: testler ağsız
                  arxiv_yerel_db=tmp_path / "yerel_yok.sqlite")  # gerçek yerel dizine dokunulmaz


def rec(title, src="arxiv", **kw):
    return new_record(src, title=title, **kw)


ITEM_RE = re.compile(r'<item id="(\d+)">(.*?)</item>', re.S)


def mock_responder(prompt: str, stage: str) -> str:
    if stage == "sef_plan":
        return json.dumps({
            "alt_sorular": [
                {"id": "S1", "soru": "graph neural networks for molecules", "sorgular": ["graph neural molecule", "message passing chemistry"], "yeterli": "x"},
                {"id": "S2", "soru": "molecular property benchmarks", "sorgular": ["molecular benchmark dataset"], "yeterli": "y"},
            ],
            "capa_calismalar": [{"baslik": "Neural Message Passing for Quantum Chemistry", "yil": 2017}],
            "web_odaklari": ["awesome molecular gnn"],
        })
    if stage == "okuyucu":
        out = []
        for i, text in ITEM_RE.findall(prompt):
            if "cooking" in text.lower():
                out.append({"id": i, "rel": 0, "kesin": True, "alt": [], "alinti": "", "not": "off"})
            elif "maybe" in text.lower():
                out.append({"id": i, "rel": 0, "kesin": False, "alt": [], "alinti": "", "not": "unsure"})
            else:
                sent = text.split(". ", 1)[-1][:120]
                out.append({"id": i, "rel": 2, "kesin": False, "alt": ["S1"], "alinti": sent, "not": "relevant"})
        return json.dumps({"items": out})
    if stage == "sef_final":
        n = len(re.findall(r"^#\d+ \|", prompt, re.M))
        k = int(re.search(r"exactly (\d+) items", prompt).group(1))
        return json.dumps({"secim": [{"kart": i + 1, "gerekce": f"card {i + 1} matters"} for i in range(min(k, n))]})
    return "{}"
