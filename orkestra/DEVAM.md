# DEVAM — orkestra v0 (WIP, 2026-10-25)

Kullanıcının bilgisayarı yeniden başlatılacağı için iş yarıda kesildi. Mimari ve kullanım için README.md'ye bakın.

## Biten işler
- Paket `orkestra/`:
  - config, http (önbellek + 429 politikası + bot duvarı)
  - funnel, records (tarih + kesim + tekilleştirme)
  - kaynaklar: arxiv (kademeli), crossref, dblp (SPARQL), openalex (bütçe), s2 (zenginleştirme), opencitations (atıf takibi)
  - web (Haiku işçileri + başlık çözümleme), reader (Haiku okuyucu), rank (BM25 + MiniLM/TF-IDF, kümeleme)
  - chef (opus plan + final), pipeline, report, cli (`run` / `batch`)
- maliyet-sayaci `tools` modu artık `forge/orkestra/logs/maliyet*.jsonl` dosyasını da okuyor (araclar/maliyet-sayaci, testi eklendi). Bu değişiklik bu WIP commit'ine **dahil değil**, yerelde duruyor.
- Testler:
  - `python -m pytest`: **40 geçti**. Ağ kullanmaz; fixture'lar ve sahte LLM ile koşar.
  - `python -m pytest -m live`: 7 canlı test. Son koşuda arXiv, Crossref, DBLP, OpenCitations ve claude-haiku geçti. OpenAlex ve S2 kota yüzünden `skip` etti.

## Duman testi (kosu1, `duman/kosu1/`)
**D1 "GNN for molecular property prediction", kesim 2025-06-01:**
- **Sonuç:** 30 çalışma üretildi. 26'sında doğrulanmış alıntı var.
- **Durum: EKSİK.** OpenAlex anahtarsız kotası bitti. arXiv bir noktadan sonra 429 verdi. S2 429 verdi.
- **Maliyet:** **$0.593** (hedef < $0.65).
- **Süre:** **1441 s (~24 dk).**
- **Özet:** ~3982 token (tahmin). Funnel dengeli.
- **Funnel:**
  - Crossref 4000 → 3532
  - arXiv 424
  - DBLP 3
  - web 69 → 29 çözüldü
  - şef çapaları 25 → 23
  - Tekilleştirme 4011 → 3185, kesimden sonra 2976
  - Atıf takibi +430 aday
  - Okuyucuya 1200 aday gitti, 970'i kaldı
  - Şefe 80 kart, şeften 30 çalışma
- **Maliyet kalemleri:**
  - Plan: $0.065
  - Web işçileri: $0.18
  - Okuyucu: 40 çağrı × ~$0.005 = ~$0.21
  - Final: $0.136

**D2 "network protocol fuzzing":** Koşu, toplama aşamasında kullanıcı isteğiyle durduruldu; sonuç yok. Kısmi LLM maliyeti (plan + 3 web işçisi, ~$0.22) `logs/maliyet.jsonl` dosyasında.

## 2026-10-25 (ikinci oturum)
- D2 koşuldu: `duman/kosu2/`, $0.56, 1148 s, EKSİK (openalex, s2). Sonuçlar README "Duman testi"nde.
- Hız (`9d51ba6`): tekilleştirme 33× (çıktı aynı), OpenCitations eşzamanlı 3, atıf tohumları paralel,
  okuyucu 8 paralel. Etkisi henüz bir koşuda ölçülmedi.
- Altın setin kalan 15'i ayrı bir ajana verildi (bu oturum forge-altin'i okumadı).
- D2 alıntı 17/30 kök nedeni: eksik 13'ün 13'ü `OZET_YOK`, hepsi yalnız-DOI (IEEE/ACM/Springer/NDSS).
  Crossref bu yayıncıların özetini taşımıyor; S2 zenginleştirmesi 429. Okuyucu bunları yalnız başlıktan
  yargıladı. Çözüm: S2 ve OpenAlex anahtarı. `s2_api_key` / `S2_API_KEY` desteği eklendi (42 test).

