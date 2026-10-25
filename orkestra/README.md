# orkestra v0

Forge'un şef–çalgıcı hattı. Girdi: araştırma sorusu + kesim tarihi. Çıktı: kesimden önce
yayımlanmış, önem sırasına göre 30 çalışma (arXiv id / DOI, başlık, yıl), her biri için 1 cümlelik
gerekçe + kodla doğrulanmış alıntı, ve şefe dönen ≤ 4000 token'lık özet (`ozet.md`).

Ön kayıt: `../ONKAYIT-orkestra-v0.md` (bu kod ondan SONRA yazıldı; dosyaya dokunulmadı).
Altın sete (`forge-altin/`) erişilmedi; hiçbir kural ona göre ayarlanmadı.

## Kullanım
```
cd forge/orkestra
python -m orkestra run   --soru "<...>" --kesim YYYY-MM-DD --out <dir>
python -m orkestra batch --sorular sorular.json --out <dir> [--k 3]
```
`sorular.json`: `[{"id": ..., "soru": ..., "kesim": "YYYY-MM-DD"}]`. Batch, her (soru, k) için
`<out>/<id>/k<k>/` yazar ve `batch_ozet.json`'da durum / maliyet / süre tutar.

Python: MiniLM embedding için `sentence-transformers` gerekir. Bu makinede gapmine'ın venv'i
kullanıldı: `..\..\akademik-bosluk\gapmine\.venv\Scripts\python -m orkestra ...` (model önbelleği
`gapmine/data/hf_cache`). Paket yoksa TF-IDF+SVD yedeğine düşer ve bunu funnel'a yazar
(`embed.backend=tfidf_svd(yedek)`). Diğer bağımlılıklar: `requests numpy scikit-learn`, `claude` CLI.

Yapılandırma (isteğe bağlı) `orkestra.toml`: `sef_model`, `isci_model`, `openalex_api_key`,
`reader_max`, `chef_cards` vb. (bkz. `orkestra/config.py`). `OPENALEX_API_KEY` ortam değişkeni de okunur.

## Akış
| # | aşama | kim | ne yapar |
|---|---|---|---|
| 1 | şef plan | `claude -p --model opus` | 4–8 alt soru, her biri için 4–6 terminoloji varyantlı sorgu + "yeterli" ölçütü; ≤25 çapa çalışma adı; web odakları. Şefe giden: yalnız soru + kesim |
| 2 | toplayıcılar (paralel) | kod + Haiku | arXiv (kademeli AND → çoğunluk → OR, alt çizgi korunur, `submittedDate` sorguda), Crossref (`until-pub-date`), DBLP (SPARQL), OpenAlex (anahtar / bütçe), Haiku web işçileri (yalnız WebSearch/WebFetch, $0.10 tavan), şef çapaları. Web ve çapa adları arXiv/Crossref'te **gerçek kayda çözülmeden** havuza girmez |
| 3 | tekilleştirme + kesim | kod | arXiv id / DOI / normalize başlık (≥0.90 karakter + ≥0.75 kelime benzerliği; sayı/roma rakamı farkı birleştirmez); preprint–yayın birleşir, tüm tarihler tutulur. **Kesim:** sürümlerden biri kesin önceyse geçer; karar verilemiyorsa (`tarih_belirsiz`) düşer |
| 4 | atıf takibi | kod | ön sıralamada en yakın 8 tohum + ≤4 çapa → OpenCitations referansları ve atıf yapanları (atıf yapanın `creation` tarihi kesimden önce olmalı). Birden çok tohuma bağlı olan önce (ortak atıf); sonra yeniden tekilleştirme + kesim |
| 5 | okuyucular | `claude -p --model haiku` ×4 paralel | 30'luk partilerle başlık + özet → rel 0–3, alt soru, alıntı. **Yalnız `rel=0 ∧ kesin`** atılır; cevapsız/bozuk/şüpheli yukarı çıkar. Alıntı `quotecheck` ile kodla doğrulanır, tutmayan silinir |
| 6 | damıtıcı | kod | BM25 + embedding (RRF) + okuyucu puanı + log atıf + tohum yakınlığı + çapa + kaynak çeşitliliği; KMeans kümeleri, tek kümeden ≤%35; ilk 80 kart |
| 7 | şef final | opus | yalnız 80 kompakt kartı görür (~6–8k token), 30'u sıralar, karta dayalı 1 cümle gerekçe. Geçersiz kart no sayılır; eksik kalırsa damıtıcı sırasıyla doldurulur ve işaretlenir |

