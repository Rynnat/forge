# Ajan Maliyet Profili (2026-10-25)

## Yöntem
Bu ölçümün dayandığı veriler:
- Transkriptlerden okunan alanlar: yalnız usage alanları ve araç çağrılarının adları.
- CAD ajanı için ek olarak: Bash komutlarının çalıştırdığı betik adı.
- Mesaj içeriği okunmadı.

Fiyatlar yaklaşık Opus fiyatları; yalnızca sıralama için kullanıldı (abonelikte $ teoriktir). Betikler:
- `scratchpad/profil.py`
- `scratchpad/profil_cad.py`

## Tüm oturumlar
`maliyet-sayaci sessions` çıktısı:
- 50 oturum.
- ≈ **$1628** teorik maliyet.
- 3,2 milyar cache-okuma tokenı.

## Ajan türü bazında (alt-ajanlar)
| Ajan | Koşu | ~$ toplam | $/koşu | En sık araçlar |
|---|---|---|---|---|
| general-purpose | 153 | 965 | 6.3 | Bash 2183, WebSearch 1239, WebFetch 700 |
| **cad-tasarimci-v2** | 23 | **654** | **28.4** | Bash 1787 |
| cad-tasarimci | 3 | 74 | 24.7 | Bash 375 |
| mekanizma-arastirmaci-v2 | 10 | 14 | 1.4 | WebSearch 163 |
| planlayici / denetci / dogrulayici | 16 | ~41 | 1.2–6.1 | Bash |

## cad-tasarimci-v2'nin içi
**Bash hedefleri:**
| Hedef | Çağrı |
|---|---|
| Betik dışı komutlar (`cd` ile başlayan: gezinme, ls, grep) | 843 |
| check.py | 181 |
| build.py | 127 |
| params.py | 68 |
| onizleme.py | 68 |
| render.py | 50 |
| sleep / until ile bekleme | 95 |

**Araç sonucu boyutu:**
- 2400 sonuç, toplam 63,5 milyon karakter (≈16 milyon token).
- Medyan 659 karakter, **p90 28.580 karakter**.

## Melezleştirme adayları (ölçüme göre)
1. **CAD döngüsü (en büyük kalem):**
   - Gözlem: `build → check → render` döngüsü tekrarlı ve deterministik.
   - Aday: tek komut + kompakt özet çıktı (yalnız değişen ölçüler ve başarısız kontroller).
   - Hipotez: koşu başı maliyet ≥%40 düşer, kontrol sonuçları aynı kalır.
2. **Çıktı şişkinliği:**
   - Gözlem: araç sonuçlarının %10'u 28 bin karakterin üstünde. Her biri sonraki her turda cache'den yeniden okunuyor.
   - Aday: çıktı bütçesi koymak (P-B Öneri 2 ile aynı yön).
3. **Gezinme ve bekleme:**
   - Gözlem: 843 gezinme/ls ve 95 bekleme çağrısı var.
   - Aday: proje durumu özet komutu ve arka plan bildirimi.
4. **general-purpose araştırma:**
   - Gözlem: WebSearch/WebFetch ağırlıklı.
   - Aday: gapmine/makale-okuyucu. Ancak gapmine RED aldığı için önce düzeltilmeli.

> Not: Bu bir hipotez listesi. Hiçbiri ölçülmeden yapılmayacak. Yapılırsa eşik önceden commit edilecek.
