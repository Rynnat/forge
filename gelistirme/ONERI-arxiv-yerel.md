# Öneri: Yerel arXiv dizini (orkestra v1 adayı) — 2026-10-25

Durum: **tasarım**. Orkestra v0 deneyi koşarken yazıldı; v0 koduna dokunmaz. İndirme B koşuları bitince yapılır
(indirme de ağı meşgul eder).

## Neden
- v0'da arXiv canlı API'si en kırılgan kaynak:
  - D1: arXiv 429 → EKSİK, 424 kayıt.
  - D2 tek başına: 4029 kayıt.
  - D2 başka işlerle aynı anda: 790 kayıt.
- Toplama aşamasının en uzunu arXiv: 3,1 s aralık + 429 geri çekilmeleri, 272–357 s.
- Üçüncü taraf bir kaynak, arXiv'in hız sınırlarını **2026-10-01'de sıkılaştırdığını** söylüyor (doğrulanmadı; resmi duyuru
  blog.arxiv.org'da aranmalı). Doğruysa canlı API'ye dayanmak daha da riskli.
- IP değiştirerek sınırı atlatmak **yapılmaz** (arXiv kuralları; kalıcı engel riski). Meşru yol: arXiv'in kendi yayımladığı toplu meta veri.

## Veri
- **Birincil: HuggingFace `librarian-bots/arxiv-metadata-snapshot`**
  - 3,22 M kayıt; ~9 parquet parça (ilki ~296 MB → toplam ~2,5 GB tahmini).
  - CC0.
  - Alanlar: id, title, abstract, authors, categories, doi, journal-ref, **versions (tarihli)**, update_date.
  - Görülen en yeni `update_date`: 2026-10-16.
  - Güncelleme sıklığı sayfada yazmıyor; ölçülecek.
- **Yedek:** Kaggle `Cornell-University/arxiv`, `arxiv-metadata-oai-snapshot.json`. Aynı içerik, CC0, hesap ister → kullanıcıya iş çıkarır, ikinci tercih.
- **Güncel tutma:**
  - arXiv **OAI-PMH**, artımlı (yalnız son anlık görüntüden sonraki günler).
  - arXiv'in toplu meta veri için önerdiği kanal bu; sık yoklama yapılmaz, günde en çok 1 kez.

## Tasarım
- **Depo:** `forge/orkestra/data/arxiv_yerel.sqlite`, **SQLite FTS5**. Python'da yerleşik, ek bağımlılık yok; BM25 sıralaması içinde.
  - Tablo `kayit(id, baslik, ozet, kategoriler, doi, v1_tarih, surumler_json)`.
  - FTS5 sanal tablosu `(baslik, ozet)`, `porter` + `unicode61` tokenizer'ı.
  - `v1_tarih` dizinli → kesim süzgeci sorguda: `v1_tarih < :kesim`.
- **Kaynak arayüzü:** `sources/arxiv_yerel.py`, canlı `arxiv.py` ile **aynı imza ve aynı kademeler**:
  - Kademeler: AND → çoğunluk (⌈0,6n⌉) → OR, sayaçları aynı adlarla.
  - Böylece funnel ve testler aynen geçerli kalır.
  - Alt çizgi koruma (`io_uring`) FTS5'te tırnaklı ifadeyle.
- **Kullanım kuralı:**
  - Yerel dizin varsa arXiv araması yereldir.
  - Canlı API yalnız iki iş için çağrılır:
    - anlık görüntü tarihinden sonraki kayıtlar,
    - verilen id listesiyle `by_ids` (web/şef çapaları).
  - Bu ikisi birkaç istek tutar.
- **Bonus — özet yedeği:** DOI'li kayıtların arXiv ön baskısı başlıkla yerelde bulunur.
  - Bugünkü `preprint_abstracts` 150 tavanla ve arXiv'e istek atarak çalışıyor; yerelde tavansız ve bedava olur.
  - OZET_YOK sorununun arXiv tarafı tamamen kapanır. IEEE/ACM'in arXiv'de olmayan kısmı kalır.
- **Dürüst durum:**
  - `arxiv_yerel` kaynak satırı: anlık görüntü tarihi + kayıt sayısı.
  - Kesim tarihi anlık görüntüden sonraysa → **EKSİK** ("dizin kesimi kapsamıyor").

## Beklenen kazanç (tahmin, ölçülecek)
- arXiv toplama: ~300 s → < 10 s. 429 ve EKSİK riski ortadan kalkar.
- Toplam koşu: ~750 s → ~450 s. Darboğaz okuyucuya (~200 s) ve atıf takibine (~110 s) kayar.
- Maliyet değişmez: LLM çağrıları aynı.

## Kabul (bu öneri için ön kayıt taslağı — kod yazmadan önce ayrı dosyada commit edilir)
1. **Eşdeğerlik (ağsız):** `data/http_cache.sqlite`'taki D1/D2 canlı arXiv yanıtları (aynı sorgular) yerel dizinle tekrarlanır.
   - **Ölçüt:** canlı ilk-N sonuçların yerelde de bulunma oranı ≥ %90 (aynı kesimle).
   - Sıra birebir beklenmez: arXiv'in sıralaması farklı.
2. **Uçtan uca:** n ≥ 10 soru, v0 ile v1 eşli.
   - recall@30 farkı ≥ −2 puan (kalite kaybı yok).
   - arXiv EKSİK oranı 0.
   - Süre ≤ %70.
   - Altın set olarak v0 deneyinde **kullanılmamış** yeni survey'ler kullanılır; v0 altını artık görülmüş sayılır.
3. **Boyut / iş:** dizin ≤ 8 GB; ilk kurulum ≤ 30 dk; günlük OAI-PMH güncellemesi ≤ 5 dk.

## Riskler
- **HF anlık görüntüsü bayatlayabilir.** Güncelleme sıklığı bilinmiyor; OAI-PMH artımı bunu kapatır, ama OAI-PMH de hız sınırlıdır (yavaş, gece).
- **Kesim kuralı:** `versions[0]` = v1 gönderim tarihi; canlı API'deki `published` alanıyla aynı mı? Eşdeğerlik testinde ayrıca kontrol edilir.
- **Disk:** ~2,5 GB parquet + ~4–5 GB FTS dizini (tahmin). Parquet, dizin kurulunca silinebilir.
- **Deney bütünlüğü:** v1'in v0 altınıyla ayarlanması yasak. Yukarıdaki 2. madde bu yüzden yeni altın istiyor.

## Kaynaklar
- https://huggingface.co/datasets/librarian-bots/arxiv-metadata-snapshot
- https://www.kunalganglani.com/blog/arxiv-rate-limit-policy (üçüncü taraf; 2026-10-01 sıkılaştırma iddiası)
- https://info.arxiv.org/help/bulk_data.html , https://info.arxiv.org/help/api/user-manual.html
- https://library.hkust.edu.hk/sc/arxiv-corpus (Kaggle yayını, 2020)
