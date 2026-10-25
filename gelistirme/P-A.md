# Forge geliştirme önerileri — Mercek A: bilimsel metodoloji ve değerlendirme geçerliliği

Tarih: 2026-10-25. Okunanlar: `forge/README.md`, `KAYIT.md`, `HAKEM-RAPORU.md`, `araclar/makale-okuyucu/{README,SPEC}.md`, `araclar/maliyet-sayaci/SPEC.md`, `akademik-bosluk/gapmine/karsilastirma/DENETIM.md`, `altin/gold.json` (yapısı), `git log` (3 commit, hepsi 2026-10-25 13:13–13:22). Hiçbir dosya değiştirilmedi. Satır numaraları bu tarihteki dosyalara göredir.

Güven aralıkları bu rapor için hesaplandı (Wilson, %95). Gerekli örneklem sayıları aynı hesaptan.

---

## Özet tablo

| # | Öneri | Hedeflediği kendini kandırma biçimi | Maliyet |
|---|---|---|---|
| 1 | Zorunlu ön kayıt dosyası + analiz planı + ŞARTLI rol eşiği | Eşiğin sonuçtan sonra yazılması, kaçış kapısı | 2 sa / ~40k token |
| 2 | Altın set karantinası ve insan kaynaklı altın | Altın setin ajan çıktısı olması ve yazara sızması | 6 sa / ~150k token |
| 3 | Yargıç bağımsızlığı: farklı model ailesi + insan kalibrasyonu (TPR/TNR) | Aynı modelin kendini onaylaması | 3 sa / ~100k token + ~$5 dış API |
| 4 | Eşikler güven aralığıyla, n tabanı, k≥3 koşu, önceden güç hesabı | Gürültüyü sinyal sanmak | 3 sa / ~60k token |
| 5 | Üçlü taban çizgisi + getirme düzeyinde canary + negatif kontrol | "Bir şey buluyor" yanılsaması | 4 sa / ~120k token |
| 6 | Tautolojik eşik yerine görev-sonuç metriği (yorum sadakati, aşağı akış A/B) | Ölçülebileni ölçüp amacı ölçmemek | 5 sa / ~200k token |
| 7 | KANIT.md şeması + regresyon koşusu + transkript okuma kotası | Kabulden sonra sessiz bozulma | 3 sa / ~80k token |

Toplam: ~26 saat, ~750k token (+ ~$5 dış API). Bunun ~12 saati insan emeği (etiketleme, altın kürasyonu) ve ajana devredilemez; öneri 2, 3 ve 6'nın asıl maliyeti budur.

---

## 1. Zorunlu ön kayıt dosyası: eşik + analiz planı + ŞARTLI için rol eşiği, koşudan önce commit

### (a) Sorun ve kanıt
- Protokol "eşik önceden yazılır … sonuçtan sonra değiştirilemez" diyor (`README.md:14`) ama bunu zorlayan hiçbir mekanizma yok. Sonuç: gapmine eşiği sonuçtan ~8 saat sonra yazıldı (`HAKEM-RAPORU.md:17-20`), KAYIT bunu kabul ediyor (`KAYIT.md:4`).
- ŞARTLI kararı için rol eşiği yazılmıyor; bu yüzden iki eşiği de geçemeyen araç "ŞARTLI" diye kurtarıldı (`HAKEM-RAPORU.md:21-24`). Protokolde ŞARTLI'nın tanımı "belli bir rolde işe yarıyor" (`README.md:18`) — bu, sonuçtan sonra herhangi bir role uyarlanabilir.
- maliyet-sayaci'nin karşılaştırma büyüklüğü sonuçtan sonra değişti (`HAKEM-RAPORU.md:25`). Değişiklik makul; sorun, "keşifsel düzeltme" ile "ön kayıtlı test"in aynı satırda, ayrımsız durması.
- KAYIT'taki tek önlem "eşikler git commit'iyle zaman damgalanacak" (`KAYIT.md:5`). Git commit tarihi yazar tarafından ayarlanabilir; tek başına kanıt değil. Üstelik şu anki üç commit'in üçü de hakem raporundan sonra, aynı 10 dakikada atılmış; hiçbiri bir koşudan *önce* atılmış eşik commit'i değil.
- Analiz planı yok: hangi metrik birincil, hangi test, hangi n, kaç koşu — hiçbiri yazılmıyor. Nosek ve ark. (2018) ön kaydın amacını tam bu ayrım için tanımlar: "post-hoc bulgu" ile "sınanmış öngörü"yü geri görüş yanlılığına karşı ayırmak.

### (b) Öneri
Her araç için koşudan önce `kanit/<arac>/ONKAYIT-v<N>.md` dosyası; sabit şablon, boş alan bırakılamaz:
1. **İddia** (tek cümle): araç X işini Y ölçütünde Z'den iyi yapar.
2. **Birincil metrik** (tek tane) ve **ikincil metrikler** (en çok 3). Birincil geçmezse karar RED; ikinciller yalnız yorum.
3. **Eşik**: sayı + güven aralığı kuralı (bkz. öneri 4).
4. **ŞARTLI rolü ve rol eşiği**: ŞARTLI verilebilecek tek rol ve o rolün sayısal eşiği burada yazılır. Yazılmamışsa ŞARTLI verilemez.
5. **Örneklem**: n, nasıl seçilecek, kaç koşu (k), altın setin sürüm hash'i.
6. **Analiz planı**: hangi test / aralık, tek yönlü mü, karşılaştırılan taban çizgileri.
7. **Öldürme kriteri**: hangi sonuçta araç arşive gider.
8. **Sapma kuralı**: plandan her sapma sonuç dosyasında "KEŞİFSEL" etiketiyle ayrı bölümde yazılır; ön kayıtlı karar etkilenmez.

