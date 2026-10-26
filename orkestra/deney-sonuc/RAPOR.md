# HÜKÜM: ARŞİV (RED) (ort(B−A1) < 0)

> Kural: eksik veya başarısız koşu o sistem için **recall 0** sayılır; eşikler ön kayıttaki gibi uygulanır. Birincil karşılaştırma B−A1; A0 yalnız betimsel.

## Eşikler

| eşik | değer | eşik değeri | geçti? |
|---|---|---|---|
| Eşli recall farkı B−A1 | -9.0 puan, p=1.0000 | ≥ +10 puan VE p < 0.05 | HAYIR |
| Maliyet B/A1 | $0.639 / $0.951 = %67 | ≤ %50 | HAYIR |
| Sadakat | 30/30 destekli, uydurma=0, Wilson alt=0.886 (betimsel) | ≥ 28/30 VE uydurma = 0 | evet |
| Bağlam (B son rapor) | 3793 token ort. (30 koşu) | ≤ 4000 token | evet |

- n = 30 eşli soru
- İşaret testi (tek yönlü, eşitlik atılır): +3 / −25 / =2, p = 1.0000
- Ara durdurma (ilk 10 soru, ort. B−A1 ≤ -10): ort = -6.0 → tetiklenmedi
- ARŞİV koşulu (ort(B−A1) < 0 ya da $(B) > $(A1)): **VAR**

## Ayrıntı

### Sistemler (30 soru)

| sistem | ort. recall@30 (puan) | ort. $ | ort. süre (s) | web arama ort. |
|---|---|---|---|---|
| B | 36.7 | 0.639 | yok | yok |
| A1 | 45.7 | 0.951 | 168 | 28.0 |
| A0 | 40.8 | 0.173 | 66 | 1.0 |

### A0 karşılaştırmaları (betimsel)
- B−A0: n=30, ort = -4.1 puan, işaret +10/−19, p = 0.9693
- A1−A0: n=30, ort = 4.9 puan, işaret +18/−8, p = 0.0378

### Alan kırılımı

| alan | n | B | A1 | A0 | B−A1 |
|---|---|---|---|---|---|
| Donanım | 3 | 33.3 | 42.2 | 32.2 | -8.9 |
| Güvenlik | 3 | 54.4 | 71.1 | 60.0 | -16.7 |
| HCI/Görselleştirme | 3 | 41.1 | 56.7 | 46.7 | -15.6 |
| ML/Görüntü | 3 | 48.9 | 44.4 | 50.0 | 4.4 |
| NLP | 3 | 34.4 | 41.1 | 40.0 | -6.7 |
| Robotik | 3 | 21.1 | 38.9 | 34.4 | -17.8 |
| Sistemler/Ağlar | 3 | 22.2 | 32.2 | 22.2 | -10.0 |
| Teori/Algoritmalar | 3 | 36.7 | 48.9 | 45.6 | -12.2 |
| Veritabanı | 3 | 26.7 | 24.4 | 23.3 | 2.2 |
| Yazılım Müh./PL | 3 | 47.8 | 56.7 | 53.3 | -8.9 |

### Soru başına recall@30 (puan)

| soru | B | A1 | A0 | B−A1 | durum B/A1/A0 |
|---|---|---|---|---|---|
| q01 | 20.0 | 30.0 | 23.3 | -10.0 | EKSİK/OK/OK |
| q02 | 40.0 | 46.7 | 46.7 | -6.7 | EKSİK/OK/OK |
| q03 | 23.3 | 33.3 | 20.0 | -10.0 | EKSİK/OK/OK |
| q04 | 23.3 | 40.0 | 40.0 | -16.7 | EKSİK/OK/OK |
| q05 | 36.7 | 46.7 | 43.3 | -10.0 | EKSİK/OK/OK |
| q06 | 53.3 | 33.3 | 30.0 | 20.0 | EKSİK/OK/OK |
| q07 | 20.0 | 30.0 | 26.7 | -10.0 | EKSİK/OK/OK |
| q08 | 6.7 | 10.0 | 13.3 | -3.3 | EKSİK/OK/OK |
| q09 | 40.0 | 50.0 | 50.0 | -10.0 | EKSİK/OK/OK |
| q10 | 43.3 | 46.7 | 50.0 | -3.3 | EKSİK/OK/OK |
| q11 | 50.0 | 80.0 | 60.0 | -30.0 | EKSİK/OK/OK |
| q12 | 36.7 | 36.7 | 40.0 | 0.0 | EKSİK/OK/OK |
| q13 | 70.0 | 76.7 | 63.3 | -6.7 | EKSİK/OK/OK |
| q14 | 50.0 | 70.0 | 63.3 | -20.0 | EKSİK/OK/OK |
| q15 | 53.3 | 56.7 | 50.0 | -3.3 | EKSİK/OK/OK |
| q16 | 30.0 | 40.0 | 10.0 | -10.0 | EKSİK/OK/OK |
| q17 | 6.7 | 23.3 | 3.3 | -16.7 | EKSİK/OK/OK |
| q18 | 16.7 | 30.0 | 13.3 | -13.3 | EKSİK/OK/OK |
| q19 | 73.3 | 83.3 | 86.7 | -10.0 | EKSİK/OK/OK |
| q20 | 23.3 | 33.3 | 23.3 | -10.0 | EKSİK/OK/OK |
| q21 | 6.7 | 10.0 | 16.7 | -3.3 | EKSİK/OK/OK |
| q22 | 60.0 | 56.7 | 46.7 | 3.3 | EKSİK/OK/OK |
| q23 | 26.7 | 33.3 | 33.3 | -6.7 | EKSİK/OK/OK |
| q24 | 63.3 | 76.7 | 73.3 | -13.3 | EKSİK/OK/OK |
| q25 | 36.7 | 43.3 | 46.7 | -6.7 | EKSİK/OK/OK |
| q26 | 36.7 | 13.3 | 23.3 | 23.3 | EKSİK/OK/OK |
| q27 | 80.0 | 80.0 | 70.0 | 0.0 | EKSİK/OK/OK |
| q28 | 33.3 | 80.0 | 70.0 | -46.7 | EKSİK/OK/OK |
| q29 | 20.0 | 33.3 | 30.0 | -13.3 | EKSİK/OK/OK |
| q30 | 20.0 | 46.7 | 56.7 | -26.7 | EKSİK/OK/OK |

