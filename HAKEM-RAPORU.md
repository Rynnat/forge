# Hakem Raporu: Forge, gapmine, maliyet-sayaci, akademik-bosluk (2026-10-25)

Hakem, incelenen sistemleri yazmadı. Raporun dışında hiçbir dosya değiştirilmedi. Geçici betikler `...\scratchpad\hakem\` altında: `usage_check.py`, `agents.json`. Transkriptlerden yalnız `type`, `message.id`, `message.model`, `message.usage`, `timestamp` alanları okundu. Mesaj içeriği okunmadı.

---

## 1. Genel hüküm

İki günün en değerli çıktısı **araçlar değil, ölüm testi ve denetim**. R3/R4 raporları ve gapmine DENETIM.md titiz ve dürüst. Eşikleri önceden yazılmış ucuz pilotlar tasarlamışlar; bunlar araştırmanın gerçekten ilerlemesini sağlayacak tek şey. Buna karşılık Forge ritüel gibi kurulmuş, kanıt üretmiyor. Protokolü "eşik önceden yazılır" diyor, ama gapmine'ın eşiği sonuçtan **~8 saat sonra** yazılmış. Sonuç eşiği geçmeyince "ŞARTLI" etiketiyle kurtarılmış. Ölçümü yapan "bağımsız denetçi" de aynı modelin aynı oturumdaki bir kopyası. Bugüne kadar Forge'a girip kabul edilmiş araç sayısı **0**. Oturumun liste fiyatıyla maliyeti **~$64** (bunun ~$27'si gapmine yapımı ve denetimi). Bu arada pilotlar hâlâ koşulmadı, oysa K5 pilotu "0 $, 1 gün" diye yazılmış. Tek tek bakınca: **maliyet-sayaci doğru ve kabul edilmeli.** **gapmine** ucuz bir ön tarayıcı olarak işe yarıyor; hüküm makinesi olarak işe yaramıyor. v2'si ise denetimin ölçtüğü en büyük sızıntıları bilerek dışarıda bırakıp kotaya daha bağımlı yeni özellikler eklemiş. **K5 ve K8** gerçekten açık görünüyor, ama ikisi de dar. Bir lisans öğrencisi için gerçekçi hedef bir **workshop veya short paper**. Ana konferans değil.

---

## 2. Sistem notları

### Forge: **C**, karar: **DÜZELT**
- **Doğru olan felsefe:** "bulunamadı ≠ aranamadı", alıntıyı kodla doğrulama, taban çizgisi. Bunlar sağlam.
- **Eşik önceden yazılmadı.**
  - `forge/` klasörü 2026-10-25T09:42 UTC'de oluşturulmuş, KAYIT.md 09:58'de. DENETIM.md ise 02:01'de yazılmış (PowerShell `CreationTimeUtc`).
  - Yani gapmine'ın "önceden yazılı" eşiği (≥%80 recall) v1 sonucu (%61) bilindikten sonra konmuş.
  - Kanıtlanabilir bir ön kayıt yok: git yok, commit zamanı yok.
- **ŞARTLI bir kaçış kapısı.**
  - gapmine v1 her iki kalite eşiğini de geçemedi: recall %61 < %80, öldürenlerde 3/6 < %80 (KAYIT.md satır 5). Protokolün 4. maddesine göre bu **RED** demek.
  - Buna rağmen "ŞARTLI (ön tarayıcı)" verildi. ŞARTLI rolü için hiçbir eşik önceden yazılmamış.
  - Böylece her başarısız araç "bir rolde işe yarıyor" etiketiyle sisteme girebilir.
- **Eşik sonradan değişti.** maliyet-sayaci satırına bir NOT eklenip karşılaştırılan büyüklük değiştirildi: "son bağlam boyutu ile karşılaştırılacak". Değişiklik makul, ama protokolün 2. maddesini ("sonuçtan sonra değiştirilemez") çiğniyor.
- **Bağımsızlık zayıf.**
  - Denetçi, aynı oturumda aynı model (opus-5-5, `a38f17e9`).
  - Ona brifi, aracı yazan asistan yazdı.
  - Altın set de bir önceki ajanların çıktısı. Yani "ajanla uyuşma" ölçülüyor, "doğruluk" değil.
- **Örneklem küçük.**
  - olum-testcisi eşiği 3 iddiaya dayanıyor (KAYIT.md satır 8). Bu 3'ün cevabı yapan tarafından zaten biliniyor.
  - gapmine'da "öldürenler" n=6.
  - Stokastik araçlar için k koşu şartı yok, oysa DENETIM §4 aynı iddiada hükmün YARALI→ÖLDÜ diye çevrildiğini gösterdi.
- **Tautolojik eşik.** makale-okuyucu için "uydurma alıntı %0" yazılmış. Doğrulanmayan alıntı kodla zaten atılıyor, yani bu eşik her zaman geçilir. Asıl risk başka: alıntı doğru, ama yorum yanlış.
- **README'de olup diskte olmayanlar:** `kanit/`, `sistem/`, her aracın `KANIT.md`'si (forge/README.md satır 24-27).

### gapmine: **v1 ön tarayıcı olarak C, hüküm aracı olarak F. v2 yönü D.** Karar: **DÜZELT (küçült)**
- **Testler:** `.venv` ile 168 test, 168 geçti (74.8 s). Ama testler mock LLM ve fixture'larla koşuyor; recall'u ölçmüyorlar.
- **Denetim iddiaları DB ile doğrulandı** (`karsilastirma/runs/karsilastirma.db`, salt okunur):
  - ÖZET düzeyi: 811 NO, 89 PARTIAL, **0 YES**.
  - TAM düzey: 2 YES.
  - Tüm PARTIAL/YES alıntıları VERIFIED.
  - Altın set (`altin/gold.json`): 92 makale, bunların 36'sı çekirdek, 6'sı öldüren. DENETIM'deki sayılarla birebir aynı.
- **Denetimin hükmü sonuçlarla destekleniyor.** Hüküm işe yaramıyor: araç 6/10'da kaldı, "her şeye YARALI" diyen kör taban 7/10 tutturdu. Ön tarayıcı olarak ise orta: çekirdeğin %61'ini ilk 60'a sokuyor.
- **v2, en büyük sızıntıları hedeflemiyor.**
  - README satır 253 kendisi yazıyor: denetim bulguları #1–#5 ve #7 "kapsam dışı bırakıldı, hâlâ açık". Yalnız #6 (rapor üzerine yazma) çözülmüş.
  - Kodda doğrulandı:
    - `sources/arxiv.py:29` regex'i alt çizgiyi hâlâ atıyor (`[A-Za-z0-9][A-Za-z0-9\-\.]*`).
    - AND→OR yedeği aynı (`arxiv.py:46-52`).
    - `verify_max_per_query = 50`, `fulltext_top_k = 3` (`config.py:34,69`).
    - Geçici 429 hâlâ kota sayılıyor (`httpclient.py:229-233`).
  - v2'nin üç yeni özelliğinin durumu:
    - **Alt iddia modu:** denetimin 6. önerisini (PARTIAL enflasyonu) hedefliyor. Mantıklı.
    - **Atıf takibi:** yalnız OpenAlex'le çalışıyor. Denetime göre ikinci büyük sızıntı zaten OpenAlex kotası (günde ~4 iddia). Atıf takibi bu kıt bütçeyi daha da tüketiyor (README satır 250).
    - **recall:** ölçüm altyapısı. Faydalı.
  - **v2'nin hiçbir özelliği canlı koşulmadı** (README satır 247).
- **Altın set kirlenmiş.**
  - Altın set aracın kendi klasöründe duruyor: `gapmine/karsilastirma/altin/gold.json`.
  - DENETIM kaybolan makaleleri tek tek adıyla sayıyor; v2'yi yazan ajan DENETIM'i okudu (README satır 52, 94, 253).
  - README satır 106'daki "hiçbir gerçek altın sete göre ayarlanmadı" cümlesi teknik olarak doğru olabilir. Ama v2'nin K1–K10 üzerinde ölçülecek recall'u artık bağımsız değil.
- **Ajana göre ne kazandırıyor:**
  - İddia başına ~$0.01–0.02. Ajanın gerçek maliyeti iddia başına $0.62–1.40 (bkz. §3, madde 1). Yani **~50–100× ucuz**.
  - Alıntıyı kodla doğruluyor ve funnel ile her kaybı muhasebeliyor.
  - 10 iddianın 5'inde ajanın listelemediği önemli makaleler buldu (DENETIM tablosu).
- **Ne kaybettiriyor:**
  - Hükmü kör tabandan kötü.
  - Blog, GitHub ve ürün kaynaklarına bakmıyor. 3/10 iddiada asıl öldüren oralardaydı.
  - Özette NO alan makaleyi tam metinden kurtaramıyor.
  - Sorgular koşudan koşuya ~%75 değişiyor.
  - Anahtarsız kotayla günde ~4 iddia taşıyor.
  - Duvar saati ajandan belirgin hızlı değil: 5–6 dk. Ajanlar 6–15 dk sürdü; ikisi aynı işi yapmıyor.

### maliyet-sayaci: **A−**, karar: **DEVAM → KABUL (küçük ekle)**
- **Kabul testini ben yaptım.** Bağımsız betiğim `usage_check.py` yalnız usage alanlarını okuyor.
  - 19/19 ajan için mesaj sayısı ve kümülatif token toplamı, aracın `--json` çıktısıyla **birebir aynı**. Örnek: ae543bee'de 17 mesaj; 34 + 19 736 + 105 167 + 1 193 674 = 1 318 611.
  - Dolar maliyetini elle yeniden hesapladım: $1.1594, araçla aynı.
  - `fiyatlar.json`'daki Opus 5.5 ($4 / $5 / $8 / $0.20 / $20), Haiku 5.5 (100K eşiği dahil) ve us 1.1× değerleri platform.claude.com/docs/en/about-claude/pricing ile aynı.
  - 19 test geçti.
- **Resmi sayı neyi ölçüyor:** **son API çağrısının `input + cache_creation + cache_read + output` toplamını**, yani son bağlam + son çıktıyı.
  - 15 ajanın 11'inde sapma **%0,00**.
  - Kalan 4'ünde −%0,05 ile −%0,23 arası: a35b6eb1, aa77868c, ac3cd4bf, ac670719.
  - Hepsi eşiğin (≤ %2) içinde.
  - Çıktı token'ı eklenmeden yalnız bağlam alınırsa sapma −%0,3 ile −%1,3 arasına çıkıyor. KAYIT'taki "son bağlam boyutu" ifadesi bu yüzden eksik.
  - Resmi sayı toplam kullanım **değil**. Kümülatif kullanım resmi sayının **9–44 katı**: a91f6ac6'da +%858, a38f17e9'da +%4284.
- **Eksik:**
  - Araç resmi sayıyla karşılaştırılabilir büyüklüğü (son bağlam + çıktı) raporlamıyor. Bu yüzden KAYIT'taki eşik araç çıktısıyla doğrudan sınanamıyor. Bir sütun eklenmeli.
  - `tools` modu yalnız `gapmine/reports/*.json`'ı okuyor (SPEC). `karsilastirma/runs/` altındaki 20 denetim koşusunun maliyeti görünmüyor, ve bunu hiçbir uyarı söylemiyor.
- **Değeri:** Bu araç olmasa DENETIM'in yanlış maliyet tablosu (§3, madde 1) fark edilmeyecekti.

### Araştırma çıktısı (akademik-bosluk): süreç **B+**, K5 **B−**, K8 **C+/B−**. Karar: **pilotları hemen koş**
- **Tarama aşaması düşük kesinlikte.** İki turda 77 niş "açık" geldi. Ölüm testinde 10 adayın hiçbiri temiz AYAKTA çıkmadı; yalnız biri "dar" ayakta kaldı (00-SKOR.md "Not"). Tarama ajanlarının "açık" etiketi neredeyse bilgi taşımıyor.
- **K5 (Dafny kanıt kırılganlığı):**
  - **"Benzer çalışma yok" iddiasını kendim sınadım.** 6 arXiv API sorgusu çalıştırdım: `mariposa ∧ LLM`, `instability ∧ LLM ∧ proofs`, `brittle ∧ Dafny`, `stability ∧ Verus`, `seed ∧ Dafny`, `robustness ∧ Verus ∧ proof`. Ayrıca 2 web araması yaptım. LLM kanıtı ile insan kanıtını seed veya mutasyon kararlılığı açısından karşılaştıran bir çalışma bulamadım. İddia **destekleniyor**, ama yalnız "bulunamadı" düzeyinde.
  - En tehlikeli komşu, Zhou & Parno'nun "Towards Proof Stability in SMT based Program Verification" çalışması (POPL'25 Dafny WS). R3 bunu yalnız ARAMA ÖZETİ düzeyinde okumuş. Özeti LLM içermiyor. Ama aynı grup "Proof Stability and Applications" diye bir oturum yürütüyor; kapılma (scoop) riski R3'ün dediğinden de gerçek.
  - DENETIM, 2606.14867'yi K5 için "bozulma kararlılığı" çalışması diye anıyor. Özetini okudum: konusu autoformalization'ın girdi parafrazına dayanıklılığı, solver instabilitesi değil. K5'i yaralamıyor.
  - DafnyBench verisini doğruladım: Apache-2.0 lisanslı, `results/reconstructed_files/` altında gpt-4o, claude-3-opus ve 3 model daha var (GitHub API).
  - **Risk:** DafnyBench programları küçük. Mariposa instabiliteyi büyük projelerde ölçmüştü; küçük programlarda etki muhtemelen sıfıra yakın çıkar (R3 de böyle diyor). Pilotun ELE çıkma olasılığı yüksek.
  - Pilot eşiği ("≥10 dosya ve ≥2 kat") istatistik testi içermiyor; küçük sayılarda gürültüye açık.
- **K8 (VLM belirsizlik grafikleri):**
  - **Kale 2020 verisini kontrol ettim.** github.com/kalealex/effect-size-jdm altında `experiment-anonymous.csv` (15 MB) ve `model-data.csv` (11 MB) var. CSV'lerde trial düzeyi sütunlar bulunuyor: `pSup`, `groundTruth`, `condition`. `StimuliGeneration.Rmd` de mevcut. Veri **erişilebilir**.
  - Ama **lisans yok**: GitHub API `license: null` döndü, README'de de lisans beyanı yok. 00-SKOR'daki "açık insan verisi" ifadesi bu yüzden abartılı. Yeniden analiz için sorun değil. R4'ün değer puanında (e=4) saydığı "yeniden kullanılabilir uyaran seti" ise izin almadan dağıtılamaz.
  - UnReason gerçek: AAAI-26, ojs.aaai.org/38812. R4'ün verdiği repo `github.com/lel304/UnReason` ise 404 dönüyor.
  - HOPs açısı zayıf: insanlar animasyon gördü, VLM'e kare dizisi verilecek. Uyaran aynı olmadığı için karşılaştırma geçerliliği zayıflıyor.
  - Veri kirliliği riski var (R4 de belirtiyor).
- **Lisans öğrencisi için makale olur mu?**
  - **K8:** Evet, VIS short paper ya da Uncertainty Viz workshop olarak. Etik kurul yok, ~$50–90. LLO/brms analizi zor ama öğrenilebilir.
  - **K5:** Yalnız pilot etki gösterirse, Dafny WS veya LMPL düzeyinde. Null sonuç da yayımlanabilir ama zayıf olur.
  - **İkisi için de bir hoca ortaklığı şart.**
- **Tutarsızlık:** YOL.md "yalnız profilsiz bağımsız tur" diyor. Ama ölüm testi profilli turdan K9 (LLM-CAD) ve K10 (EMG) adaylarını da sınamış.

### makale-okuyucu: **not verilmedi (yapımda)**
- Dosyalar şu an değişiyor; son değişiklik 13:06 yerel saat.
- 6 test dosyası var. Testler koşulmadı (DOKUNMA talimatı).
- Duman testi 2 makalede yapılmış (2501.08156, 2001.08361) ve kart üretilmiş. `data/smoke/*.err.txt` dosyaları var, içerikleri okunmadı.
- Duman makalesi 2501.08156 altın setteki bir K7 öldüreni. Kabul ölçümünde bu makale kullanılmamalı.
- Kabul eşiğindeki "uydurma alıntı %0" tautolojik (bkz. Forge). Yerine "doğrulanmış alıntıyla yanlış yorum oranı" konmalı.

---

## 3. Kanıtla desteklenmeyen (veya yanlış) iddialar

1. **DENETIM §2, maliyet tablosu: "Token oranı ~1:1", "ajan ~$0.3–0.5 / iddia". YANLIŞ.**
   - Tablodaki ajan token'ları resmi "son bağlam" sayılarının yarısı. Örnek: aa77868c için 145 508/2 ≈ 73k.
   - Ölüm testi ajanlarını eşledim: R1 aa77868c, R2 ab83d6e8, R3 ac3cd4bf, R4 ac670719, R5 a91f6ac6. Eşleme bitiş zamanları ile R dosyalarının mtime'larının ≤15 s farkla tutmasına ve token/2 değerlerinin tabloyla birebir aynı olmasına dayanıyor.
   - Gerçek kullanım iddia başına 0,55–2,77 M token, $0.62–1.40.
   - Araç bu yüzden denetimin yazdığından daha da ucuz: token'da ~10–35×, parada ~50–100×.
2. **KAYIT.md: "Kabul eşiği (önceden yazılı)", gapmine satırı. Desteklenmiyor.** Forge, DENETIM'den ~7,7 saat sonra kurulmuş. Ön kayıt kanıtı yok.
3. **KAYIT.md: "v1: ŞARTLI".** Önceden yazılı eşiklerin ikisi de geçilmemiş. Protokole göre RED olmalı. ŞARTLI rolünün eşiği yok.
4. **KAYIT.md NOT: "son bağlam boyutu (1 ajanda −%0,1)". Eksik.** Doğrusu son bağlam + son çıktı. Yalnız bağlam alınırsa sapma −%0,3 ile −%1,3 arası.
5. **gapmine README satır 106: "Bağımsızlık… ayarlanmadı". Gelecek ölçüm için geçersiz.** Altın set ve kayıp listesi v2'yi yazan ajanın erişimindeydi ve DENETIM'i okuduğu belgeli.
6. **gapmine v0.2'nin iyileştirdiği varsayımı.** Canlı kanıt sıfır (README satır 247). 168 yeşil test mock davranışını doğruluyor, recall'u değil.
7. **00-SKOR: "Kale 2020'nin açık insan verisi".** Veri erişilebilir ama lisanssız (GitHub API `license: null`).
8. **R4: UnReason repo github.com/lel304/UnReason.** 404 dönüyor. Makalenin kendisi doğrulandı.
9. **DENETIM K5 satırı: 2606.14867 ilgili diye anılıyor.** Konusu farklı (autoformalization dayanıklılığı).
10. **forge/README.md satır 24-27.** `kanit/`, `sistem/` ve `KANIT.md` yok.
11. **00-SENTEZ-B'nin "Örtüşme yok" çıkarımı ile YOL.md'nin "yalnız bağımsız tur" kapsamı.** Ölüm testi, profilli turun adaylarını (K9, K10) da içeriyor.

Destekleniyor (kontrol ettim):
- DENETIM'in 0 YES / 89 PARTIAL sayımı.
- Altın set büyüklükleri.
- arXiv alt çizgi hatasının v2'de hâlâ durması.
- R3'teki "K5 için benzer çalışma bulunamadı".
- DafnyBench verisinin varlığı ve lisansı.
- Kale verisinin trial düzeyinde oluşu.
- UnReason'ın varlığı.
- maliyet-sayaci'nin token ve dolar doğruluğu.
- gapmine'ın 168 testi.

---

## 4. Riskler ve değerler

**En büyük 3 risk**
1. **Kendi kendini doğrulayan döngü.**
   - Aracı, denetimi, eşiği ve sicili aynı model aynı oturumda yazıyor.
   - Eşikler sonradan konuyor, başarısızlık ŞARTLI diye kurtarılıyor.
   - Bu hâliyle Forge bir kalite kapısı değil, bir onay damgası.
2. **Meta-iş asıl işi yiyor.**
   - 00-SKOR dün 21:18'de "önce 1 günlük pilot" dedi. O andan bu yana:
     - gapmine v2 için ~$13 harcandı.
     - Denetim için ~$14 harcandı.
     - Forge kuruldu.
     - makale-okuyucu yazılmaya başlandı.
     - olum-testcisi planlandı.
   - Pilotların hiçbiri koşulmadı. Oysa K5 pilotu $0'a mal oluyor ve tek başına bir adayı öldürebilir ya da ayakta tutabilir.
3. **gapmine yanlış yöne büyüyor.**
   - Kotaya bağımlı yeni özellikler eklendi.
   - Ölçülmüş sızıntılar (21/92 getirme kaybı, ilk-N kesimi, 429) açık kaldı.
   - Altın set kirlendi. Gelecekteki "recall %80 oldu" sonucu ezber olabilir.

**En değerli 3 şey**
1. **Ölüm testi süreci ve R3/R4.** Tam metin okunmuş, okuma düzeyi etiketlenmiş, pilot eşikleri sayıyla önceden yazılmış. Batık yatırımı gerçekten önlüyor: 10 adaydan 8'ini eledi.
2. **gapmine DENETIM.md.** Örnek alınacak bir denetim. Kayıpları aşama aşama sebepleriyle sayıyor; canary testi var, tekrarlanabilirlik ölçülmüş, kod satırları gösterilmiş.
3. **maliyet-sayaci.** Doğru, gizlilik sözleşmesine uyuyor, ucuz. En önemli bulgusu: resmi alt-ajan token sayısı gerçek kullanımın 9–44'te 1'i. Bundan sonraki her maliyet kararı bu araçla verilmeli.

---

## 5. Önümüzdeki 2 hafta (sıralı)

1. **Gün 1:** `forge/` ve `akademik-bosluk/` klasörlerini git'e al. K5 ve K8 pilot eşiklerini **koşmadan önce** commit et; commit zamanı ön kaydın kanıtı olur.
2. **Gün 1–2: K5 pilotu.** DafnyBench gpt-4o + claude-3-opus, 20 seed, ~300 eş. Eşiğe bir istatistik ekle: Fisher exact testi, p < 0,05. ELE çıkarsa K5'i bırak, Verus'a "yeni gerekçe" arama.
3. **Gün 3–4: K8 pilotu** (~$5). Kale uyaran kodu, 2 VLM, statik 3 kodlama. HOPs'u pilottan çıkar. Ayrıca Kale/Hullman'a veri kullanım izni için tek satırlık bir e-posta at.
4. **Gün 5:** Pilot sonuçlarıyla 1 sayfalık pitch hazırla ve hocaya götür. Hoca bulunmadan Faz 1'e geçme.
5. **maliyet-sayaci:** "son bağlam + çıktı" sütununu ekle (yarım saatlik iş) ve bu raporun yaptığı karşılaştırmayı regresyon testi yap. Sonra **KABUL**. DENETIM'in maliyet tablosuna düzeltme notu ekle.
6. **Forge protokolünü düzelt:**
   - ŞARTLI için rol eşiği de önceden yazılsın.
   - Stokastik araçlarda en az 3 koşu şartı olsun.
   - Altın set aracı yazanın göremeyeceği yerde dursun ve yeni iddialarla tazelensin.
   - "Bağımsız denetçi" ya farklı bir model ya da insan kontrolü olsun.
   - Tautolojik eşikleri (alıntı %0) değiştir.
   - gapmine KAYIT satırını şöyle düzelt: "hüküm: RED; ön tarama: rol eşiği yazılacak".
7. **gapmine'ı dondur.** Yeni özellik ekleme. Yalnız şunları yap:
   - Bir OpenAlex anahtarı al.
   - Denetim bulguları #1 (alt çizgi), #2 (AND/OR ara kademe + 200 sınırı) ve #3 (429) düzelt; toplam ~1 günlük iş.
   - Yeni, aracı yazanın görmediği 10 iddialık bir altın set kur.
   - Bunlardan önce v2'nin K1–K10 recall'unu "başarı" diye raporlama.
8. **makale-okuyucu ve olum-testcisi'ni beklet.** Pilotlardan biri DEVAM çıkıp gerçek bir okuma ihtiyacı doğana kadar yeni araç yapma. olum-testcisi'nin 3 iddialık eşiği zaten anlamsız.

---

### Kaynaklar (dış)
- Fiyatlar: https://platform.claude.com/docs/en/about-claude/pricing
- Kale 2020 verisi: https://github.com/kalealex/effect-size-jdm (API: `license: null`)
- DafnyBench: https://github.com/sun-wendy/DafnyBench (Apache-2.0)
- UnReason: https://ojs.aaai.org/index.php/AAAI/article/view/38812
- Zhou & Parno POPL'25 WS: https://popl25.sigplan.org/details/dafny-2025-papers/5/Towards-Proof-Stability-in-SMT-based-Program-Verification
- Dafny brittleness blogu: https://dafny.org/blog/2023/12/01/avoiding-verification-brittleness/
- arXiv özetleri: 2606.14867, 2605.03822 (KVerus), 2512.18436 (VeruSAGE), export.arxiv.org API üzerinden
