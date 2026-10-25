# Ön Kayıt: maliyet-sayaci kabul testi (2026-10-25)

Bu dosya kod değişikliğinden ÖNCE commit edilir.

## Değişecekler
1. **"Son bağlam + son çıktı" sütunu:** ajan başına, son assistant çağrısının `input + cache_creation + cache_read + output` toplamı.
2. **`etiketler.csv`:** oturum/ajan → `arastirma | forge-meta | ogrenme | diger`.
3. **`ozet --hafta` alt komutu:** etiket bazında pay.
4. **Regresyon testi:** hakemin 19 ajanlık karşılaştırması.

## Metrik ve eşikler
- **Ana test (görülmemiş ajanlar):**
  - Kapsam: hakem raporundan sonra oluşmuş ajanlar. Bu oturumda 2026-10-25 10:00 UTC sonrası başlayanlar ve sonraki oturumlardakiler; n ≥ 10.
  - Ölçülen: yeni sütun ile resmi `subagent_tokens` arasındaki sapma.
  - Eşik: sapma **≤ %2**, ve bu **10/10** ajanda tutmalı.
- **Regresyon:** hakemin 19 ajanında toplam token sapması **≤ %0,5**.
- **Etiket katmanı:** ilk hafta raporunda eşlenmemiş pay **≤ %10** (bugün %35).
- **Karar:** ikili, KABUL ya da RED. Araç deterministik olduğu için k=1 yeterli.
- **Denetçi:** kodu yazandan farklı bir model ailesi.

## Öldürme
- Görülmemiş ajanlarda tek bir sapma > %2 ise → **RED**. Araç sayaç olarak kullanılmaya devam eder ama KAYIT'ta KABUL yazmaz.
- Etiket katmanında 3 hafta üst üste eşlenmemiş pay > %30 ise → katman silinir. Bu durumda OLUM-KRITERI K2 "ölçülemedi" ve başarısız sayılır.
