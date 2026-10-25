# makale-okuyucu — SPEC (v0.1.0)

## Amaç
Ajanların en büyük token harcaması makale tam metnini tekrar tekrar okumak. Bu araç her makaleyi
**bir kez** okur, küçük, yapılandırılmış ve **alıntıyla kanıtlı** bir kart üretir ve önbelleğe koyar.
Sonraki sorular önce karttan, gerekirse yalnız ilgili pasajlardan cevaplanır.

## İş bölümü (Forge felsefesi)
| katman | iş |
|---|---|
| kod | girdi çözümleme, indirme, durum sınıflama, PDF→metin, bölümleme, parçalama, alıntı doğrulama, sayfa bulma, BM25, önbellek, maliyet logu, Markdown bütçesi |
| ucuz LLM (Haiku, `claude -p`) | parça başına alan çıkarımı (alıntılı), kartı birleştirme (yalnız id seçer), soru cevaplama |
| pahalı model | yalnız kartı (≤~1500 token Markdown) okur |

## Girdi
`read <girdi>`; girdi şunlardan biri:
- arXiv id (`2501.08156`, `2501.08156v2`, `arXiv:…`, `https://arxiv.org/abs/…`) → anahtar `arxiv:<id-sürümsüz>`
- DOI (`10.xxxx/…`, `https://doi.org/…`) → anahtar `doi:<küçük harf>`
- PDF URL (`http(s)://…`) → anahtar `url:<sha1[:16]>`
- yerel PDF yolu → anahtar `sha:<sha256[:16]>`; `--as <arXiv|DOI>` ile o anahtara bağlanır.
Aynı PDF baytları (sha256) başka anahtarla gelirse yeniden okunmaz, takma ad eklenir.

## İndirme
Aday URL sırası: arXiv → `https://arxiv.org/pdf/<id>`; DOI → OpenAlex `works/doi:<doi>` →
(arXiv konumu varsa arXiv PDF) → `best_oa_location.pdf_url` → `best_oa_location.landing_page_url`.
Durumlar: `OK | NO_OA | NOT_FOUND | PAYWALL | BOT_BLOCKED | NOT_PDF | PARSE_ERROR | EMPTY_TEXT | NETWORK_ERROR | HTTP_ERROR`.
- Cloudflare/insan doğrulaması (403/429/503 + işaret metni) → `BOT_BLOCKED`. **Atlatma denenmez.**
- 401/402/403 → `PAYWALL`. HTML açılış sayfası → `NOT_PDF`.
- Başarısızlıkta: çıkış kodu 2, her adayın sebebi yazılır, kullanıcıdan `read <yerel.pdf> --as <id>` istenir.
- Kişisel veri gönderilmez (User-Agent'ta e-posta yok, OpenAlex `mailto` yok).

## Metin ve bölümler
- pymupdf ile sayfa sayfa metin; sayfa numarası (1 tabanlı) her satırda korunur.
- Başlık sezgisi: satır başı numaralı (`3`, `3.`, `III.`) kısa satır, numara bir öncekinin +1'i
  olmalı (tablo gürültüsünü eler); ya da yalnız anahtar kelimeden oluşan satır (Abstract, References…).
- Kanonik bölümler: `abstract, introduction, related_work, method, experiments, results,
  limitations, conclusion, references, appendix, other`. Anahtar kelimesi tutmayan numaralı
  başlık `other` olur ama başlık metni saklanır. İlk başlıktan önceki metin `front`.
- `references` LLM'e gönderilmez (funnel'da `skipped_references` olarak sayılır).

## Çıkarım
- Bölümler ~`chunk_chars` (vars. 12 000) karakterlik parçalara bölünür (bölüm sınırı aşılmaz,
  küçük ardışık bölümler birleştirilebilir). Her parça tek Haiku çağrısı (vars. 4 paralel).
- Parça çıktısı: alan → madde listesi; her madde `text` (kısa iddia, İngilizce) + `quote` (birebir).
  `veri_setleri_ve_kaynaklar`: + `name`, `link`; `en_yakin_isler`: + `name`, `relation`.
