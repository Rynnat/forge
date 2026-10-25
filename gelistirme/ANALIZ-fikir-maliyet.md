# Fikir hattı neden ~3× pahalı? (2026-10-25, ağsız analiz + 1 test çağrısı)

Veri: fikir pilotu, 3 konu (`pilot-fikir/sonuc`). B ~$1,10 / konu, A ~$0,37.

## Kalem dökümü (konu başına ortalama)
| aşama | model | çağrı | ağırlık |
|---|---|---|---|
| fikir_yenilik (6 web işçisi) | Haiku | 6 | $0,25 |
| okuyucu | Haiku | 40 | $0,21 |
| web_isci | Haiku | 3 | $0,16 |
| fikir_uret | Opus | 1 | $0,16 |
| fikir_sec | Opus | 1 | $0,13 |
| sef_final | Opus | 1 | $0,13 |
| sef_plan | Opus | 1 | $0,07 |

## Bulgu 1 — tek seferlik çağrılar önbellek yazma primi ödüyor (DOĞRULANDI)
- `claude -p`, girdiyi 1 saatlik önbelleğe yazıyor: Opus için $8/M, oysa düz girdi $4/M. Bu önbellek bir daha hiç okunmuyor.
- Log: `sef_final` → input 2, **cache_write 10149**, cache_read 0.
- Test (Haiku, ~6k token istem):
  - önbellek açık: $0,00112,
  - `DISABLE_PROMPT_CACHING=1`: **$0,00062 (−%44)**.
- **Kural:** tek seferlik çağrılarda (plan, final, fikir_uret, fikir_sec, okuyucu) önbellek kapatılır.
  Çok turlu web işçilerinde açık kalır, çünkü onlar önbelleği gerçekten okuyor.
- **Tahmini kazanç:** Opus ~35k girdi × $4/M ≈ $0,14; okuyucu ≈ $0,03 → **~$0,17 / konu (~%15)**.

## Bulgu 2 — şefe 80 kart çok
- Final, üretim ve seçim istemleri ~10–12k token.
- Kart sayısı 80 → 30 olursa üç Opus istemi ~%60 küçülür → ~$0,08 / konu.
- **Risk:** kalite düşebilir. Ölçülmeden yapılmaz.

## Bulgu 3 — okuyucu çıktısı şişkin
- Okuyucu girdisi 257k, çıktısı **~320k token**: parti başına ~8k çıktı.
- Her öğe için not + alıntı yazılıyor.
- Alıntı yalnız rel ≥ 2 öğelere istenirse çıktı yarıya inebilir → ~$0,08.

## Toplam tahmin
- $1,10 → ~$0,77 / konu. A (~$0,37) hâlâ ~2× ucuz.
- **Sonuç:** ucuzluk iddiası bu görevde gerçekçi değil.
- Forge'un iddiası "aynı ya da biraz fazla ağırlıkla daha iyi ve doğrulanabilir sonuç" olmalı.

## Not
- Hepsi v1 adayı. Donmuş v0 deneyi aynen sürer.
- A1 de aynı CLI fiyat yapısıyla ölçülüyor; karşılaştırma adil.