- Sadakat denetçisi (`deney/sadakat.py`, Sonnet + web): pilot n=10 → 10/10 destekli, 0 uydurma, $0.29.
  Elle bakıldı: kanıtlar gerçek. **Zayıflık:** bazı gerekçeler başlığı tekrar ediyor (ör. "TLS kütüphanelerine
  fuzzing uygular") → tautolojik destek; "foundational / landmark" gibi etki ifadeleri denetlenmiyor.
  Asıl ölçümde denetçi raporu bu iki sınıfı ayrıca saymalı (eşik değişmez; betimsel not).

- Hız ölçümü (kosu3, D2, yeni kod): 1148 → 752 s; atıf 213 → 112, okuyucu 448 → 199, tekil+kesim 66 → 42.
  **Karşılaştırma temiz değil:** kosu3'te arXiv 429 ile EKSİK (790 kayıt; kosu2'de 4029). Sebep büyük olasılıkla aynı IP'den
  eşzamanlı arXiv kullanan diğer işler (sadakat pilotu, özet yedeği ajanı). **Gerçek deneyde B koşuları tek başına,
  aynı makinede arXiv'e giden başka iş yokken koşulmalı**; yoksa arXiv EKSİK olur ve B haksız zayıf ölçülür.
- Altın set tamam (30/30, 4089 kaynak); hash ONKAYIT'ta (`b3c1fd7`).

## Kalan işler (ilk oturumdan; 1, 2, 5 bitti)
1. D2'yi baştan koş: `python -m orkestra batch --sorular duman/sorular.json --out duman/kosu2`. Ya da yalnız D2'yi `run` ile koş.
2. Duman sonuçlarını (maliyet, süre, funnel) README'nin "Duman testi" bölümüne yaz.
3. Hız. Süre 24 dk, darboğazlar şunlar:
   - arXiv: 3 s aralık, çok sayıda sorgu.
   - DBLP: SPARQL sorgusu başına ~20 s.
   - Crossref: 40 sorgu × 100 satır.
   - Tekilleştirme: 100 s, bulanık blok döngüsü Python'da.
   - Atıf takibi: 263 s.
4. Maliyet sınırda ($0.59). Okuyucu partisi büyütülebilir (30 → 50), ya da web işçi sayısı azaltılabilir.
5. Final commit: WIP yerine gerçek mesaj. maliyet-sayaci değişikliği de commit edilecek.

## Bilinen hatalar / zayıflıklar
- **Crossref gürültüsü:** 4000 kaydın 362'si peer-review türünde (eleniyor), geri kalanı da çok gürültülü. Crossref, havuzu şişiriyor ve okuyucu kesimine (1200) baskı yapıyor.
- **Kesimde düşen kayıtlar:** `tarih_belirsiz` 206 kayıt düştü. Bunlar yılı kesim yılına eşit, ayı bilinmeyen kayıtlar. S2 zenginleştirmesi 429 verdiği için tarihleri tamamlanamadı.
- **DBLP:** yalnız 3 kayıt verdi. Tüm terimler başlıkta aranıyor, çoğunluk kademesi zaman aşımına düşüyor. REST API'si bot duvarının (Anubis) arkasında.
- **arXiv 429:** arXiv 5 denemeden sonra EKSİK oldu (424 kayıt geldi). Aralık 3.1 s'den büyütülmeli ya da sorgu sayısı azaltılmalı.
- **Anahtarsız kaynaklar:** OpenAlex ve S2 anahtarsız pratikte kullanılamıyor; anahtar alınmalı (`orkestra.toml` → `openalex_api_key`).
- **Atıf takibi:** OpenCitations'ta arXiv-only tohumların referansı yok. Atıf yapanlar önem sırasına göre gelmiyor; seçim yalnız ortak atıf sayısına dayanıyor.
- **Web işçileri:** başlıkların %55'i çözülemedi (38/69). Bunlar uydurma ya da arXiv/Crossref'te başlık eşleşmesi tutmayan başlıklar.
- **Özet token sayısı:** tahminidir: `ceil(karakter / 3)`. Gerçek tokenizer kullanılmadı.

## Linux'ta yeniden kurulum
- **Python 3.11+** (tomllib).
- **Paketler:**
  - `pip install requests numpy scikit-learn pytest`
  - MiniLM için: `pip install torch --index-url https://download.pytorch.org/whl/cpu` ve ardından `pip install sentence-transformers`
