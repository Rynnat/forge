# Fikir pilotu — sonuç (2026-10-25, n=3 konu, PİLOT: karar yok)

| | A (Claude tek elden) | B (orkestra + fikir adımı) |
|---|---|---|
| Ağırlık / konu | **$0,35–0,38** | $1,10–1,12 (**~3×**) |
| Süre / konu | **~80 s** | 16–31 dk |
| Opus token / konu | ~190–230 bin (çoğu ucuz önbellek okuması) | ~45 bin (önbelleksiz, büyük istemler → Opus kısmı tek başına $0,49) |
| Web araması | 10–11 | web işçileri + 6 Haiku yenilik işçisi |
| Yenilik (Sonnet denetçi) | 9/9 KISMEN, 0 YAPILMIŞ | 8 KISMEN + **1 YENİ**, 0 YAPILMIŞ |
| Dayanak (kodla çözümleme) | 43/43 VAR, 0 uydurma | 28 VAR, 10 BİLİNMİYOR (kaynak hatası), 0 YOK |
| Kör hakem (Sonnet) | 1/3 (T2) | **2/3** (T1 7,5–6,5; T3 7–5) |

## Hipotezler
- **H1 (B ≤ %60 × A ağırlık): TUTMADI.** B ~3 kat pahalı. A beklenenden çok ucuz: tek Opus çağrısı, 11 arama, girdinin çoğu önbellek okuması.
  Kullanıcının "Claude tek elden muazzam token harcar" iddiası bu görevde **çürüdü**.
- **H2 (B YAPILMIŞ ≤ A): tuttu** (ikisi de 0).
- **H3 (hakem ≥ 2/3 B): tuttu** (2/3). Hakemin B gerekçesi: daha yapılabilir, açık veri setleri ve kodla daha iyi sınırlandırılmış.
- **H4 (B uydurma 0): tuttu**, ama 10 kaynak çözümlenemedi (BİLİNMİYOR).

## Okuma
- Kalitede B'ye hafif eğilim var; 3 konuda bu şans olabilir.
- Maliyette A açık ara önde.
- B'nin pahalılığı üç kalemden geliyor:
  - Opus çağrıları önbelleksiz ve büyük istemli (80 kart).
  - Haiku yenilik işçileri, konu başına ~$0,25.
  - Okuyucu, ~$0,21.
- "Pahalı model token sayısı" yanıltıcı bir ölçüt: B daha az Opus token'ı kullandı ama o token'lar daha pahalıydı.

## Sonraki adım için dersler
1. Ağırlık hedefi için B'nin Opus istemini küçültmek: 80 kart yerine ~30 kart. Ölçülerek yapılmalı.
2. Asıl değer genişlik ve doğrulamada olabilir, ucuzlukta değil. İddia buna göre yeniden kurulmalı:
   "aynı ya da biraz daha fazla token'la daha iyi ve doğrulanabilir sonuç".
3. Kullanıcının kör hükmü bekleniyor: `pilot-fikir/sonuc/` içindeki 6'şar fikir.