### B kaynak durumu
- EKSİK kaynaklı koşu: 30/30
  - q01: openalex, s2_zenginlestirme
  - q02: openalex, s2_zenginlestirme
  - q03: openalex, s2_zenginlestirme
  - q04: openalex, dblp, s2_zenginlestirme
  - q05: openalex, s2_zenginlestirme
  - q06: openalex, s2_zenginlestirme
  - q07: openalex, s2_zenginlestirme
  - q08: openalex, s2_zenginlestirme
  - q09: openalex, s2_zenginlestirme
  - q10: openalex, s2_zenginlestirme
  - q11: openalex, s2_zenginlestirme
  - q12: openalex, s2_zenginlestirme
  - q13: openalex, s2_zenginlestirme
  - q14: openalex, s2_zenginlestirme
  - q15: openalex, s2_zenginlestirme
  - q16: openalex, s2_zenginlestirme
  - q17: openalex, s2_zenginlestirme
  - q18: openalex, s2_zenginlestirme
  - q19: openalex, s2_zenginlestirme
  - q20: openalex, arxiv, s2_zenginlestirme, ozet_arxiv
  - q21: openalex, s2_zenginlestirme
  - q22: openalex, s2_zenginlestirme
  - q23: openalex, s2_zenginlestirme
  - q24: openalex, s2_zenginlestirme
  - q25: openalex, arxiv, s2_zenginlestirme, ozet_arxiv
  - q26: openalex, arxiv, s2_zenginlestirme, ozet_arxiv
  - q27: openalex, dblp, arxiv, s2_zenginlestirme, ozet_arxiv
  - q28: openalex, arxiv, s2_zenginlestirme, ozet_arxiv
  - q29: openalex, arxiv, dblp, s2_zenginlestirme, ozet_arxiv
  - q30: openalex, arxiv, s2_zenginlestirme, ozet_arxiv
- OZET_YOK alıntı durumu: 158/900 çalışma
- ozet_arxiv sayaçları (toplam): aday=19960, atlandi_kota=1050, atlandi_tavan=15460, bulunamadi=3074, bulundu=376, denendi=3450, onbaski_kesim_sonrasi=6

### Kararlılık (B, k koşu, soru içi örnek std. sapması, n−1)
Kararlılık koşusu verilmedi.

### Sadakat
- n=30, sayım: {'DESTEKLENIYOR': 30, 'DESTEKLENMIYOR': 0, 'UYDURMA': 0, 'KONTROL_EDILEMEDI': 0}; Wilson alt (z=1,96) = 0.886 (betimsel; bağlayıcı olan sayıdır)

## Bilinen sınırlamalar
- Anahtarsız koşu: OpenAlex ve Semantic Scholar anahtarı yoktu; B bu kaynaklar olmadan ölçüldü (B için haksız zayıflık olabilir).
- Sorular Türkçe yazıldı; iki sistem de aynı soruyu aldı, ama şef planı/sorguları İngilizce üretir; dil etkisi ölçülmedi.
- Altın set kalite kontrolü 2/30 hata buldu (kesik DOI); sistematik süzgeçle 26 kayıt atıldı, süzgeç sonrası yeni örneklem çekilmedi.
- Sadakat denetçisi (Sonnet) B ile aynı model ailesinden; bağımsız bir aile değil.
- Altın = survey kaynakçası; survey'in atıf yapmadığı ama önemli çalışmalar 'yanlış' sayılır (recall tavanı < 1).
- Özet token sayısı tahminidir: ceil(karakter/3), gerçek tokenizer değil.