Zorlama:
- Dosyanın SHA-256'sı `KAYIT.md`'deki satıra yazılır; ölçüm raporu (`KANIT.md`) aynı hash'e atıf yapar. Hash uyuşmuyorsa karar geçersiz.
- Koşu betiği (`run_*.py`) başlarken ONKAYIT hash'ini log'a basar; log zaman damgası koşunun ön kayıttan sonra olduğunu gösterir. Bu, git tarihine göre daha zor oynanır çünkü iki bağımsız iz (git + koşu log'u) tutmalıdır.
- KAYIT.md'ye sütun: "ONKAYIT hash / commit". Boşsa durum en çok "Kuruldu" olabilir, "KABUL/ŞARTLI" olamaz.

Geriye dönük: gapmine ve maliyet-sayaci için bugünkü eşikler "sonradan yazıldı" etiketiyle kalır; yeni sürüm ölçümünden önce yeni ONKAYIT yazılır.

### (c) Beklenen kazanç
Kabul kararlarının tamamı öngörü testine dönüşür; "ŞARTLI" kaçış kapısı kapanır; hakemin "onay damgası" eleştirisi (`HAKEM-RAPORU.md:157`) somut olarak cevaplanır. Ek olarak her ONKAYIT, öneri 4'teki güç hesabını zorladığı için anlamsız n'li ölçümler (3 iddialık eşik) baştan elenir.

### (d) Maliyet
Şablon + KAYIT sütunu + koşu betiklerine hash log satırı: ~2 saat, ~40k token. Araç başına ONKAYIT yazımı: ~20 dk.

### (e) Önceden kaydedilebilir metrik + eşik
- **Metrik:** KABUL/ŞARTLI/RED kararlarının, karardan önce commit'lenmiş ve hash'i uyuşan ONKAYIT'a sahip olanlarının oranı.
- **Eşik:** 30 gün içinde verilen kararlarda **%100**. Tek istisna yok; istisna gereken karar "Kuruldu / beklemede" kalır.
- **İkincil:** ŞARTLI kararlarının hepsinde rol eşiği ONKAYIT'ta önceden yazılı (%100).

### (f) Öldürme kriteri
30 gün içinde ONKAYIT'lı hiçbir karar verilmezse (ya da ilk üç ONKAYIT'ın üçü de sonradan "sapma" bölümüyle fiilen yeniden yazılırsa) mekanizma ritüele dönmüştür: şablon tek sayfalık kontrol listesine indirilir ve Forge'un kendisi için öneri 7'nin sonundaki genel öldürme kriteri işler.

---

## 2. Altın set karantinası ve insan kaynaklı altın: yazar göremez, held-out tek kullanımlık, kaynak ajan değil

### (a) Sorun ve kanıt
- Altın set aracın kendi klasöründe: `gapmine/karsilastirma/altin/gold.json` (`HAKEM-RAPORU.md:58`). v2'yi yazan ajan, kaybolan makaleleri adıyla sayan DENETIM'i okudu (`HAKEM-RAPORU.md:59`, `KAYIT.md:10`). Gelecekteki "recall %80" sonucu ezber olabilir (`HAKEM-RAPORU.md:169`).
- Altın setin kaynağı ajan çıktıları: "Altın set olum-testi raporlarından çıkarıldı" (`DENETIM.md:58`). Yani ölçülen "ajanla uyuşma", "doğruluk" değil (`HAKEM-RAPORU.md:29`). gold.json'da bile 92 makalenin bir kısmının arXiv id'si `null` (ör. K1 "KernJC", K2 "RingGuard", K5 "Mariposa"); altın setin kendisi tam çözümlenmemiş.
- makale-okuyucu'nun duman testi makalesi (2501.08156) altın setteki bir K7 öldüreni (`HAKEM-RAPORU.md:115`); kabul ölçümüne sızmaya aday.
- README `kanit/` klasörünü "ortak altın setler" diye tanımlıyor (`README.md:25`) ama klasör yok (`HAKEM-RAPORU.md:35`); yani karantina fiziksel olarak da yok.
- Literatür: Jacovi ve ark. (EMNLP 2023) test verisini düz metin olarak paylaşmamayı, şifreli ve türev yasaklı tutmayı; Sainz ve ark. (EMNLP 2023) kirlenmeyi benchmark başına ölçmeyi; GSM1k (Scale AI) held-out setin yalnız küçük bir kısmını açmayı öneriyor. Anthropic'in ajan eval yazısı da paylaşılan durumdan (ör. git geçmişi) sızan "haksız avantaj" örneği veriyor.

### (b) Öneri
**Fiziksel karantina**
- `kanit/` forge deposunun *dışında*, ayrı bir klasör ve ayrı git deposu olsun (ör. `Projeler/forge-kanit/`). Araç yazan ajanlar bu klasöre erişemez: Claude Code oturumu `forge/araclar/<arac>` altında açılır, `--add-dir` ile kanıt klasörü verilmez. Denetçi oturumu ise yalnız `kanit/` + aracın CLI'ını görür, kaynak kodu görmez.
- Her altın set iki parça: **gelistirme (açık)** ve **held-out (kapalı)**. Held-out şifreli zip (parola yalnız kullanıcıda); her araç sürümü için bir kez açılır, koşulur, sonuç yazılır, held-out "yakıldı" sayılır ve sonraki sürüm için en az yarısı yenilenir. Held-out koşusu ONKAYIT'ta (öneri 1) ilan edilen tek koşudur.
- Her altın öğeye `kaynak` alanı: `insan-yayin | atif-grafi | kullanici-elle | ajan`. `ajan` kaynaklı öğe kabul ölçümünde sayılmaz, yalnız geliştirme setinde durur.

