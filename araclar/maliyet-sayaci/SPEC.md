# maliyet-sayaci — SPEC

Claude Code oturumlarının ve alt-ajanlarının gerçek token kullanımını transkriptlerden çıkarır, model fiyatıyla teorik dolar maliyetine çevirir. Amaç: "bu iş ajanla mı, araçla mı daha ucuz" sorusunu sayıyla cevaplamak.

## Gizlilik sözleşmesi (değişmez)
- Transkript satırları `json.loads` ile çözülür (bozuk satırı saymanın tek yolu bu) ama yalnız şu alanlar **okunur ve tutulur**:
  `type`, `timestamp`, `sessionId`, `agentId`, `requestId`, `uuid`, `message.id`, `message.model`, `message.usage.*`.
  Ayrıca alt-ajan `*.meta.json` dosyasından yalnız `agentType`.
- `message.content`, `toolUseResult`, `attachment`, meta `description` vb. hiçbir alan okunmaz, yazdırılmaz, saklanmaz.
  Çözülen satır sözlüğü alanlar çekildikten hemen sonra atılır.
- Dosyalar salt okunur açılır (`open(..., "r")`); araç hiçbir dosyaya yazmaz. Çıktı yalnız stdout.
- `tools` modunda yalnız maliyet log dosyaları okunur ve onlardan da yalnız sayısal `llm` bloğu alınır.

## Veri yapısı (2026-10-25'te keşfedildi)
Kök: `~/.claude/projects/<proje-klasörü>/`
- `<oturum-id>.jsonl` — ana oturum transkripti.
- `<oturum-id>/subagents/agent-<ajan-id>.jsonl` — oturumun alt-ajanları (+ `agent-<ajan-id>.meta.json`: `agentType`).
- `<oturum-id>/subagents/workflows/<wf-id>/agent-<ajan-id>.jsonl` — workflow içinden doğan ajanlar.
- `<oturum-id>/tool-results/`, `workflows/` — maliyet verisi yok, okunmaz.
- `%TEMP%/claude/<proje>/<oturum>/tasks/<ajan-id>.output` — alt-ajan transkriptinin **hard link**'i
  (aynı dosya, link sayısı 2) ya da ajan bitince 0 bayta inmiş kopyası. Ana kaynak `subagents/`; `--ek-dizin`
  ile bu klasör de eklenebilir, mesaj id tekilleştirmesi çift sayımı engeller.

Satır türleri: `assistant`, `user`, `api-request`, `attachment`, `queue-operation`, `system`, ... Maliyet yalnız
`type == "assistant"` satırlarındaki `message.usage`'dan gelir.

### usage alanları
`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`,
`cache_creation.ephemeral_5m_input_tokens`, `cache_creation.ephemeral_1h_input_tokens`,
`server_tool_use.web_search_requests`, `speed` (`standard`/`fast`), `inference_geo` (`global`/`us`/...).
Gerçek veride cache yazımlarının büyük kısmı **1 saatlik** (2x fiyat), bu yüzden 5m/1h ayrı fiyatlanır.

## Tekilleştirme
Claude Code bir API yanıtını içerik bloğu başına ayrı satır olarak yazar (thinking, text, tool_use...) ve
her satır aynı `message.id` ile aynı `usage`'ı tekrarlar. Kural:
- Anahtar: `message.id`; yoksa `requestId`; o da yoksa tekilleştirilemez → satır olduğu gibi sayılır ve
  `id_yok` sayacında raporlanır.
- Aynı anahtarın tekrarlarında her token alanı için **en büyük değer** alınır (akış parçalarında
  `output_tokens` büyüyebilir; eşit tekrarlarda sonuç aynıdır). Zaman = en erken zaman damgası.
- Tekilleştirme çalıştırma boyunca **küresel**dir (dosyalar arası da), böylece hard link / kopya
  dosyalar çift sayılmaz. Ajan ataması ilk görülen kayda göre yapılır.

