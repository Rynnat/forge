# Tahmin kaydı — orkestra v0 deneyi (2026-10-25, sonuçlar görülmeden)

B'nin 30 sorusundan yalnız 1'i bitmişken yazıldı (q01: $0.652, 1151 s). A1/A0'ın hiçbir gerçek koşusu ve hiçbir puan görülmedi.

## Claude (şef) tahmini
- recall@30 ortalama: A0 ≈ %20, A1 ≈ %25, B ≈ %28. Ortalama(B − A1) ≈ +3 puan (%80 aralık: −5 … +10).
- Eşik 1 (≥ +10 puan ve p < 0,05): **tutmaz** (olasılık ~%20).
- Eşik 2 (maliyet, B ≤ %50 × A1): A1 ≈ $1,2 → sınır ≈ $0,60; B ≈ $0,60. **Yazı tura** (~%45).
- Eşik 3 (sadakat ≥ 28/30, 0 uydurma): **tutar** (~%80). B yalnız gerçek kayda çözülmüş çalışmaları listeliyor.
- Eşik 4 (özet ≤ 4000 token): **tutar** (~%95).
- Genel: **RED** (~%80). ARŞİV (B − A1 < 0 ya da $B > $A1) olasılığı ~%30.
- Gerekçe: Opus'un hafızası/araması alanın klasiklerini zaten buluyor; survey kaynakçaları ise çok sayıda niş ve yeni çalışma
  içeriyor. B daha geniş tarıyor ama 30'luk listede sıralama aynı "ünlü" işlere kayıyor. Anahtarsız koşu (OpenAlex/S2 yok)
  ve IEEE/ACM özet eksikliği B'yi aşağı çeker.

## Kullanıcı tahmini
(boş — kullanıcı isterse ekler)
