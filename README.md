# Forge — Claude'un Orkestrası

## Misyon
Forge, Claude'un bir projeye bağlı yardımcı aracı değil, orkestrasıdır. Tek bir hedefi yoktur; araştırma, CAD, kod ve her proje için kullanılır.

**Şef: Claude (pahalı model)**
- Soruyu alt sorulara böler.
- "Yeterli" olmanın ölçütünü koyar.
- Son yargıyı verir.

**Çalgıcılar: betikler, Haiku alt-ajanları, makale-okuyucu (ucuz)**
- Yüzlerce kaynağı paralel tarar.
- Alıntıları doğrular.
- Bilgiyi damıtır.

**Amaç:** Claude'un "birkaç kaynakla sınırlı ve pahalı" çalışmasını genişletmek ve ucuzlatmak. Claude'un bağlamına yalnız damıtılmış, kanıtlı özet girer.

Kapsam kaydı: kullanıcı kararı, 2026-10-25. Önceki dar kapsam ("akademik araştırmanın yan aracı") bir yanlış anlamaydı.

## İlkeler
- **Şef yargılar, çalgıcı toplar.** Ucuz model kesin hüküm vermez. Ucuz katman yalnız kesin olarak alakasız olanı atar; şüpheli olan yukarı çıkar.
- **Çıktı özettir, döküm değildir.** Bağlam bütçesi ölçülür.
- **Dürüst durum.** "Bulunamadı" ile "aranamadı" ayrıdır. Sessiz veri kaybı yasaktır; her aşama girdi, çıktı ve düşen sayısını loglar.
- **Kanıt doğrulanabilir.** Alıntılar kaynakta kodla kontrol edilir.
- **Genişlik kalite değildir.** Kalite, insan yapımı altın setlerle ölçülür.

## Kabul protokolü (v3)
1. **Ön kayıt:** `ONKAYIT-<deney>.md` dosyası (metrik, eşik, n, k, öldürme kriteri) ilk kod ya da koşu commit'inden ÖNCE commit edilir.
2. **İstatistik:** eşik "Wilson alt sınırı" ya da "eşli fark + işaret testi" biçimindedir. n < 30 ise sonuç "pilot, karar yok" olur. Stokastik sistemde k ≥ 3.
3. **Taban çizgisi:** aynı iş Claude'un bugünkü yöntemiyle, tek bir Opus ajanıyla ölçülür.
4. **Altın set:** mümkünse insan yapımı (survey kaynakçaları, küratörlü listeler, hoca). Sistemi yazanın erişimi dışında tutulur.
5. **Denetçi:** sistemi yazandan farklı bir model ya da kullanıcı.
6. **Karar:** KABUL ya da RED.
7. **Regresyon:** kabul testi kalıcıdır.

## Yapı
- `KAYIT.md` — çalgıcı sicili.
- `ONKAYIT-*.md` — ön kayıtlar.
- `OLUM-KRITERI.md` — Forge'un kendi ölçütü.
- `ISTEK-GUNLUGU.md` — fikirler.
- `araclar/<ad>/` — çalgıcılar.
- `orkestra/` — şef–çalgıcı hattı.
- `gelistirme/` — öneriler, yargılar, ölçümler.
- `HAKEM-RAPORU.md` — ilk bağımsız değerlendirme.
