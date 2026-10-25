# Ölçüm: Claude tek başına kaynak kimliği uyduruyor mu? (2026-10-26, ağsız)

**Yöntem:** listelenen çalışmaların arXiv kimlikleri, yerel arXiv dizininde (forge-v1, 3,2 M kayıt, anlık görüntü 2026-10-15) aranır.
- Kimlik var mı?
- Kimliğin başlığı, listelenen başlıkla aynı mı? Normalize başlık benzerliği:
  - ≥ 0,90 → DOĞRU
  - 0,6–0,9 → YAKIN (genelde sürüm ya da başlık değişikliği)
  - < 0,6 → BAŞKA MAKALE

DOI'ler kontrol edilmedi; Crossref'e gitmek çalışan deneyi etkilerdi.

| Sistem | Çalışma | arXiv kimlikli | DOĞRU | YAKIN | BAŞKA MAKALE | KİMLİK YOK | Hatalı oran |
|---|---|---|---|---|---|---|---|
| A0 (Opus hafızadan, deneyin 30 sorusu) | 870 | 602 | 575 | 17 | 10 | 0 | **%1,7** |
| A1 (Opus aramalı, D2) | 30 | 14 | 13 | 1 | 0 | 0 | %0 |
| B (orkestra, biten 17 soru) | 510 | 351 | 350 | 1 | 0 | 0 | %0 |

## Okuma
- **"Claude tek başına kaynak uydurur" iddiası arXiv kimlikleri için büyük ölçüde çürüdü.**
  - Opus hafızadan bile %98,3 doğru kimlik veriyor.
  - Var olmayan kimlik hiç yok.
  - Hata türü uydurma değil, karıştırma: gerçek bir kimliği başka bir makaleye bağlıyor (10/602).
- B tasarım gereği %0. Fark küçük: ~1,7 puan.
- **Kontrol edilmeyenler:**
  - A0'ın 268 DOI'li ya da kimliksiz çalışması.
  - Kimliksiz listelenen çalışmalar; uydurma başlık ihtimali en çok burada.
- Bu, Forge'un "doğrulanabilirlik" avantajının pratikte küçük olduğunu gösteriyor: kalite farkı, varsa, recall'dan gelmeli.
