# makale-okuyucu (v0.1.0)

Makaleyi **bir kez** okur, alıntıyla kanıtlı küçük bir **kart** üretir ve önbelleğe koyar. Sonraki sorular
önce karttan, gerekirse yalnız ilgili pasajlardan cevaplanır. Tasarım: [`SPEC.md`](SPEC.md).
Durum: **Forge kabul protokolü bekliyor** (taban çizgisi + eşik + bağımsız ölçüm henüz yapılmadı).

| katman | iş | modül |
|---|---|---|
| kod | girdi çözümleme, indirme, durum sınıflama | `fetch.py` |
| kod | PDF → sayfa metni, bölümleme (metin + yazı biçimi sezgisi), parçalama, pasajlar | `pdftext.py` |
| Haiku | parça başına alan çıkarımı (alıntılı), id seçen birleştirme | `extract.py` |
| kod | alıntı doğrulama + sayfa bulma (gapmine'dan kopya + `locate_page`) | `quotecheck.py` |
| kod | Markdown bütçesi (≤ 1500 token) | `render.py` |
| Haiku + kod | `ask`: kart → BM25 pasajları → cevap | `core.py` |
| kod | SQLite + JSON önbellek, maliyet/funnel logu | `store.py` |
| — | LLM arka uçları (gapmine/llm.py'den kopya) | `llm.py`, `mockllm.py` |

## Kurulum (Windows, Python 3.12, GPU yok)

```powershell
cd C:\Users\LENOVO\Projeler\forge\araclar\makale-okuyucu
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --no-cache-dir -r requirements.txt   # requests, pymupdf, pytest
```

`claude` CLI PATH'te olmalı (ek API anahtarı gerekmez). Embedding modeli yok (BM25 kodla yazıldı),
yani torch/HF indirmesi yok; yine de `HF_HOME` vb. `data/hf_cache`'e yönlendirilir.

## Komutlar

```powershell
$py = ".\.venv\Scripts\python"
& $py -m makale_okuyucu read 2501.08156             # arXiv id / DOI / PDF URL / yerel PDF
& $py -m makale_okuyucu read makale.pdf --as 10.1145/xxxx   # engellenen makale için yerel PDF
& $py -m makale_okuyucu read 2501.08156 --json      # kart JSON
& $py -m makale_okuyucu ask 2501.08156 "Hangi judge modeli kullanıldı?"
& $py -m makale_okuyucu card 2501.08156 [--json]    # yalnız önbellekten
& $py -m makale_okuyucu runs -n 10                  # maliyet / funnel logu
```

Genel bayraklar: `--llm claude_cli|anthropic_api|mock`, `--data-dir`, `-v`.

- `read` stdout'a kompakt Markdown, stderr'e tek satırlık `LOG:` (sayfa, parça, Haiku çağrısı, token,
  maliyet, süre, UNVERIFIED, başarısız parça, md token) basar.
- İndirme başarısızsa çıkış kodu **2**, her aday URL'nin sebebi ve `read <pdf> --as <anahtar>` önerisi basılır.
  Cloudflare → `BOT_BLOCKED`, 401/402/403 ya da ödeme sayfası → `PAYWALL`. **Atlatma denenmez**; her URL bir kez istenir.
- `ask` JSON döner: `kaynak` = `kart` | `bolum` | `bulunamadi` | `aranamadi`, `cevap`, `alintilar`
  (`quote`, `page`, `check`), `dogrulanmis`, `llm` (çağrı/token/maliyet), `gonderilen_karakter` (bölüm adımında).

Dosyalar: `data/cache.db` (tablolar `papers`, `aliases`, `runs`, `llm_calls`, `asks`) ve
`data/papers/<anahtar>/{paper.pdf, doc.json, card.json, card.md}`.

## Kart

Alanlar: `problem, katkilar, yontem, veri_setleri_ve_kaynaklar (name, link), deney_kurulumu, ana_sonuclar,
sinirliliklar, gelecek_calisma, kapsam_disi, en_yakin_isler (name, relation)`. Her madde:
`text` (kısa İngilizce iddia), `quote` (birebir), `page` (kodla bulunur, ör. `"7"` ya da `"4-5"`),
`check` (`VERIFIED` / `UNVERIFIED` + `neden`). Kart ayrıca `eksik_parcalar` (başarısız parça → bölüm + sayfa)
ve `funnel` taşır. Alan üst sınırları `config.FIELD_CAPS` (toplam en çok 48 madde).

Birleştirme adımında Haiku **yalnız id seçer**; metin yeniden yazdırılmaz, böylece alıntı–kanıt bağı
korunur. Bilinmeyen id ve aynı isimli iş/veri seti tekrarı atılır ve sayılır; LLM bir alanı boş bırakırsa
deterministik yedekten doldurulur.

## Testler

```powershell
.\.venv\Scripts\python -m pytest     # ağ ve gerçek LLM gerekmez; geçici dosyalar .pytest_tmp/
```

Son durum (2026-10-25): **67 test, hepsi yeşil** (~16 s).

| dosya | ne test ediliyor |
|---|---|
| `test_sections.py` (13) | kanonik ad eşleme, üretilmiş PDF'te bölüm + sayfa, numara +1 kuralı (tablo gürültüsü), Roma rakamı ve "3\nBaşlık" biçimi, alt bölüm sınır değil, satır içi Abstract, references sonrası harfli ek, içindekiler tablosu başlık sayılmaz, harf aralıklı figür metni, **yazı biçimi kapısı** (girişteki numaralı liste başlık sayılmaz), parçalar references'ı dışlar ve boyuta uyar, uzun bölüm bölünürken sayfa korunur, pasajlar |
| `test_quotecheck.py` (7) | boşluk/harf, kıvrık tırnak + ligatür, satır sonu tirelemesi, parafraz → UNVERIFIED, üç nokta sırası, çok kısa, sayfa bulma (tek sayfa ve sayfa sınırı aşan) |
| `test_fetch.py` (19) | arXiv/DOI/URL/yerel girdi çözümleme (9 biçim), tanınmayan girdi, durum sınıflama (OK, BOT_BLOCKED ×3, PAYWALL ×3, NOT_PDF, NOT_FOUND, HTTP_ERROR, NETWORK_ERROR), DOI→OpenAlex→arXiv önceliği, Cloudflare+ödeme duvarı zinciri (her URL bir kez), NO_OA, bilinmeyen DOI, ağ hatası, PDF olmayan yerel dosya |
| `test_llm.py` (6) | claude CLI bayrakları (`--tools ""`, `--setting-sources ""`, `--strict-mcp-config`, `--system-prompt`, `--no-session-persistence`), prompt stdin'den (60k karakter), boş cwd, tekrar denemeler, exe yok, JSON ayrıştırma, PARSE_FAIL / LLM_ERROR, kayıt geri çağrısı |
| `test_extract.py` (9) | doğrulama + sayfa (`"6"`, `"5-6"`), UNVERIFIED nedenleri, bozuk madde sayımı, şema hatası, küçük havuzda LLM'siz birleştirme, bilinmeyen id + üst sınır + boş alan yedeği, birleştirme hatasında yedek, aynı isimli işin tekilleştirilmesi, başarısız parçanın kayda geçmesi |
| `test_render.py` (3) | alıntı + UNVERIFIED etiketi, büyük kartta bütçe + "(+N madde JSON'da)", boş alan işareti |
| `test_e2e.py` (10) | mock LLM + sahte HTTP + üretilmiş PDF: doğrulanmış kart ve doğru sayfalar, references'ın LLM'e gitmemesi, ikinci okumada 0 HTTP / 0 LLM, aynı baytlı yerel PDF'in önbelleğe düşmesi, `--as`, BOT_BLOCKED'da yerel PDF isteği, başarısız parça → PARTIAL, boş metin, `ask` kart / bölüm / bulunamadı + ask önbelleği, ask'in tam metni göndermemesi, CLI |

## Duman testi (gerçek arXiv + gerçek Haiku, 2026-10-25)

`claude -p --model haiku`, 4 paralel çağrı, parça 12 000 karakter. Maliyet CLI'nin liste fiyatıyla
bildirdiği değer (abonelikte fatura değil, kota tüketimi).

| | arXiv 2501.08156 (R1 faithfulness) | arXiv 2001.08361 (Scaling Laws) |
|---|---|---|
| sayfa / karakter | 36 / 141 015 | 30 / 88 759 |
| references (LLM'e gitmedi) | p.11-15, 14 452 karakter | p.28-30, 10 107 karakter |
| parça / Haiku çağrısı | 12 / **13** (12 çıkarım + 1 birleştirme), 0 başarısız | 10 / **11**, 0 başarısız |
| token (önbellek-yazma + okuma / çıktı) | 59 162 + 8 553 / 50 954 | 50 956 / 65 489 |
| **maliyet** | **$0.037** | **$0.043** |
| **duvar saati** | **89.8 s** (LLM toplamı 229 s, paralel) | **117.7 s** (LLM 279 s) |
| ham madde → doğrulanmış | 104 → 103 (1 UNVERIFIED) | 131 → 130 (1 UNVERIFIED) |
| kartta madde / UNVERIFIED | 44 / 0 | 44 / 0 |
| kart boyu | card.md 4 790 karakter ≈ **1 369 token** (tahmin); card.json 17.9 KB | 4 702 karakter ≈ **1 344 token**; 17.7 KB |
| ikinci `read` | önbellekten, 0.3 s, 0 çağrı | aynı |

Çıktı token'larının çoğu Haiku'nun düşünme token'ları. `MAX_THINKING_TOKENS=0` tek parçada denendi:
ucuzlatmadı ($0.0024 → $0.0033, gürültü içinde), bu yüzden varsayılan bırakıldı.

`ask` örnekleri (önbellekteki kartla):

| soru | kaynak | Haiku | maliyet | süre |
|---|---|---|---|---|
| R1 ipucunu yüzde kaç dile getiriyor? (2501) | kart, "59%", p.1 VERIFIED | 1 | $0.0008 | 4.3 s |
| Hangi judge modeli, nasıl doğrulandı? (2501) | kart, GPT-4o, p.7/10/17/20 VERIFIED | 1 | $0.0009 | 5.2 s |
| Öğrenme oranı takvimi? (2001) | kart, 3000 adım warmup + cosine, p.7 | 1 | $0.0007 | 3.4 s |
| Tokenizer ve sözlük boyu? (2001) | **bolum**, BPE 50257, p.6 VERIFIED (8.7k karakter gönderildi) | 2 | $0.0022 | 12.0 s |
| Hangi donanımda eğitildi? (Türkçe soru, 2001) | bulunamadi (makale donanım vermiyor) | 2 | $0.0016 | 7.3 s |
| Protein katlama değerlendiriliyor mu? (2001) | bulunamadi | 2 | $0.0017 | 7.8 s |

Çıktılar: `data/smoke/*.md|.err.txt|ask_*.json`, kartlar `data/papers/arxiv_*/`.

## Bilinen zayıflıklar

- **Doğrulanmış alıntı ≠ doğru yorum.** Kod yalnız alıntının metinde geçtiğini ve sayfasını kanıtlar;
  `text` alanındaki özetin alıntıya sadık olduğunu kanıtlamaz. Alan sınıflaması da Haiku'nundur
  (ör. karşılaştırma modelleri `veri_setleri_ve_kaynaklar`'a düşebiliyor).
- **Markdown'da alıntı yok.** 44 maddelik kart 1500 token'a ancak alıntısız ve madde metni ~100 karaktere
  kısaltılarak sığıyor; tam alıntı `card.json`'da. Token sayısı karakter/3.5 tahmini, gerçek sayım değil.
- **Bölümleme sezgisel.** Biçim bilgisi (büyük/kalın satır) + numara +1 kuralı + içindekiler
  süzgeci. İki gerçek makalede ana bölümler doğru çıktı, ama ek alt başlıkları (A, B…) her zaman
  ayrılmıyor. Bölüm adı çıkarımı etkilemez (tüm metin parçalara girer), **tek istisna references**:
  yanlış bir "References" satırı sonrasını LLM'den düşürür. Funnel bunu `skipped_references` (sayfa +
  karakter) olarak gösterir; kontrol edilmeli.
- **Kapsam:** `kapsam_disi` ve `sinirliliklar` en çok 5 madde; birleştirme önemli bir maddeyi atabilir
  (atılanlar `dropped_by_merge` sayısıyla görünür, içerik ham havuzda saklanmaz).
- **`ask` BM25:** sözcük eşleşmesine dayanır. Türkçe soru için kart adımında Haiku İngilizce arama
  terimleri üretir, ama eş anlamlı/dolaylı anlatım kaçabilir; "bulunamadi" kesin yokluk kanıtı değildir.
- **Tam metin:** yalnız PDF. HTML tam metin, OCR (taranmış PDF → `EMPTY_TEXT`) ve tablo/şekil içeriği yok;
  iki sütun düzeni pymupdf'in blok sırasına bağlı. Formül ve tablo içi sayılar alıntıda bozulabilir → UNVERIFIED.
- **Tekrarlanabilirlik:** aynı makalenin `--force` ile yeniden okunması farklı (benzer) kart verir.
- **Önbellek süresiz**, sürüm değişince kartlar otomatik yenilenmez (`--force`).
- `anthropic_api` arka ucu canlı denenmedi (anahtar yok).
- Yan etki: `claude` CLI kendi `~/.claude` dizinine iz bırakabilir (`--no-session-persistence` açık);
  bunun dışında tüm yazmalar proje klasöründe.