**İnsan yapımı, ajandan bağımsız altın kaynakları** (gapmine ve olum-testcisi için)
1. **Survey / SoK makalelerinin ilgili-çalışma tabloları.** İnsan yazarların, hakemden geçmiş kürasyonu. Örnek: K5 için Dafny/Verus kanıt kararlılığı üzerine bir SoK'un atıf listesi; K9 için LLM-CAD survey'inin karşılaştırma tablosu. İddia → "bu survey'in tablo 2'sindeki N makale" şeklinde kurulur; recall bu N üzerinden ölçülür.
2. **Atıf grafı (OpenAlex `cites`/`cited_by`).** Bilinen bir çekirdek makaleyi (ör. Mariposa) kim alıntıladı listesi, yazarların kendi kararıdır; ajan üretmedi. "Tohum makaleye atıf yapan ve başlığında X geçen" kümesi altın olur.
3. **Hakem / program komitesi kaynakları.** OpenReview'daki açık hakem raporlarında "missing related work: …" satırları; konferans "related work" ödevleri. Küçük ama tamamen bağımsız.
4. **Kullanıcının danışmanı/hocası.** 5 iddia için "bilen biri" 10 dakikada 3–5 makale yazar. En pahalı ama en geçerli kaynak; aynı zamanda hoca ortaklığı hedefiyle örtüşüyor (`HAKEM-RAPORU.md:108`).
5. **Kürasyonlu bibliyografyalar** (awesome-* listeleri, alan wiki'leri, dergi "editor's picks"). Ajan değil, topluluk yapımı; blog/GitHub kaynaklı öldürenleri (`DENETIM.md:62-67`) de kapsar.

**makale-okuyucu için** altın: (i) yazarların kendi "highlights / key findings" metni (yayıncı sayfası, OpenReview özeti), (ii) kullanıcının zaten okumak zorunda olduğu 5 makale için elle yazdığı 10'ar soru-cevap (sayfa numaralı), (iii) ders kitaplarındaki klasik makaleler için mevcut insan özetleri. Duman testi makaleleri held-out'tan düşürülür.

### (c) Beklenen kazanç
Recall sayısı "ajanla uyuşma" olmaktan çıkar, gerçek kapsam ölçümü olur. Sızıntı yoluyla şişen sürüm başarısı önlenir. Hakemin "yeni ve görülmemiş altın set" şartı (`KAYIT.md:17`) tanımlı bir prosedüre bağlanır.

### (d) Maliyet
Klasör/depo/zip düzeni + `kaynak` alanı: 1 saat, ~20k token. 10 iddia için insan kaynaklı altın kürasyonu: ~4 saat insan (survey tabloları + atıf grafı), ~100k token ajan yardımı (yalnız kaynak getirme, etiketleme değil). makale-okuyucu 5 makale × 10 soru: ~1,5 saat insan. Toplam ~6 saat, ~150k token.

### (e) Önceden kaydedilebilir metrik + eşik
- **Metrik 1 (köken):** Kabul ölçümünde kullanılan altın öğelerin `kaynak ≠ ajan` oranı. **Eşik ≥ %80**, kalan %20 yalnız `kullanici-elle`.
- **Metrik 2 (sızıntı testi):** Aynı araç sürümünün gelistirme-set recall'u ile held-out recall'u arasındaki fark. **Eşik: fark ≤ 10 puan.** Fark > 10 puan ise sürüm ezber şüphesiyle RED (GSM1k mantığı: açık sette daha iyi olmak kirlenme göstergesidir).
- **Metrik 3 (erişim):** Araç yazan oturumun transkriptinde `kanit/held-out` yolu geçmez (maliyet-sayaci'nin gizlilik sözleşmesine benzer biçimde yalnız yol adı taranır). **Eşik: 0 geçiş.**

### (f) Öldürme kriteri
İki hafta içinde 10 iddianın en az 5'i için insan kaynaklı altın kurulamazsa (survey yok, atıf grafı boş, hoca yok), "bağımsız altın" bu alan için ulaşılamazdır; o zaman gapmine için recall eşiği bırakılır ve araç yalnız öneri 6'daki aşağı-akış A/B ile değerlendirilir. Ayrıca üç ardışık sürümde gelistirme–held-out farkı ≤ 3 puan kalırsa held-out yenileme sıklığı yarıya indirilir (karantina maliyeti kazancı aşıyor demektir).

---

## 3. Yargıç bağımsızlığı: farklı model ailesi + insan kalibrasyonu (TPR/TNR ayrı), kör brif

### (a) Sorun ve kanıt
- Denetçi aynı oturumda aynı model (`HAKEM-RAPORU.md:27`); brifi aracı yazan asistan yazdı (`HAKEM-RAPORU.md:28`). Protokol "aracı yazmayan bir denetçi ajan" diyor (`README.md:15`) — aynı modelin başka kopyası bu tanımı karşılıyor ama bağımsızlığı sağlamıyor.
- DENETIM'in LLM doğruluğu ölçümünde "denetçi özetleri kendisi okudu" (`DENETIM.md:125`); yani Haiku'nun kararını başka bir Claude modeli puanladı. Yanlış YES %23 bulundu (`DENETIM.md:130`) — insan okusa bu oran farklı çıkabilir, bilmiyoruz.
- Literatür: Panickssery, Bowman ve Feng (2024) LLM yargıçların kendi çıktılarını tanıyıp kayırdığını ve tanıma gücü arttıkça kayırmanın arttığını gösterdi. 2025 takip çalışması (arXiv 2504.03846) zararlı kendi-tercihin özellikle yargıcın kendisinin kötü cevap ürettiği durumlarda ortaya çıktığını buldu — yani tam da aracın zorlandığı sınır vakalarında. Anthropic'in ajan eval yazısı model tabanlı yargıç için "insan yargıçlarla kalibrasyon gerektirir" diyor. Husain'in LLM-yargıç yöntemi ham uyuşma yerine TPR ve TNR'yi ayrı raporlamayı, yargıç doğrulaması için etiket başına 30–50 örnek ve toplamda 60'ın altına inmemeyi öneriyor ("60'ın altında güven aralıkları çoğu zaman fazla geniş").

### (b) Öneri
1. **Üçlü yargıç:** Her kabul ölçümünde (i) aracın kendi modeli dışında bir aile (Gemini / GPT, ücretsiz katman yeterli; abonelik yoksa 100 kararlık örnek ~$1–2), (ii) aynı aile ama ayrı oturum ve kör brif, (iii) **insan** (kullanıcı). İnsan, her kabul için en az **30 Pozitif + 30 Negatif** öğeyi kör etiketler (öğe sırası karıştırılmış, aracın kararı gizli).
2. **Kör brif:** Denetçinin brifi SPEC'teki "Kabul" bölümünden otomatik üretilir (şablon), aracın yazarı tarafından yazılmaz. Brif denetçiye aracın kaynak kodunu değil yalnız CLI'ı ve ONKAYIT'ı verir.
3. **Yargıç raporu:** İnsan etiketine göre her model yargıcın TPR ve TNR'si ayrı yazılır; Cohen κ eklenir. Model yargıç yalnız bu eşiği geçtiyse insan yerine ölçek büyütmede kullanılabilir (Husain'in dev/test ayrımı: yargıç ayarı dev'de, son sayı test'te bir kez).
4. **Kendi-tercih kontrolü:** Aynı 60 öğede aynı-aile yargıç ile farklı-aile yargıcın insanla uyuşması karşılaştırılır. Fark anlamlıysa (öneri 4'teki aralık kuralıyla) aynı-aile yargıcın kararları kabul ölçümünden düşer.

### (c) Beklenen kazanç
"Ajanla uyuşma" yerine "insanla uyuşma" ölçülür; kendi-tercih yanlılığı sayısal olarak izlenir; model yargıç yalnız kanıtlanmış kalibrasyonla ölçek büyütür. Bu, hakemin en büyük risk dediği "kendi kendini doğrulayan döngü"nün (`HAKEM-RAPORU.md:154-157`) doğrudan kırılma noktası.

### (d) Maliyet
Şablon brif + yargıç raporu betiği (TPR/TNR/κ): 1,5 saat, ~40k token. Kabul başına insan etiketleme 60 öğe: ~1 saat (makale özeti okuma hızında ~1 dk/öğe). Dış aile yargıç: ~$1–5/kabul. İlk kurulum toplamı ~3 saat, ~100k token.

### (e) Önceden kaydedilebilir metrik + eşik
- **Metrik:** Kabul ölçümünde kullanılan model yargıcın, 30P+30N insan etiketine göre **TPR ≥ 0,85 ve TNR ≥ 0,85** (ikisi birden; Wilson alt sınırı ≥ 0,70). Geçmeyen yargıcın kararları sayılmaz; insan etiketi tek başına karar verir.
- **İkincil:** aynı-aile vs farklı-aile yargıcın insanla κ farkı raporlanır; fark > 0,15 ise aynı-aile yargıç o araç için yasaklanır.

### (f) Öldürme kriteri
Ardışık iki araçta aynı-aile ve farklı-aile yargıç insanla aynı düzeyde uyuşursa (κ farkı ≤ 0,05) farklı-aile yargıç zorunluluğu kaldırılır; insan kalibrasyonu (30+30) kalır. Tersine, insan etiketleme bir kabul için 2 saati aşıyorsa öğe sayısı 20+20'ye düşer ama eşik aralığı buna göre genişletilir ve ONKAYIT'a yazılır — sessizce düşürülmez.

---

## 4. Eşikler güven aralığıyla, n tabanı, stokastik araçta k≥3 koşu, önceden güç hesabı

### (a) Sorun ve kanıt
- Bugünkü sayıların aralıkları (bu rapor için hesaplandı, Wilson %95):
  - gapmine çekirdek recall 22/36 = %61 → **[%45, %75]**. "%80 eşiği" ile farkı anlamlı; ama "%61" de bir nokta tahmini değil, 30 puanlık bir bant.
  - Öldürenlerde 3/6 → **[%19, %81]**. Bu sayı hiçbir şey söylemiyor.
  - Hüküm uyumu araç 6/10 → [%31, %83]; kör taban 7/10 → [%40, %89]. İkisi ayırt edilemez; "taban çizgisi aracı yendi" cümlesi de (`DENETIM.md:11`) istatistiksel olarak kurulamaz.
  - olum-testcisi eşiği "bilinen 3 iddiada aynı hüküm" (`KAYIT.md:12`). Üç sınıflı hükümde çoğunluk sınıfı %70 ise 3/3 tesadüfi uyuşma olasılığı **0,34**. Eşik bilgi taşımıyor; hakem de "anlamsız" dedi (`HAKEM-RAPORU.md:197`).
  - "Kör tabanı %70'i yenmek" için tek yönlü binom testiyle: n=10'da 10/10, n=30'da 26/30, n=50'de 41/50 gerekir. n=10 ile pratikte hiçbir araç tabanı anlamlı yenemez.
  - ±10 puanlık aralık için n≈80, ±7,5 için n≈143.
- Stokastiklik: sorgular koşudan koşuya ~%75 değişiyor, aynı iddiada hüküm YARALI→ÖLDÜ çevrildi (`DENETIM.md:107-112`); makale-okuyucu `--force` ile farklı kart veriyor (`README.md:135`). Protokolde k koşu şartı yok (`HAKEM-RAPORU.md:33`).
- Literatür: Miller / Anthropic (2024) eval sonuçlarının hata payıyla ve eşli (paired) farkla raporlanmasını öneriyor; Bowyer ve ark. (2025) birkaç yüz veri noktasının altında CLT aralıklarının belirsizliği "dramatik biçimde düşük" tahmin ettiğini, Bayesci/alternatif frekansçı yöntemlerin kullanılmasını söylüyor. Anthropic'in ajan eval yazısı pass@k ile pass^k'nın k=10'da zıt hikâye anlattığını ve ilk evaller için 20–50 görev öneriyor.

### (b) Öneri
1. **Eşik biçimi:** Her eşik "nokta ≥ X" değil, "**%95 Wilson alt sınırı ≥ X**" ya da taban çizgisiyle "**eşli farkın aralığı 0'ı dışlar**" biçiminde yazılır. n < 200 için CLT yerine Wilson / Clopper-Pearson / bootstrap; ONKAYIT'ta hangisi olduğu yazılır.
2. **n tabanı:** Oran metrikleri için **n ≥ 30 iddia / makale**; yargıç kalibrasyonu için 30+30 (öneri 3); n < 30 ise karar en çok "pilot, karar yok".
3. **k koşu:** Stokastik araçta her öğe **k=3** koşulur. Raporlanan: pass^3 (üçünde de doğru) ve pass@3 ayrı ayrı. Kabul eşiği pass^k üzerinden yazılır, çünkü araç bir karar aracı; "üçte bir tutturdu" kabul değildir. Koşular arası Jaccard DENETIM §4'teki gibi raporlanır.
4. **Önceden güç hesabı:** ONKAYIT'ta tek satır: "Taban p0=…, hedef p1=…, α=0,05 tek yönlü, güç 0,8 → n=…". Hesap küçük bir betikle (`kanit/guc.py`) yapılır; betik olmayınca ONKAYIT eksik sayılır.
5. **Eşli tasarım:** Araç vs taban aynı öğelerde koşulur; fark eşli olarak raporlanır (Miller 2024). İşaret testi için en az 6 uyuşmazlık gerekir (6'sı aynı yönde: p=0,03).

### (c) Beklenen kazanç
"%61 < %80" gibi kararlar aralığa dayanır; 3 iddialık eşikler yazılamaz hale gelir; stokastik araçların tek koşuluk şans sonuçları kabul edilmez. Yan etki: n tabanı, altın set büyüklüğünü (öneri 2) ve insan etiket emeğini (öneri 3) baştan tanımlar — bütçe kararı gerçekçi olur.

### (d) Maliyet
`guc.py` + Wilson/bootstrap yardımcıları + rapor şablonu: ~3 saat, ~60k token. Koşu maliyeti: k=3 araç koşularını üçe katlar; gapmine'da iddia başına ~$0,02 × 3 × 30 iddia ≈ $2 — ihmal edilebilir. Asıl maliyet n=30 için altın set (öneri 2'de sayıldı).

### (e) Önceden kaydedilebilir metrik + eşik
- **Metrik 1:** KABUL/ŞARTLI kararlarının güven aralığı + n + k ile raporlanma oranı. **Eşik %100.**
- **Metrik 2:** Kabul edilen araçlarda held-out'ta **pass^3 ≥ ONKAYIT eşiği**; ayrıca pass@3 − pass^3 farkı raporlanır, > 20 puan ise "kararsız" etiketi ve ŞARTLI'ya düşürme.
- **Metrik 3:** Hiçbir ONKAYIT'ta n < 30 olmaz (0 istisna).

### (f) Öldürme kriteri
n ≥ 30 ve k = 3 şartıyla üç ay içinde hiçbir araç ölçülemiyorsa (altın set kurulamıyor ya da koşu bütçesi yetmiyor), eşik tasarımı Forge'un bütçesine göre fazla büyüktür: n tabanı 20'ye, k 2'ye çekilir ama aralık kuralı korunur ve bu değişiklik KAYIT'a tarihli not olarak düşülür. Aralık kuralından vazgeçilirse öneri boşa çıkmıştır.

---

## 5. Üçlü taban çizgisi + getirme düzeyinde canary + negatif kontrol

### (a) Sorun ve kanıt
- Protokolün taban çizgisi tek: "bugünkü yöntem (ajan veya elle)" (`README.md:13`). Oysa DENETIM, "her şeye YARALI de" diyen sıfır-maliyetli tabanın aracı yendiğini gösterdi (`DENETIM.md:11`, `38-42`). Böyle bir taban protokolde zorunlu olmadığı için ancak denetçi aklına gelince ölçüldü.
- Canary testi önbellek üzerinden girdi, getirme aşamasını test etmedi; asıl sızıntı oradaydı (`DENETIM.md:121`, `93`).
- Negatif kontrol yok: altın seti gerçekten boş olan bir iddia (literatürde gerçekten yok) için aracın "bulunamadı" demesi hiç sınanmadı. "X yok" biçimli iddialarda PARTIAL enflasyonu (`DENETIM.md:138`) tam bu yüzden görünmez kalıyor. makale-okuyucu'da da "bulunamadi kesin yokluk kanıtı değildir" (`README.md:132`) yazılı ama ölçülmüyor.
- Literatür: Anthropic'in ajan eval yazısı "geçmek gerçekten problemi çözmeyi gerektirmeli" ve yargıca "Unknown" çıkışı verilmeli diyor; Husain ham uyuşmanın, her şeye Pass diyen yargıçta bile %95 çıkabileceğini vurguluyor.

### (b) Öneri
Her ONKAYIT'ta üç taban zorunlu:
1. **Önemsiz taban:** çoğunluk sınıfı / rastgele / "hep YARALI". Araç bunu eşli farkla yenemiyorsa RED, başka metriğe bakılmaz.
2. **Ucuz taban:** LLM'siz yöntem — gapmine için arXiv API + BM25 ilk-60; makale-okuyucu için özet + sonuç bölümünü kesip vermek. Araç bunu yenemiyorsa ŞARTLI bile olamaz (pahalı katman katkı sağlamıyor demektir).
3. **Bugünkü yöntem:** ajan (maliyet-sayaci ile gerçek token).

Ek kontroller:
- **Getirme canary'si:** Her held-out iddiaya, arXiv'de gerçekten var olan ama yalnız uygun sorguyla bulunabilen 1 işaretli makale eklenir (ör. DENETIM'in tespit ettiği `io_uring` alt çizgi vakası gibi). Canary ilk-60'a girmezse funnel'ın "kayıp yok" demesi geçersizdir. Önbellek temizlenerek koşulur.
- **Negatif kontrol:** 30 iddianın en az 5'i, insan kaynaklı altın setin boş olduğu bilinen iddialar (ör. kasıtlı saçma birleşimler ya da hoca onaylı "gerçekten yok"). Araç bunlarda ≥1 öldüren/yaralayan üretirse yanlış pozitif sayılır. makale-okuyucu için: makalede olmayan 5 soru → "bulunamadi" beklenir (duman testindeki 2 örnek bunun tohumu, `README.md:112-113`).
- **Funnel korunumu** zaten var (`DENETIM.md:160`); canary bunun "kaybolan altın öğeyi" de yakaladığını kanıtlar.

### (c) Beklenen kazanç
"Araç bir şeyler buluyor" izlenimi, "önemsiz ve ucuz yöntemlerden anlamlı derecede iyi" ölçümüne dönüşür. Negatif kontrol, "X yok" iddialarındaki PARTIAL enflasyonunu ve makale-okuyucu'nun uydurma riskini doğrudan sayıya bağlar.

### (d) Maliyet
Ucuz taban betikleri (BM25 ilk-60; özet-kesme): ~2 saat, ~60k token. Canary + negatif iddia kürasyonu: ~1 saat insan. Koşu: önemsiz. Toplam ~4 saat, ~120k token.

### (e) Önceden kaydedilebilir metrik + eşik
- **Metrik 1:** Araç − önemsiz taban eşli farkının %95 aralığı 0'ı dışlar **ve** araç − ucuz taban farkı ≥ 10 puan (alt sınır ≥ 0).
- **Metrik 2 (canary):** held-out iddialarda canary'nin ilk-60'a girme oranı **≥ %90** (k=3 koşunun pass^3'ü).
- **Metrik 3 (negatif kontrol):** boş-altın iddialarda yanlış öldüren/yaralayan üretme oranı **≤ 1/5**; makale-okuyucu'da olmayan soruya uydurma cevap **0/5**.

### (f) Öldürme kriteri
İki ardışık araçta önemsiz ve ucuz taban hiçbir zaman aracın %10 yakınına gelmiyorsa (araç açık ara üstün), ucuz taban zorunluluğu kaldırılır (önemsiz taban kalır; maliyeti sıfır). Negatif kontrol iddiaları iki haftada kurulamıyorsa (gerçekten boş iddia bulmak zorsa) yerine "yapay negatif" (iki alakasız iddianın birleşimi) konur; o da işe yaramıyorsa bu kontrol düşer ve KAYIT'a yazılır.

---

## 6. Tautolojik eşik yerine görev-sonuç metriği: yorum sadakati ve aşağı-akış A/B

### (a) Sorun ve kanıt
- makale-okuyucu için "uydurma alıntı %0" eşiği tautolojikti, çıkarıldı (`KAYIT.md:11`); ama SPEC'in kabul bölümü hâlâ "alan başına doğrulanmış madde oranı"nı ilk ölçülecek diye yazıyor (`SPEC.md:88-90`). Kod doğrulanmayanı zaten atıyor; bu oran araçla ilgili değil, filtreyle ilgili. README asıl riski kendisi yazıyor: "Doğrulanmış alıntı ≠ doğru yorum" (`README.md:119-121`) ve bunu ölçen hiçbir şey yok.
- Duman testinde "ham madde → doğrulanmış 104 → 103" (`README.md:96`) etkileyici görünüyor ama doğrulanan şey alıntının metinde geçmesi; `text` alanının alıntıyı doğru özetlediği hiç kontrol edilmedi.
- gapmine'da ölçülen "hüküm uyumu" (`DENETIM.md:36`) aracın asıl amacı değil; hakem aracın değerini "ajanın listelemediği makaleleri buldu" ve "~50–100× ucuz" diye tanımlıyor (`HAKEM-RAPORU.md:61-64`). Bu değer ancak aşağı akışta ölçülür: ajan, gapmine'ın kısa listesiyle aynı öldürenlere daha az token'la ulaşıyor mu?
- Yapı geçerliliği (construct validity): ölçülen şey, aracın kabul gerekçesini temsil etmeli. Husain'in yöntemi bu yüzden puan ölçeklerini değil, alan uzmanının ikili Pass/Fail + gerekçe etiketini temel alıyor.

### (b) Öneri
**makale-okuyucu**
1. **Yorum sadakati:** held-out 5 makaleden rastgele 30 doğrulanmış madde; insan kör olarak "text alıntıyı sadık özetliyor mu? (Evet/Hayır + bir cümle gerekçe)" etiketler. Birincil metrik budur.
2. **Soru-cevap doğruluğu:** öneri 2'deki insan yazımı 50 soru (10'u cevabı olmayan). Metrik: doğru cevap oranı + doğru sayfa oranı + "bulunamadi" doğruluğu.
3. **Bütçe metriği:** kart token ≤ 1/10 tam metin, zaten yazılı (`KAYIT.md:11`); kalır.
4. SPEC'teki "alan başına doğrulanmış madde oranı" **teşhis** metriği olarak kalır, kabul metriği olmaz.

**gapmine (ön tarayıcı rolü için rol eşiği)**
5. **Aşağı-akış A/B:** 10 held-out iddiada ajan iki koşul: (A) sıfırdan, (B) gapmine ilk-60 listesi elinde. Eşli ölçüm: insan altınındaki öldüren/yaralayanlara ulaşma oranı ve maliyet-sayaci ile ölçülen gerçek token. ŞARTLI "ön tarayıcı" eşiği buradan yazılır: B, A'nın recall'unu korurken (fark ≥ −5 puan) token'ı ≥ %30 azaltmalı.

**olum-testcisi**
6. "3 iddiada aynı hüküm" yerine: insan altınındaki öldürenleri bulma oranı (n ≥ 30, öneri 4) + negatif kontrol (öneri 5).

### (c) Beklenen kazanç
Eşikler aracın varlık gerekçesini ölçer; "yeşil ama işe yaramaz" sonuç (168 mock testi geçen gapmine gibi, `HAKEM-RAPORU.md:38`) kabul kapısından geçemez. Aşağı-akış A/B ayrıca "araç pahalı ajanı gerçekten ucuzlatıyor mu" sorusuna ilk sayısal cevabı verir; Forge'un felsefesindeki ilk madde (`README.md:6`) ilk kez sınanmış olur.

### (d) Maliyet
İnsan etiketleme: 30 madde sadakat (~30 dk) + 50 soru yazımı (öneri 2'de sayıldı) + A/B sonuçlarının altınla eşlenmesi (~1 saat). Ajan koşuları: A/B için 10 iddia × 2 koşul × ~1M token ≈ 20M token — bu Forge'un bugüne kadarki en pahalı tek ölçümü olur (~$15–25 liste fiyatıyla). Bu yüzden önce 5 iddiayla pilot, pilot anlamlıysa 10'a çık. Kurulum ~5 saat, ~200k token (A/B ajan koşuları hariç).

### (e) Önceden kaydedilebilir metrik + eşik
- **makale-okuyucu birincil:** yorum sadakati **≥ 27/30** (Wilson alt sınırı ≥ 0,75). İkincil: 50 soruda doğru cevap ≥ %85, sayfa doğruluğu ≥ %80, olmayan 10 soruda uydurma 0.
- **gapmine ŞARTLI rol eşiği:** A/B'de recall farkı ≥ −5 puan **ve** gerçek token azalması ≥ %30 (eşli, n=10, işaret testi tek yönlü p < 0,05; 10 çiftin ≥ 9'unda B daha ucuz).
- **olum-testcisi:** öldüren bulma ≥ %80 alt sınırla, n ≥ 30.

### (f) Öldürme kriteri
Yorum sadakati pilotta (ilk 30) ≥ 29/30 çıkarsa ve iki ayrı makale setinde tekrarlanırsa, bu metrik ayırt edici değildir; teşhis metriğine indirilir ve birincil metrik soru-cevaba geçer. A/B pilotunda (5 iddia) B koşulu token'ı hiç azaltmıyorsa ya da recall'u > 10 puan düşürüyorsa, gapmine için "ön tarayıcı" rolü de düşer; araç arşive gider ve 10 iddialık tam A/B yapılmaz (bütçe korunur).

---

## 7. KANIT.md şeması + kalıcı regresyon koşusu + transkript okuma kotası

### (a) Sorun ve kanıt
- Protokolün 5. maddesi "kanıt testi kalıcıdır; her değişiklikten sonra yeniden koşulur" (`README.md:20`), ama `kanit/`, `sistem/` ve hiçbir aracın `KANIT.md`'si yok (`HAKEM-RAPORU.md:35`, `135`). maliyet-sayaci "KABUL (koşullu)" oldu (`KAYIT.md:9`) ve kanıtı yalnız hakem raporunun gövdesinde; hakemin yaptığı bağımsız karşılaştırma regresyon testine çevrilmedi (`HAKEM-RAPORU.md:184`).
- gapmine'ın 168 testi mock ile koşuyor, recall'u ölçmüyor (`HAKEM-RAPORU.md:38`); makale-okuyucu'nun 67 testi de öyle (`README.md:68`). Yani "testler yeşil" ile "kanıt geçerli" arasında bağ yok.
- Hakemin maliyet tablosu bulgusu (`HAKEM-RAPORU.md:122-126`): DENETIM'in token oranı yanlıştı ve bunu kimse transkripte bakmadan fark etmedi. Anthropic'in ajan eval yazısı aynı noktayı tekrarlıyor: "Read the transcripts!" — graderların çalıştığını ancak çok sayıda transkript ve not okuyarak bilirsiniz; regresyon evalleri ~%100 geçmeli ve olgunlaşan yetenek evalleri regresyona "mezun" olmalı.

### (b) Öneri
1. **`KANIT.md` şeması** (her araç, zorunlu alanlar): ONKAYIT hash'i; altın set sürüm hash'i (held-out "yakıldı" tarihi); n, k; taban çizgileri ve eşli farklar; yargıç TPR/TNR; sonuç + aralık; karar; KEŞİFSEL bölüm; "bir sonraki held-out için gereken yenileme". Boş alan = karar geçersiz.
2. **Regresyon koşusu:** kabul edilen araç için `kanit/<arac>/regresyon.py` — geliştirme setinde (açık) k=1 koşu, çıktı tek satır (tarih, commit, metrik, aralık). `araclar/<arac>/` altını değiştiren her commit'ten sonra koşulur; sonuç `KANIT.md`'ye eklenir. maliyet-sayaci için ilk regresyon: hakemin `usage_check.py` karşılaştırması (19/19 ajan birebir) aynen test edilir.
3. **Mezuniyet kuralı:** üç ardışık regresyonda metrik eşiğin ≥ 10 puan üstünde kalırsa o test "regresyon" sayılır ve held-out ölçümü yalnız büyük sürümde tekrarlanır (eval doygunluğu).
4. **Transkript okuma kotası:** her kabul ölçümünde insan, aracın ya da yargıcın en az **10 kararının** ham gerekçesini okur ve "adil mi?" diye işaretler (yargıç yanlış mı reddetti, araç mı yanlış?). Bunun için ham LLM cevabının saklanması şart (DENETIM bulgu 7, `DENETIM.md:154`: gapmine ham cevabı saklamıyor; makale-okuyucu `llm_calls` tablosunda saklıyor mu, SPEC'ten net değil — şema zorunlu kılsın).

### (c) Beklenen kazanç
Kabul bir kerelik tören olmaktan çıkar; sessiz bozulma (ör. sorgu regex'inin değişmesi) yakalanır; "testler yeşil" ile "kanıt geçerli" ayrılır. Transkript kotası, hakemin yakaladığı türden (yanlış maliyet tablosu) hataların içeriden yakalanma şansını verir.

### (d) Maliyet
Şema + regresyon betiği iskeleti + KAYIT bağlantısı: ~3 saat, ~80k token. Araç başına regresyon ilk yazımı ~1 saat. Her koşu: dakikalar, < $0,5.

### (e) Önceden kaydedilebilir metrik + eşik
- **Metrik 1:** `araclar/<kabul edilmiş arac>/` değiştiren commit'lerin, 24 saat içinde eklenmiş regresyon satırı olanlarının oranı. **Eşik ≥ %90.**
- **Metrik 2:** Regresyon geçme oranı **≥ %95** (Anthropic: "nearly 100%"); altına düşen araç otomatik "ŞARTLI (regresyon kırık)" olur.
- **Metrik 3:** Her KANIT.md'de "okunan transkript" alanı ≥ 10 ve en az 1 "adil değil" bulgusu kayıt altında (0 bulgu, okunmadığının işaretidir; bu durumda örnek 20'ye çıkar).

### (f) Öldürme kriteri
İki ay içinde regresyon hiçbir gerçek gerilemeyi yakalamadıysa **ve** transkript kotası hiçbir "adil değil" bulgusu üretmediyse, ikisi de maliyetine değmiyordur: regresyon yalnız büyük sürümlerde koşulur, kota 5'e iner. Tersine, bu mekanizmalar ilk iki ayda kabul edilmiş bir aracın eşiğin altına düştüğünü gösterirse, öneri kendini kanıtlamıştır ve KAYIT'a tarihli not düşülür.

---

## Forge'un kendisi için öldürme kriteri (önerilerin üstünde)

Hakem "Forge'a girip kabul edilmiş araç sayısı 0" ve "meta-iş asıl işi yiyor" dedi (`HAKEM-RAPORU.md:9`, `158-165`). Bu yedi öneri de meta-iştir; aynı tuzağa düşebilir. Bu yüzden ön kayıtla şu yazılmalı:

- **60 gün** içinde, öneri 1–4 uygulanmış biçimde en az **1 KABUL ve 1 RED** kararı çıkmazsa; ya da maliyet-sayaci ile ölçülen Forge meta-token'ı (protokol, denetim, altın set) aynı dönemde pilot/araştırma token'ının **2 katını** aşarsa — Forge protokolü tek sayfalık kontrol listesine (ONKAYIT şablonu + KANIT şeması) indirilir, geri kalan altyapı arşive kalkar.

Bu kriter kendisi de bugün commit'lenmelidir; aksi hâlde bu rapor, eleştirdiği şeyi yapmış olur.

---

## Kaynaklar

Yerel:
- `C:\Users\LENOVO\Projeler\forge\README.md`, `KAYIT.md`, `HAKEM-RAPORU.md`
- `C:\Users\LENOVO\Projeler\forge\araclar\makale-okuyucu\README.md`, `SPEC.md`; `araclar\maliyet-sayaci\SPEC.md`
- `C:\Users\LENOVO\Projeler\akademik-bosluk\gapmine\karsilastirma\DENETIM.md`, `altin\gold.json`
- `git -C forge log` (27f60e3, a636c35, bea1d08 — hepsi 2026-10-25 13:13–13:22)

Dış (web'de doğrulandı, 2026-10-25):
- Nosek, Ebersole, DeHaven, Mellor. "The preregistration revolution." PNAS 115 (2018). https://www.pnas.org/doi/10.1073/pnas.1708274114 — ön kaydın amacı: post-hoc bulgu ile sınanmış öngörüyü ayırmak.
- Jacovi, Caciularu, Goldman, Goldberg. "Stop Uploading Test Data in Plain Text." EMNLP 2023. https://arxiv.org/abs/2305.10160 — test verisini şifreli, türev yasaklı tut; kapalı API'lerden dışlama kanıtı iste.
- Sainz ve ark. "NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark." Findings of EMNLP 2023. https://arxiv.org/abs/2310.18018
- Zhang ve ark. (Scale AI). GSM1k: held-out set, yalnız 50/1000 soru açık; kirlenme açığı ölçümü. https://scale.com/leaderboard/math ; özet: https://www.deeplearning.ai/the-batch/the-problem-with-benchmark-contamination-in-ai
- Panickssery, Bowman, Feng. "LLM Evaluators Recognize and Favor Their Own Generations." 2024. https://arxiv.org/abs/2404.13076 — kendi-tercih yanlılığı, kendini tanıma ile ilişkili.
- "Do LLM Evaluators Prefer Themselves for a Reason?" 2025. https://arxiv.org/abs/2504.03846 — zararlı kendi-tercih en çok yargıcın kendisinin zorlandığı örneklerde.
- Anthropic. "Demystifying evals for AI agents." 2026. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents — pass@k vs pass^k, model yargıca insan kalibrasyonu, regresyon ~%100, "Read the transcripts!", 20–50 görevle başla.
- Miller (Anthropic). "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations." 2024. https://arxiv.org/abs/2411.00640 ; https://www.anthropic.com/research/statistical-approach-to-model-evals — eşli fark, standart hata, aralık raporlama.
- Bowyer ve ark. "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints." 2025. https://arxiv.org/abs/2503.01747 — küçük n'de CLT aralıkları fazla dar; Bayesci/alternatif yöntemler.
- Husain. "Creating a LLM-as-a-Judge That Drives Business Results." https://hamel.dev/blog/posts/llm-judge/ — alan uzmanı ikili etiket + gerekçe; TPR/TNR ayrı; etiket başına 30–50, toplam 60 altı aralıklar fazla geniş; dev/test ayrımı. Ayrıca evals SSS: https://hamel.dev/blog/posts/evals-faq/