## Dürüst durum bilgisi
Her çıktının sonunda veri kalitesi satırı: dosya sayısı, satır, **bozuk satır** (JSON çözülemeyen ya da
nesne olmayan; atlanır ama sayılır, dosya adıyla `--json`'da listelenir), tekrar satır, usage'ı eksik
assistant mesajı, id'siz mesaj, **fiyatı bilinmeyen model** (token'ları sayılır, doları `null`).
`<synthetic>` model (yerel üretilmiş, API'ye gitmemiş mesaj) 0 maliyetle sayılır.

## Fiyatlandırma
- `fiyatlar.json`: model başına `input`, `output`, `cache_write_5m`, `cache_write_1h`, `cache_read` ($/MTok),
  isteğe bağlı `uzun_baglam` (eşik + ayrı fiyatlar; Haiku 5.5 > 100K prompt), `fast_carpan`,
  ayrıca `web_search_per_1k`, `bolge_carpanlari` (`us`: 1.1). Kaynak URL ve tarih dosyada.
- Model eşleşmesi: tam ad; yoksa en uzun önek (ör. tarihli sürüm adları).
- Maliyet = Σ token × fiyat / 1e6 × (fast ise fast çarpanı) × bölge çarpanı + web arama.
- `usage.cache_creation` alt kırılımı yoksa tüm cache yazımı 5m sayılır (alt sınır) ve sayacı raporlanır.
- **Abonelik (Pro/Max) kullanıcısı için dolar teoriktir**: API'de aynı işi yapsaydınız ödeyeceğiniz liste
  fiyatıdır, faturanız değildir. Her tabloda yazılır.

## Komutlar
```
python maliyet_sayaci.py sessions [--proje AD] [--since TARIH] [--limit N] [--json]
python maliyet_sayaci.py agents --session ID_ONEKI [--ek-dizin DIZIN] [--json]
python maliyet_sayaci.py since TARIH [--proje AD] [--json]
python maliyet_sayaci.py tools [--json]
```
Ortak: `--root` (vars. `~/.claude/projects`), `--fiyat` (vars. araç klasöründeki `fiyatlar.json`).
- `sessions`: oturum başına (ana + tüm alt-ajanlar) toplam; son etkinliğe göre yeni→eski. En çok 40 satır;
  fazlası "N oturum gösterilmedi" diye yazılır.
- `agents`: oturumun ana iş parçacığı + her alt-ajan (id, agentType, model, mesaj, token, $) + toplam.
- `since`: tarihten (dahil, UTC, `YYYY-MM-DD`) beri mesajların model bazında toplamı.
- `tools`: forge araçları ve gapmine'ın JSON maliyet logları (aşağıda).

Tablo kompakttır (≤ 40 satır). `--json` tam yapıyı verir (yine içerik yok).

## tools modu
Okunan dosyalar (yalnız bunlar):
- `C:\Users\LENOVO\Projeler\akademik-bosluk\gapmine\reports\*.json` — her rapordan yalnız `llm` bloğu
  (`backend, calls, ok, failed, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd`).
- `C:\Users\LENOVO\Projeler\forge\araclar\*\logs\maliyet*.json` ve `maliyet*.jsonl` — forge araçlarının
  maliyet log sözleşmesi: her kayıt ya üst düzeyde ya da `llm` altında yukarıdaki sayısal alanları taşır.
  (makale-okuyucu henüz yok; bu sözleşmeye uyarak yazdığında otomatik okunur.)
`cost_usd` aracın kendi bildirdiğidir (gapmine'da `claude -p`'nin `total_cost_usd`'u); yeniden fiyatlanmaz.
gapmine'ın `data/gapmine.db` `llm_calls` tablosu aynı çağrıları tutar; çift sayım olmasın diye okunmaz.

## Testler
`pytest` (`tests/`): tekilleştirme, dosyalar arası tekilleştirme, eksik usage, bozuk satır sayımı,
model bazlı fiyat (5m/1h, uzun bağlam, fast, bölge, bilinmeyen model, synthetic), alt-ajan keşfi, tools modu.
Test dosyaları araç klasörü içindeki geçici `tests/_calisma/` altına yazılır ve silinir.