- **`claude` CLI** PATH'te olmalı ve oturum açık olmalı.
- **Windows'a özgü yollar (değiştirilmeli):**
  - `orkestra/config.py` → `hf_cache` = `C:\Users\LENOVO\Projeler\akademik-bosluk\gapmine\data\hf_cache`. Linux'ta `orkestra.toml` içinde `hf_cache = "<yol>"` verin ya da boş bırakın; model HF Hub'dan iner.
  - `araclar/maliyet-sayaci/maliyet_sayaci.py` → `GAPMINE_RAPORLAR` (Windows yolu).
  - Duman testi gapmine'ın `.venv\Scripts\python` yorumlayıcısıyla koşuldu. Linux'ta kendi venv'inizi kurun.
- **Kopyalanmayan dizinler:** `data/` (HTTP önbelleği sqlite + OpenAlex bütçe sayacı) gitignore'da, yeniden oluşur.

## DENEY KOŞUSU (2026-10-25 gece başladı)
- Kod donduruldu: etiket `orkestra-v0-donmus` (commit bc0f62b). orkestra/ ve deney/ kodu artık DEĞİŞMEZ.
- Kullanıcı "başla" dedi (aşamalı: önce B). Anahtarsız koşuluyor (OpenAlex/S2 yok, arXiv önbaskı yedeği açık) — raporda yazılacak.
- B: `python -m orkestra batch --sorular ../../forge-altin/sorular.json --out deney-sonuc/B` (log: deney-sonuc/B.log).
  Yarıda kalırsa: tamamlanan soru dizinlerini atlayarak aynı komutla devam (önce batch'in atlama yapıp yapmadığını kontrol et).
- Sonra sırayla (aynı anda arXiv'e giden iş YOK): A1 (`python -m deney.taban batch --mod a1 --sorular ../../forge-altin/sorular.json --out deney-sonuc/A1 --tavan 3`),
  A0 (`--mod a0 --out deney-sonuc/A0`), B kararlılık (rastgele 10 soru k=3), sadakat (n=30), puanlama (`orkestra.deney.puanla esli`).
- Ara durdurma kuralı: ilk 10 soruda ortalama(B − A1) ≤ −10 puan → RED, kalan koşulmaz (tek bakış).
- Bu oturum `forge-altin/altin.json`'u yalnız puanlayıcı üzerinden okur; içeriğini bağlama dökmez.
- **Bilinen sınırlama:** altın set ajanı araştırma sorularını Türkçe yazdı (talimat "dosyalara Türkçe yaz" idi; ON KAYIT örneği de Türkçe).
  İki sistem aynı soruyu alıyor. B'de etkisi: şef planı İngilizce; Türkçe soru, sıralamanın 6–9 sorgu metninden yalnız biri.
  Durdurulmadı; raporda yazılacak. q01: $0.652, 1151 s.
- v1 adayı tasarım: `gelistirme/ONERI-arxiv-yerel.md` (yerel arXiv FTS5 dizini; indirme B bitince).

## DURDURULDU (2026-10-25 ~19:15, kullanıcı isteği)
- Kullanıcı tüm çalışan görevleri durdurttu; sebep: Forge'un yönü sorgulanıyor (literatür hattına daralma, gerçek kullanım 0).
- Durdurulduğunda: B 4/30 soru bitmiş (deney-sonuc/B), A0 deney-sonuc/A0 (bkz. sayı), v1 ajanı yarıda
  (forge-v1 worktree'de commit'siz dosyalar; forge-veri/arxiv_yerel.sqlite ~5,2 GB, kurulum bitmemiş olabilir).
- Deney yarıda: n < 30 → ON KAYIT'a göre karar yok. Devam edilirse B aynı komutla, bitmiş soruları atlayarak sürdürülmeli
  (batch'in atlama yapıp yapmadığını önce kontrol et). Kod etiketi orkestra-v0-donmus değişmedi.
- Sıradaki önerilen iş (kullanıcı onayı bekliyor): "diğer" %79'luk kullanımı projelere bölmek (maliyet-sayaci), sıradaki çalgıcıyı ona göre seçmek.
