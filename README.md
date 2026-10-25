# Forge

Claude'un (ve ajanlarının) kullanacağı araçların yapıldığı, kanıtlandığı ve sisteme alındığı merkez. Tüm geliştirmeler burada toplanır.

> **Yürürlükte:** `MORATORYUM.md` (pilotlar önce, yeni araç yok) ve `OLUM-KRITERI.md` (Forge'un kendisi 2026-11-22'de ölçülür).

## Felsefe
- **Pahalı model yalnız yargı yapar.** Tekrarlı iş koda ya da ucuz modele gider.
- **Araç özet döndürür, döküm döndürmez.**
- **Dürüst durum bildirir.** "Bulunamadı" ile "aranamadı" ayrı şeylerdir. Sessiz veri kaybı yasaktır.
- **Kanıt doğrulanabilir.** Alıntılar kaynakta kodla kontrol edilir.
- **Araç ancak elle 3 kez tekrarlanmış bir işten doğar.**

## Kabul protokolü (v2, 2026-10-25, YARGI.md'ye göre)
1. **Ön kayıt:** `ONKAYIT-<araç>.md` dosyasına metrik, eşik, n, k ve öldürme kriteri yazılır. **Bu dosya ilk kod ya da koşu commit'inden ÖNCE commit edilir.**
2. **Eşik biçimi:** "Wilson alt sınırı ≥ X" ya da "eşli fark". **n < 30 ise sonuç "pilot, karar yok" olur.** Stokastik araçta k ≥ 3 koşu yapılır.
3. **Taban çizgisi:** aynı iş bugünkü yöntemle de ölçülür.
4. **Bağımsız ölçüm:** denetçi ya farklı bir model ailesidir ya da öğrencinin kendisidir. Değerlendirme seti aracı yazanın erişiminde olamaz.
5. **Karar ikilidir: KABUL ya da RED.** ŞARTLI yalnız ön kayıtta bir rol eşiği yazılmışsa verilebilir.
6. **Regresyon:** kabul testi kalıcıdır; her değişiklikten sonra yeniden koşulur.

## Yapı
- `KAYIT.md` — araç sicili.
- `ISTEK-GUNLUGU.md` — araç fikirleri (moratoryum süresince yalnız burada durur).
- `ONKAYIT-*.md` — ön kayıtlar.
- `araclar/<ad>/` — her aracın kodu, SPEC'i ve testleri.
- `gelistirme/` — öneri raporları, yargı ve ölçümler.
- `HAKEM-RAPORU.md` — ilk bağımsız hakem değerlendirmesi.