Çıktılar (`--out`): `sonuc.json` (30 çalışma + plan + maliyet + süre), `ozet.md` (şefe dönen,
temkinli token tahmini `ceil(karakter/3)` ≤ 4000; aşarsa alıntı/gerekçe kısaltılır),
`funnel.json`, `kartlar.json` (şefin gördüğü 80 kart), `dusenler_on_siralama.jsonl` (okuyucuya
hiç gitmeyen adaylar, adıyla).

## Dürüst durum
- Her aşama `giren = çıkan + Σ düşen(sebep)`; tutmazsa `UNACCOUNTED` yazılır ve `funnel_dengeli=false`.
- Kaynak durumu: `OK` / `EKSİK` / `KAPALI`. EKSİK yapışkandır; bir kaynak EKSİK ise koşu `EKSİK`.
- Retry-After'sız geçici 429 kota sayılmaz: 10→30→60→120 s beklenir; ancak tükenirse ya da
  Retry-After > 300 s ise kaynak EKSİK olur. QLever'ın "timed out" 429'u kota değil, sorgu hatasıdır.
- Bot doğrulama sayfası (Anubis) `BotBlocked` → EKSİK; aşılmaya çalışılmaz.
- OpenAlex anahtarsız: koşu başına 12, günde 80 istek (kalıcı sayaç `data/openalex_butce.json`); dolunca EKSİK.
- API'nin döndürmediği (kesilen) sonuç sayısı, AND=0 kademeleri, MiniLM'e sığmayan metin sayısı,
  okuyucu cevapsızları, reddedilen alıntılar `bilgi` sayaçlarında.

## gapmine DENETİM derslerine karşılık
| ders | orkestra |
|---|---|
| alt çizgi silme (`io_uring` → `io AND uring`) | terim düzenli ifadesi `_` korur; birim + canlı test |
| AND→OR ikilemi, OR'da 50 kesimi | AND → çoğunluk (⌈0.6n⌉ terim) → OR(200); kademe ve kesilen sayaçları |
| top-N kesimi (ilk 60) | okuyucuya 1200 aday; şefe 80 kart; okuyucu yalnız kesin alakasızı atar; kesilenler adıyla dosyada |
| MiniLM 256 token sessiz kesim | metin başlık + ilk 170 kelime; kesilen sayılır; BM25 tam metni görür |
| kota → EKSİK, geçici 429 | yukarıda |
| kaynak çeşitliliği | 6 kaynak + Haiku web işçileri (blog / awesome-list) |
| atıf takibi OpenAlex kotasına bağlı | OpenCitations (anahtarsız) |
| rapor üzerine yazma | her koşu kendi `--out` dizini; maliyet logu ekleme (append) |

## Maliyet logu
Her LLM çağrısı `logs/maliyet.jsonl`'a bir satır yazar (`llm` bloğu: backend, calls, ok, failed,
token'lar, `cost_usd` = CLI'nin `total_cost_usd`'u, liste fiyatı, teorik). maliyet-sayaci:
`python ..\araclar\maliyet-sayaci\maliyet_sayaci.py tools` bunu `orkestra` adıyla toplar.

## Testler
- `python -m pytest` — ağsız, fixture + sahte LLM: funnel muhasebesi, EKSİK bayrağı (kota/bütçe/şef
  hatası), kesim filtresi (ay/gün/yıl belirsizliği, sürüm kuralı), tekilleştirme + preprint–yayın
  birleştirme, alıntı doğrulama, uydurma başlık reddi, arXiv kademeleri, 429 politikası, özet tavanı.
- `python -m pytest -m live` — her kaynağa 1 küçük gerçek sorgu (kota/bot durumunda sebebiyle `skip`).

## Duman testi
(aşağıda)
