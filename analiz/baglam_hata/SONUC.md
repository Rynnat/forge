# SONUC: bağlam büyüdükçe hata artıyor mu? (ön kayıt: ONKAYIT-baglam-hata.md)

**Karar: DESTEKLENMİYOR** (her iki sinyalde de). Bu veride bağlam büyüdükçe araç hatası ya da kullanıcı düzeltmesi artmıyor; araç hatası hafifçe azalıyor. "Oturum yorgunluğu" cümlesi uygulanmaz (kaybolacak bir etki yok).

Veri: 59 oturum, 15 928 tekil asistan turu (7 380 ana, 8 548 alt-ajan), 1 850 gerçek insan mesajı, 47 düzeltme olayı. Orkestra deney klasörleri (otomatik, insan yok) dışarıda. Seed 20261026, oturum bazlı bootstrap 1000.

## Kova oranları (olay/tur)

| Sinyal | <50k | 50-100k | 100-150k | >=150k | büyük/küçük oran (%95 AA) | Spearman ρ tur düzeyi (%95 AA) | tekdüze? |
|---|---|---|---|---|---|---|---|
| Araç hatası, hepsi | 29/940 (3,09%) | 178/4116 (4,32%) | 84/2661 (3,16%) | 220/8211 (2,68%) | 0,87 (0,56-1,40) | -0,041 (-0,060; -0,018) | hayır |
| Araç hatası, yalnız ana | 1/33 (3,0%) | 74/1617 (4,58%) | 42/1333 (3,15%) | 111/4397 (2,52%) | 0,83 (0,19-1,29) | -0,051 (-0,072; -0,026) | hayır |
| Araç hatası, yalnız alt-ajan | 28/907 (3,09%) | 104/2499 (4,16%) | 42/1328 (3,16%) | 109/3814 (2,86%) | 0,93 (0,60-1,53) | -0,033 (-0,056; -0,002) | hayır |
| Düzeltme (birincil, tüm ana turlar) | 1/33 (3,0%) | 12/1617 (0,74%) | 9/1333 (0,68%) | 25/4397 (0,57%) | 0,19 (0,04-0,38) | -0,0001 (-0,033; 0,043) | hayır |
| Düzeltme (ikincil, insanla biten turlar) | 1/19 | 12/482 (2,49%) | 9/352 (2,56%) | 25/997 (2,51%) | 0,48 (0,10-0,94) | 0,016 (-0,043; 0,084) | hayır |

Karar kuralı: "destekleniyor" için oran >=1,5 ve ρ alt sınırı >0 gerekirdi; hiçbiri sağlanmadı. Oran <1,2 ya da ters yön olduğu için "desteklenmiyor".

## Tur sırası karıştırıcısı

- Bağlam ile tur sırası güçlü bağlı (ρ = 0,77). Tur sırası kovasına göre araç hatası: 1-10 %3,93, 11-30 %3,89, 31-100 %2,81, 101-300 %2,73, >300 %2,69 (uzadıkça azalıyor). Düzeltme: %0,75 / 0,83 / 0,61 / 0,82 / 0,15, belirgin eğilim yok.
- Tur sırası kovası içinde ayarlı ρ: araç hatası -0,023 (-0,036; -0,004), düzeltme -0,002 (-0,029; 0,016). Kova içi bağlam etkisi de pozitif değil. Kovaların çoğunda bağlam kovalarının dağılımı çok dengesiz (küçük bağlam kovaları boş), bu yüzden kova içi oranlar gürültülü.

## Düzeltme kalıbı isabeti (40 rastgele olay, seed 20261026, kör)

Yalnız kullanıcı mesajının ilk 60 karakterine bakılarak (önceki asistan eylemi görülmeden) hükmedildi: kesin düzeltme 27, belirsiz 5, düzeltme değil 8. İsabet: **%67,5 (sıkı) - %80 (belirsizler dahil)**. Yanlış pozitifler: "evet hayır" sorusuna cevap, "yanlış chat" (kullanıcının kendi hatası), "hatalı mıydı?" sorusu, hardware şikayeti.

Kalıp dağılımı (47 olay): "hayır" 27 (hayır+hayir), "hatalı" 4, "çalışmıyor" 4, "niye" 4, "yanlış/yanlis" 4, "olmadı" 2, kalanı tek.

## Sınırlar

1. Düzeltme olayı yalnız 47 (50k altı bölgede 1 olay): düzeltme sinyalinin gücü düşük; aşırı kova oranları (n=33) güvenilmez. Duyarlılık: 50-100k -> >=150k kıyaslarında araç hatası 4,32% -> 2,68% (0,62x), düzeltme 0,74% -> 0,57% (0,77x), yön yine ters.
2. Bağlam ≥50k neredeyse hep (sistem istemi + önbellek tabanı); "<50k" kovası ana iş parçacığında yok sayılır. Gerçek "boş bağlam" ile karşılaştırma bu veriyle yapılamaz.
3. Araç hatası, model hatası değil: reddedilen izin, bulunamayan dosya, kullanıcı iptali de sayılır. "Hata" != "uydurma"; uydurma ölçülmedi.
4. Sağkalım yanlılığı: kötü giden oturumlar erken bırakılıp yeni oturum açılıyor olabilir; uzun bağlama ulaşan oturumlar zaten iyi gidenlerdir. Bu, "desteklenmiyor"un nedeni olabilir (kanıtlanmadı). Görev türü karıştırıcısı ölçülmedi.
5. Kalıp eşleşmesi tam sözcük (ör. "dur" "durum"u yakalamaz); ek-1 listesi değişmedi. İnsan mesajı yalnız hemen önceki tura bağlandı; kuyruklanmış mesajlar yanlış tura düşmüş olabilir.
6. Kesinlik hükmü bağlam görmeden verildi ve tek yargıç (Claude) tarafından; aynı aileden denetçi şerhi (KURALLAR 4.8).

Kod: `analiz.py` (aynı klasör), ham çıktı `sonuc.json` (yalnız sayılar). Örnek parçacıkları rapora yazılmadı (gizlilik).
