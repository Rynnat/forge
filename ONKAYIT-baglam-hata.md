# Ön Kayıt: Bağlam büyüdükçe Claude'un hata oranı artıyor mu? (2026-10-26)

Bu dosya analiz kodundan ÖNCE commit edilir. Veri: kullanıcının Claude Code oturum kayıtları (yerel, salt okunur).

## Hipotez (kullanıcı, 2026-10-26)
Uzun projede bağlam doldukça ve kapsam büyüdükçe hata ve uydurma olasılığı artar. Bu yüzden Claude tek başına uzun işleri (ör. makale) güvenilir biçimde bitiremez.

## Ölçüm
- **Birim:** asistan turu (ana iş parçacığı + alt-ajanlar ayrı).
- **Bağlam büyüklüğü:** o turdaki girdi + önbellek token'ı. Kova: < 50k / 50–100k / 100–150k / ≥ 150k.
- **Hata olayı:** iki sinyal, ikisi ayrı raporlanır.
  1. **Araç hatası:** tool_result `is_error=true` (başarısız komut, reddedilmiş düzenleme…).
  2. **Kullanıcı düzeltmesi:** asistan turundan hemen sonraki kullanıcı mesajı bir düzeltme kalıbıyla başlıyor.
     - Kalıplar: "hayır", "yanlış", "neden … yaptın", "dur", "olmamış", "hata", "no", "wrong", "stop" …
     - Kalıp listesi koddan önce bu dosyaya yazılır (ek-1).
- **Karıştırıcılar (raporlanır):**
  - Oturum içindeki tur sırası. Bağlam ile birlikte artar; ayrıca tur sırası kovası raporlanır.
  - Görev türü.
  - Alt-ajan / ana iş parçacığı.

## Eşik / karar (betimsel çalışma; KABUL / RED yok, yön)
- **"Destekleniyor":** her iki sinyalde de en büyük kovanın oranı en küçük kovanınkinin ≥ 1,5 katı **ve** eğilim tekdüze (Spearman ρ > 0, bootstrap %95 alt sınırı > 0).
- **"Desteklenmiyor":** oran farkı < 1,2 kat ya da ters yön.
- Arada kalırsa **"belirsiz"**.
- Tur sırasını sabitleyince (aynı tur sırası kovası içinde) etki kayboluyorsa, sonuç "bağlam değil oturum yorgunluğu / görev zorluğu" olarak yazılır.

## Sınırlar
- Düzeltme kalıbı kaba bir ölçüdür; rastgele 40 olay elle (Claude, kör) kontrol edilir ve isabet oranı raporlanır.
- "Hata" ≠ "uydurma". Uydurma bu veriyle ayrıca ölçülemez; bu bir alt sınır ölçümüdür.

## Ek-1: düzeltme kalıpları (TR + EN, küçük harf, mesaj başı ya da ilk 40 karakter)
hayır · hayir · yanlış · yanlis · olmamış · olmadı · olmadi · dur · neden böyle · neden öyle · niye · hata var · hatalı · bozuk · çalışmıyor · calismiyor · geri al · istemedim · demedim · no, · wrong · stop · that's not · undo · revert · doesn't work
