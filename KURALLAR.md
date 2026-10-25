# Forge Kuralları

Tek kaynak. Her kural bir satırdır, kökeni parantezde. Yeni kural buraya eklenir; README ve DEVAM buraya atıf yapar.
Kural değişikliği tarihle yazılır, eskisi silinmez, üstü çizilir.

## 1. Yetki
1. Forge içinde kod, ön kayıt, deney, alt-ajan ve yerel commit **sormadan** yapılır (kullanıcı, 2026-10-25).
2. **Sorulur:**
   - dışa giden işler (push, yayın, e-posta, dış servise veri),
   - geri alınamaz işler (silme, force),
   - tek seferde > $10 ağırlık (2026-10-25).
3. Rapor yalnız kilometre taşında verilir, her adımda verilmez (2026-10-25).
4. Forge dışındaki projelerde eski kural geçerli: açık komut olmadan kurulum, dosya ya da komut yok. "Devam" eylem izni değildir (2026-10-05).
5. Claude Code ayarları ve kullanıcının bilgisayar düzeni Forge dışıdır; önce sorulur (ilerleme barı, 2026-10-25).

## 2. Kapsam
1. Forge, Claude'un orkestrasıdır. **Ana kullanım:** "bana yüksek potansiyelli bir fikir / makale ver" → arkada ucuz çalgıcılar geniş tarar ve doğrular, Claude damıtılmışı yargılar (2026-10-25).
2. Tek bir projenin yardımcısına indirgenmez. Ama bir uygulama oturmadan ikincisine geçilmez (2026-10-25).
3. Yeni iş seçimi ölçüme dayanır. Elde tek veri var diye ("CAD ölçülmüştü") genelleme yapılmaz; önce ilgili payı ölç (CAD sapması, 2026-10-25).
4. Forge'un kendine harcadığı (forge-meta), gerçek kullanımın 3 katını aşmaz (OLUM-KRITERI K3).
5. "Bağımsız" istenen analizde sentez ve öneriye mevcut projeler (CAD vb.) sokulmaz (2026-10-24).
6. Plan ya da tasarımdan önce fizibilite yapılır: ihtiyaç, en yakın rakip, fiziksel tavan, erişim. Olumsuz bulgu başta söylenir (2026-10-22).

## 3. Çalışma düzeni
1. **Paralel varsayılan.** Bir iş yalnız (a) veri bağımlılığı ya da (b) paylaşılan kaynak çakışması varsa bekler; "alışkanlık" sebep değildir (2026-10-25).
2. Çakışan kaynaklar:
   - arXiv: IP başına sınır; WebFetch de bu bilgisayardan gider.
   - Anahtarsız OpenAlex / S2.
   - Süresi ölçülen deneyler.
   - Abonelik limiti.
   Çakışma varsa önce yol değiştirilir: ayrı venv, worktree, ağsız iş, başka veri kaynağı (2026-10-25).
3. arXiv kullanan koşu, arXiv'e giden başka iş yokken tek başına koşar. Ölçüldü: tek başına 4029, eşzamanlı 790 kayıt (D2, 2026-10-25).
4. Hız sınırı **atlatılmaz**: IP değiştirme yok, bot duvarı aşma yok. Meşru yol aranır (toplu veri, anahtar) (2026-10-25).
5. Uzun koşudan önce, bilgisayar kapanırsa nereden devam edileceği `DEVAM.md`'ye yazılır.
6. Çalışan bir hattın kodu, koşu sürerken aynı çalışma ağacında değiştirilmez; yeni sürüm için worktree açılır (v1, 2026-10-25).
7. Ajanlar commit etmez; çıktılarını Claude inceler ve commit eder. Ajan raporundaki iddia kodla ya da sayıyla doğrulanmadan sicile girmez.

## 4. Deney disiplini
1. Ön kayıt (metrik, eşik, n, öldürme kriteri) ilk koddan ve koşudan **önce** commit edilir.
2. Eşikler **farka** göre yazılır, mutlak orana göre değil (K5 dersi: fark yokken mutlak eşik "ARADA" verdi).
3. n < 30 → "pilot, karar yok". Stokastik sistemde k ≥ 3.
4. Taban çizgisi, Claude'un bugünkü yöntemidir. Taban gerçekten o işi yapıyor mu, önce tek denemeyle bakılır (A0 hiç arama yapmadı, 2026-10-25).
5. Altın set insan yapımıdır ve ayrı repoda durur. Sistemi yazan ya da koşan oturum içeriğini görmez; yalnız hash'i ve sayıları görür.
6. Kod **dondurulur** (git etiketi), sorular ancak ondan sonra açılır. Sonucu gördükten sonra ayar yapılmaz.
7. Ön kayıt sonradan yalnız **tarihli ek** ile açıklanır ya da değiştirilir; ek, veri görülmeden yazılır ve eşik gevşetilmez.
8. Denetçi, sistemi yazandan farklı bir model ya da kullanıcıdır. Aynı aileden denetçi şerh olarak yazılır.
9. Ölçüm aracı da test edilir: veri biçimi uyuşmazlığı sessiz kayıp yaratır (`arxiv` ≠ `arxiv_id`: 953/4089 kimlik kaçıyordu, 2026-10-25).
10. Tahmin, sonuçtan önce commit edilir (`TAHMIN-*.md`).
11. Fiziksel ya da gösterim deneyi önerilmeden önce sorulur: ne kanıtlıyor, çürütülebilir mi, başarısızlığı gösteriyor mu, kanıt zincirine oturuyor mu (2026-10-22).

## 5. Dürüst durum
1. "Bulunamadı" ile "aranamadı" ayrıdır. Sessiz veri kaybı yasaktır; her aşama girdi, çıktı ve düşen sayısını loglar.
2. Bilinen sınırlamalar (anahtarsız koşu, Türkçe soru, altın kalite kontrolü…) raporda açıkça yazılır.
3. Aynı hata ikinci kez yapılmaz: kök neden bir kerede çözülür ve aynı sınıftaki diğer yerler de taranır. Kontrol etmeden "oldu" denmez (2026-10-23).

## 6. Kullanıcıyla iletişim
1. Kısa ve basit konuşulur: önce 3–5 satırlık öz, detay istenirse verilir (2026-09-28).
2. Harcama **token** ile anlatılır; liste fiyatı yalnız "ağırlık" olarak yanına yazılır, karşılaştırma yüzdeyle yapılır. Kullanıcı aboneliktedir; para çekilmez, limit tükenir (2026-10-25).
3. Kilit kararlar kısaca "neden"iyle anlatılır; proje kara kutu kalmaz (2026-10-05).
4. Üretilen sayfa ya da görsel hemen açılıp gösterilir; yalnız link verilmez (2026-10-17).
5. Dış repolara katkıda `Co-Authored-By` ve "Generated with" satırları yazılmaz (2026-10-16).