- Alanlar: `problem, katkilar, yontem, veri_setleri_ve_kaynaklar, deney_kurulumu, ana_sonuclar,
  sinirliliklar, gelecek_calisma, kapsam_disi, en_yakin_isler`.
- **Doğrulama (kod):** alıntı, parçanın metninde normalize edilmiş haliyle aranır (NFKC, tırnak/tire,
  boşluk, büyük/küçük harf, satır sonu tirelemesi, `...` parçaları sırayla). Bulunamazsa
  `UNVERIFIED`, 20 karakterden kısaysa `TOO_SHORT` (o da doğrulanmamış sayılır). Sayfa
  numarası alıntının bulunduğu sayfadan kodla bulunur (sayfa sınırını aşan alıntı → `"4-5"`).
- **Birleştirme:** tek Haiku çağrısı yalnız madde id'lerini seçer/sıralar (alan başına üst sınır);
  metin yeniden yazdırılmaz, böylece alıntı-kanıt bağı bozulmaz. Bilinmeyen id atılır ve sayılır.
  Birleştirme başarısızsa deterministik yedek: doğrulanmışlar önce, token benzerliği ile tekilleştirme, üst sınır.
- Başarısız parça (LLM_ERROR / PARSE_FAIL) kartta `eksik_parcalar` listesinde bölüm + sayfalarla
  görünür; kart durumu `PARTIAL` olur. Sessiz kayıp yok.

## Kart
JSON: `{key, aliases, title, source_url, pages, status, fields{alan:[{text, quote, page, check, ...}]},
eksik_parcalar, funnel, version}`. Markdown: alan başlıkları + maddeler + kısaltılmış alıntı + `p.N`,
doğrulanmamışlar `[UNVERIFIED]`. Bütçe `md_max_tokens` (vars. 1500; token ≈ karakter/4):
aşılırsa önce alıntılar kısaltılır, sonra alan sonundaki maddeler düşer ve "(+N madde JSON'da)" yazılır.

## Sorgu
`ask <girdi> "<soru>"` — makale önbellekte yoksa önce `read`.
1. **kart:** kart maddeleri (id'li) + soru → Haiku `{answerable, answer, item_ids}`. Geçerli id
   varsa kaynak `kart`, alıntılar o maddelerden.
2. **bölüm:** değilse BM25 (kod, ek bağımlılık yok) ile ~1500 karakterlik pasajlar sıralanır, en iyi
   `ask_top_k` (vars. 6) pasaj Haiku'ya gider → `{found, answer, quotes}`; alıntılar pasajlarda
   doğrulanır, sayfa bulunur. Kaynak `bolum`.
3. Hiçbiri → `bulunamadi`. Tam metin asla tek seferde gönderilmez (references hariç tutulur).
Cevaplar `asks` tablosunda önbelleklenir.

## Önbellek ve log
`data/cache.db` (SQLite): `papers` (anahtar, durum, sha256, sayfa, kart JSON), `aliases`, `runs`
(her read/ask: sayfa, parça, Haiku çağrısı, token, maliyet, süre, UNVERIFIED, başarısız parçalar,
durum), `llm_calls`, `asks`. Dosyalar: `data/papers/<anahtar>/paper.pdf, doc.json (sayfa+bölüm),
card.json, card.md`. Başarısız indirmeler de `runs`'a yazılır.

## LLM arka uçları
gapmine'dan kopya: `claude_cli` (vars.; `--system-prompt`, `--tools ""`, `--strict-mcp-config`,
`--setting-sources ""`, `--no-session-persistence`, boş cwd, prompt stdin), `anthropic_api`, `mock`.

## Kısıtlar
Python 3.12, Windows, GPU yok. Bağımlılık: requests, pymupdf, pytest. Her şey proje klasöründe
(`.venv`, `data/`; `HF_HOME` vb. `data/` altına yönlendirilir). Testler ağ ve gerçek LLM istemez.

## Kabul (Forge protokolü için öneri, eşik denetçi tarafından yazılır)
Ölçülecekler: alan başına doğrulanmış madde oranı, altın sete göre `kapsam_disi`/`sinirliliklar`
duyarlılığı, makale başına maliyet ve süre, Markdown token boyu, `ask` doğruluğu.
