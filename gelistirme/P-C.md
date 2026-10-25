# P-C: Forge için geliştirme önerileri. Mercek: kullanıcıya değer, strateji, batık yatırım (2026-10-25)

Kapsam: `forge/README.md`, `forge/KAYIT.md`, `forge/HAKEM-RAPORU.md`, `akademik-bosluk/YOL.md`, `PILOT-ESIKLERI.md`, `olum-testi/00-SKOR.md` okundu. Ayrıca `pilot-k5/karar-gunlugu.md` ve `pilot-k5/data/run_log.txt` okundu, git logları kontrol edildi. Maliyet rakamları `maliyet_sayaci.py sessions` ve `agents --session 76053f18` çıktısından alındı. Bu çıktılarda yalnız sayısal sütunlar kullanıldı. Hiçbir dosya değiştirilmedi; yalnız bu rapor yazıldı.

> Dolar değerleri API liste fiyatıyla teorik maliyettir, fatura değildir. Ama göreli kıyas için geçerli.

---

## 0. Sayılarla durum

### Harcama
| Kalem | Tutar | Pay | Kaynak |
|---|---|---|---|
| Son ~13 günün tüm oturumları | **$1 624,74** | — | `sessions` TOPLAM, 50 oturum |
| Forge ve akademik-bosluk oturumu (76053f18) | **$74,13** | %100 | `agents` TOPLAM |
| gapmine v2 yapımı ve denetimi (a39ba301 + a38f17e9) | $27,23 | %37 | Ajan eşlemesi hakem raporundan |
| Ölüm testi R1–R5 (aa77868c, ab83d6e8, ac3cd4bf, ac670719, a91f6ac6) | $10,73 | %14 | Ajan eşlemesi hakem raporundan |
| Ana oturum | $9,98 | %13 | `agents` |
| İlk 8 ajan (ae543bee…ae40262a) | $11,91 | %16 | Eşlenmedi |
| Kalan 7 ajan | $14,30 | %19 | Eşlenmedi (hakem, makale-okuyucu, bu öneri turu vb.) |

### Ne elde edildi
| Çıktı | Hedef 1 (makale) | Hedef 2 (öğrenme) | Hedef 3 (sistem) |
|---|---|---|---|
| Ölüm testi: 10 aday → 2 pilot (8 aday elendi, eleme başına ~$1,34) | **Doğrudan** | Orta (raporlar okunabilir) | — |
| K5 pilotu: eşik commit'li (`b4b2b53`), D0–D2 önceden yazılı. Okuma anında base aşaması 750/1505, tahmini toplam ~105 dk, API maliyeti ~$0 | **Doğrudan** | Yüksek, eğer öğrenci kararları anlıyorsa | — |
| maliyet-sayaci: KABUL (koşullu) | Dolaylı | — | **Evet**. Resmi sayının gerçek kullanımın 9–44'te 1'i olduğunu buldu |
| gapmine: RED, donduruldu | Yok | — | Yok |
| makale-okuyucu v0.1: kabul testi yok, donduruldu | Henüz yok | Risk (bkz. Ö3) | Henüz yok |
| Forge protokolü + sicil | Yok | — | Henüz kapı değil, damga (hakem §4) |

### Denge
- Hedefe doğrudan hizmet eden iş (ölüm testi + pilot) bilinen harcamanın en az **%14'ü**: $10,73 artı ~$0'lık pilot.
- Araç yapım/denetim kaleminin bilinen kısmı **%37** ($27,23). Bunun sicile verdiği tam KABUL sayısı **0**.
- En ucuz ve en çok karar üreten iş, araç gerektirmeyen işti: önceden yazılı eşikle tam metin okumak ve yerel CPU'da pilot koşmak.
- Pilot, hakem "meta-iş asıl işi yiyor" dedikten sonra birkaç saat içinde başladı (commit 13:13, D0 13:18). Engel teknik değildi; **öncelik** sorunuydu.

**Hüküm:**
- **Hedef 1 (makale):** Forge bugün ona neredeyse hiç hizmet etmiyor; hizmet eden şey akademik-bosluk'un kendi süreci.
- **Hedef 3 (sistem):** Tek gerçek katkı maliyet-sayaci.
- **Hedef 2 (öğrenme):** Ölçülmüyor. Bu en büyük kör nokta.

---

## Öneriler (önem sırasına göre)

### Ö1: Yeni araç moratoryumu. Forge "talep çekmeli" çalışsın (en önemli)

**(a) Sorun ve kanıt**
- 00-SKOR 2026-10-24 21:18'de "önce 1 günlük pilot" dedi. Pilot ise ancak 10-25 13:18'de başladı.
- Arada şunlar yapıldı: gapmine v2 + denetim ($27,23), Forge kuruldu, makale-okuyucu yazıldı, olum-testcisi ve ders-modu planlandı.
- Forge'un hiçbir aracı bir pilotun ya da makalenin içinde tekrarlanan bir elle işten doğmadı. Hepsi "ileride lazım olur" diye yapıldı.
- Dış örnek: Anthropic'in ajan rehberi "en basit çözümle başla, karmaşıklığı yalnız gerektiğinde artır; bazen bu, ajan sistemi kurmamak demek" diyor ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

**(b) Öneri**
- K5 ve K8 pilotları hüküm alana ve 1 sayfalık pitch hocaya gidene kadar **yeni araç yazılmasın, mevcut araçlara özellik eklenmesin.**
- Bundan sonra bir araç ancak şu üç koşulla yapılsın:
  1. Aynı elle iş gerçek araştırma akışında **≥3 kez** yapılmış olsun ve günlükte kaydı bulunsun.
  2. Elle maliyeti ölçülmüş olsun. Bu taban çizgisi bedavaya gelir, çünkü iş zaten yapıldı.
  3. Aracın yokluğu bir sonraki kilometre taşını geciktiriyor olsun.

**(c) Beklenen kazanç**
- Araç kalemindeki harcama (%37) araştırmaya döner.
- K8 pilotu (~$5) ve hoca pitch'i aynı hafta içinde biter.
- Yapılan her aracın kendiliğinden bir taban çizgisi ve gerçek bir kullanıcısı olur.

**(d) Maliyet:** Sıfır. Yalnız disiplin gerekir. Fırsat maliyeti: ders-modu ve makale-okuyucu gecikir.

**(e) Metrik ve eşik:** Eşik bugün commit edilmeli.
- Moratoryum süresince "Forge/araç" diye etiketlenen oturum harcaması, toplam araştırma harcamasının **≤ %10'u** olmalı. Ölçüm için bkz. Ö6.
- K8 pilot hükmü ve hoca pitch'i **2026-11-08'e kadar** çıkmalı.

**(f) Öldürme kriteri**
- Moratoryumun kendisi şu durumda gevşetilir: pilotlar en az biri DEVAM ile bitti ve 2 hafta içinde aynı elle iş ≥3 kez tekrarlandı.
- Araç fikri şu durumda kalıcı iptal edilir: 4 hafta içinde ≥3 tekrar koşulunu sağlamadı.

---

### Ö2: Forge'un kendisi için tarihli öldürme kriterleri

**(a) Sorun ve kanıt**
- Forge'un sicilinde RED ve ŞARTLI var, ama Forge'un **kendi** başarısızlık tanımı yok.
- Bugüne kadar tam KABUL alan araç sayısı 0. Kurulan protokolün eşiği ilk araçta sonradan yazıldı (hakem §2).
- Batık maliyet tuzağı tam da bu: "altyapıyı kurduk, artık kullanalım".
- Dış örnek: METR'in randomize deneyinde deneyimli geliştiriciler AI araçlarıyla **%19 daha yavaş** çalıştı, ama kendilerini **%20 hızlanmış** sandı ([The Register](https://www.theregister.com/2025/07/11/ai_code_tools_slow_down/), [eWeek](https://eweek.com/news/news-ai-tools-slow-developer-productivity-study)). Algılanan fayda, ölçülen faydanın yerine geçmiyor.

**(b) Öneri:** Aşağıdaki tabloyu `forge/OLUM-KRITERI.md` olarak commit et. Tarih: **2026-11-22**, yani 4 hafta sonra. O gün tek bir mekanik hüküm verilsin.

| Koşul | Ölçüm | Eşik |
|---|---|---|
| K1: Kullanılan araç | Gerçek araştırma görevinde kullanılan KABUL'lü araç sayısı. "Kullanıldı" = günlükte en az 5 çağrı | ≥ 1 (maliyet-sayaci dışında) |
| K2: Maliyet oranı | Forge-meta harcaması / akademik-bosluk harcaması | ≤ %25 |
| K3: Kilometre taşı | En az bir pilot hükmü + hoca görüşmesi | Tarihinde yapılmış |
| K4: Kapı gerçek mi | En az bir aracın önceden commit'li eşikte RED alıp arşive gitmesi ya da gerçekten KABUL alması | "ŞARTLI" sayılmaz |

- **Hüküm kuralı:**
  - K3 tutmadıysa **Forge DONDUR**: yalnız maliyet-sayaci tek başına bir betik olarak kalır, gerisi `_arsiv`'e gider.
  - K1 ile K2'nin ikisi de tutmadıysa **Forge ÖLDÜR**: klasör arşive alınır, protokolün iyi fikirleri ("bulunamadı ≠ aranamadı", ön kayıt) akademik-bosluk'un README'sine taşınır.

**(c) Beklenen kazanç**
- Batık yatırım kararı duyguya değil tarihe bağlanır.
- Kullanıcının şüpheciliği sisteme kodlanmış olur.

**(d) Maliyet:** ~15 dk yazım. 11-22'de ~10 dk ölçüm.

**(e) Metrik:** Dosya commit zamanı < 2026-10-26. 11-22'de hüküm satırı aynı dosyaya, yeni bir commit'le yazılır.

**(f) Öldürme kriteri:** Kriter dosyası tarihinden sonra değiştirildiyse bu öneri başarısız sayılır, Forge da otomatik DONDUR'a geçer.

---

### Ö3: Öğrenme kapısı. "Önce öğrenci düşünür, sonra araç"

**(a) Sorun ve kanıt**
- Hedef 2 (kara kutu olmasın) Forge'un hiçbir metriğinde yok.
- K5 karar günlüğündeki 14 analiz kararını (McNemar, Wilson aralığı, `0` etiketli görevler, `--allow-warnings`) asistan yazdı. Öğrencinin bunları savunabildiğine dair kayıt yok.
- makale-okuyucu ve ders-modu planı tam da "okumayı devralma" riskini taşıyor. ders-modu kuralı "okumanın yerine geçmez" diyor, ama bunu ölçen bir şey yok.
- Dış kanıt:
  - Bastani vd. (PNAS 2025), ~1000 öğrenci: korumasız GPT erişimi pratikte notu %48 artırdı, erişim kalkınca sınav notu **%17 düştü**. Öğrenmeyi koruyacak şekilde tasarlanmış "GPT Tutor" bu düşüşü yaşatmadı ([Wharton](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education), [SSRN](https://papers.ssrn.com/abstract=4895486)).
  - Lee vd. (CHI 2025), 319 bilgi çalışanı: AI'ya güven arttıkça eleştirel düşünme azalıyor; kendine güven arttıkça artıyor ([Microsoft Research](https://www.microsoft.com/en-us/research/?p=1135061)).
  - MIT "Your Brain on ChatGPT" (n=54, hakemsiz): LLM grubu kendi yazdığı metinden alıntı yapmakta zorlandı ([MIT Media Lab](https://www.media.mit.edu/publications/your-brain-on-chatgpt/)). Küçük örneklem, temkinli okunmalı.

**(b) Öneri:** Her pilot hükmünden ve okunan her kilit makaleden sonra 20 dakikalık bir **kapalı-kitap geri anlatma** yapılsın:
1. Öğrenci, asistana bakmadan şunları yazar: pilotun ne ölçtüğü, eşiğin neden o değer olduğu, sonucun ne zaman yanlış olabileceği ve 3 hakem sorusuna cevap.
2. Asistan ya da tercihen farklı bir model, önceden yazılı 5 maddelik rubrikle puanlar.
3. Eksik çıkan madde bir sonraki oturumun ilk 10 dakikasında konuşulur.
- ders-modu bir araç olarak değil, bu kapının **elle** yapılan hâli olarak denensin (Mariposa ile).
- Sıralama tersine çevrilsin: önce öğrenci tahmin eder ("sence DafnyBench'te kararsızlık çıkar mı?"), sonra veri gösterilir.

**(c) Beklenen kazanç**
- Hoca görüşmesinde öğrenci kendi pilotunu savunabilir.
- Makale yazım aşamasında (Faz 3) asistana bağımlılık azalır.
- Hedef 2 ilk kez ölçülür.

**(d) Maliyet:** Pilot başına ~20 dk öğrenci zamanı, ~$0,5 puanlama.

**(e) Metrik ve eşik:** Rubrik bugün commit edilmeli.
- K5 hükmünden sonraki ilk geri anlatmada **≥ 3/5**.
- Hoca görüşmesinden önce **≥ 4/5**.
- Ek olarak: öğrencinin önceden yazdığı tahminin pilot sonucuyla karşılaştırması kayıtlı olmalı. Tutması gerekmiyor; kaydın varlığı ölçülür.

**(f) Öldürme kriteri**
- İki ardışık geri anlatma ≤ 2/5 çıkarsa: asistanın üreteceği yeni analiz kararları durur, öğrenci önce mevcut kararları anlar.
- Kapı 3 kez atlanırsa (pilot hükmü var, geri anlatma yok) öneri başarısız sayılır. O zaman "kara kutu olmasın" hedefi Forge'dan çıkarılıp dürüstçe "hedef değil" diye yazılır.

---

### Ö4: Yapılmayacaklar. olum-testcisi iptal, gapmine arşiv, makale-okuyucu batık sayılsın

**(a) Sorun ve kanıt**
- **olum-testcisi:**
  - Ölüm testi elle $10,73'e 10 adayı işledi ve hakemin "en değerli 3 şey" listesinde 1. sırada.
  - Bu iş araştırma döngüsünde **bir kez** yapıldı. Araçlaştırma için tekrar yok.
  - Eşiği yalnız 3 iddiaya dayanıyor ve bu iddiaların cevabı zaten biliniyor (hakem §2).
- **gapmine:**
  - Hüküm aracı olarak kör tabandan kötü (6/10'a karşı 7/10). Altın set kirli.
  - Düzeltmek ~1 gün iş, artı OpenAlex anahtarı, artı yeni bir altın set gerektiriyor.
  - Dış örnek: Sakana "AI Scientist"in bağımsız değerlendirmesi, yüzeysel anahtar kelime aramasının köklü fikirleri "yeni" diye etiketlediğini buldu ([Beel vd., arXiv 2502.14297](https://arxiv.org/abs/2502.14297)). gapmine'ın zayıflığı yapısal; kişisel ölçekte kapanacak bir şey değil.
  - Answer.AI, Devin ile 20 görevde yalnız 3 başarı aldı ve hangi görevin işe yarayacağını öngöremedi ([Answer.AI](https://www.answer.ai/posts/2025-01-08-devin)).
- **makale-okuyucu:**
  - 67 testli v0.1 zaten yazıldı. Bu bir **batık** maliyet.
  - "Yazdık, o hâlde kabul testini yapalım" gerekçesi geçersiz.

**(b) Öneri**
- olum-testcisi'ni sicilden **İPTAL** gerekçesiyle çıkar. Ölüm testi elle, önceden yazılı şablonla yapılmaya devam etsin.
- gapmine'ı **ARŞİV**'e al. Yeniden açılma koşulu: iki pilot da ELE çıktı ve yeni bir aday turu gerekiyor. O zaman bile önce elle yapılmış bir turla kıyaslansın.
- makale-okuyucu dondurulmuş kalsın. Kabul testi yalnız Faz 1'de **≥ 10 makalelik** gerçek bir okuma ihtiyacı doğarsa yapılsın.
- ders-modu araç olarak yapılmasın (bkz. Ö3).

**(c) Beklenen kazanç**
- En az 2–3 araçlık gelecek harcama önlenir.
- Gelecekte gapmine'ın kirli altın setiyle sahte bir "recall %80" başarısı ilan etme riski ortadan kalkar.

**(d) Maliyet:** KAYIT.md'de 3 satır değişikliği. Kaybedilen: gapmine'ın teorik "~50–100× ucuz ön tarama" potansiyeli, ki bu yalnız yeni bir tarama turu gerekirse değer taşıyor.

**(e) Metrik ve eşik:** 2026-11-22'ye kadar iptal ya da arşivlenmiş araçlara harcanan token = **0** (maliyet-sayaci `tools` modu + oturum etiketi).

**(f) Öldürme kriteri (bu önerinin geri alınması)**
- İki pilot da ELE çıkar ve yeni aday taraması elle **> $25** tutarsa, gapmine yeniden açılabilir.
- Açılırsa önce temiz, görülmemiş 10 iddialık altın set kurulur. Eşik kod yazılmadan commit edilir.

---

### Ö5: Değer üretecek tek "sıradaki araç": K5 için rakip bekçisi. Koşullu ve deterministik

**(a) Sorun ve kanıt**
- K5'in en büyük öldürücüsü kapılma (scoop). 00-SKOR şöyle diyor: "Dafny ekibi önce yapabilir".
- Hakem de Zhou & Parno'nun "Proof Stability" oturumunu gerçek bir risk olarak işaretledi.
- Faz 1–3 boyunca (8–12 hafta) bir rakip çıkarsa, her geçen hafta batık maliyet olur.
- YOL.md "literatür bekçisi"ni zaten listeliyor. Ama bugün gapmine gibi LLM'li bir boru hattı gerekmiyor. Gereken, sabit 6–8 arXiv/Semantic Scholar sorgusu + yeni sonuçların diff'i.
- Dış örnek: Hamel Husain'e göre değerlendirmenin büyük kısmı "veriye bakmak", ve bunun için CSV ya da düz metin yetiyor ([O'Reilly](https://www.oreilly.com/radar/podcast/generative-ai-in-the-real-world-getting-beyond-the-demo-with-hamel-husain/), [Simon Willison](https://simonwillison.net/tags/hamel-husain/)). Anthropic de araçların her API'yi sarmamasını, az ama amaca özel olmasını öneriyor ([Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)).

**(b) Öneri**
- **Yalnız K5 pilotu DEVAM çıkarsa** yaz. Kapsam:
  - Hakemin kullandığı 6 sorgu (`mariposa ∧ LLM`, `brittle ∧ Dafny` vb.) + 2 yazar takibi (Parno, Zhou).
  - Haftalık çalışır. Yeni başlık ve özetleri tek satırlık özet olarak verir. LLM kullanmaz.
  - "Aranamadı" durumunu ayrı raporlar (Forge felsefesi).
- Önceki iş elle yapılmıştı. Hakemin kendi sorgu seti hazır bir taban çizgisi.

**(c) Beklenen kazanç:** Kapılma, Faz 2'nin sonunda değil haftalar önce fark edilir. 4–6 haftalık deney emeğini kurtarabilecek tek ucuz sigorta bu.

**(d) Maliyet:** ~2 saat kod. Çalıştırma maliyeti $0.

**(e) Metrik ve eşik:** Önceden kayıt.
- **Canary testi:** Zhou & Parno POPL'25 WS makalesi ve Mariposa, araç ilk koşturulduğunda **2/2** yakalanmalı.
- 4 haftalık koşuda yanlış alarm (öğrencinin "ilgisiz" dediği) haftada **≤ 5** olmalı.

**(f) Öldürme kriteri**
- K5 ELE ya da ARADA→ELE çıkarsa hiç yazılmaz.
- Canary 2/2'yi tutturamazsa ya da 4 hafta boyunca öğrenci çıktıyı hiç açmadıysa (günlük kaydı) arşive gider.

---

### Ö6: maliyet-sayaci'yi bitir ve onu "hedef başına harcama" defterine çevir

**(a) Sorun ve kanıt**
- Forge'un tek KABUL adayı bu araç. Hakem "son bağlam + çıktı" sütununun eksik olduğunu yazdı. KABUL hâlâ koşullu.
- Daha önemlisi: araç bugün oturum ve ajan düzeyinde rapor veriyor, **hedef** düzeyinde değil.
- Bu raporda harcamanın %35'i ($26,21) hiçbir kaleme eşlenemedi.
- Bu ölçüm olmadan Ö1, Ö2 ve Ö4'ün eşikleri ölçülemez.
- METR örneği burada da geçerli: algı ölçümün yerine geçmiyor.

**(b) Öneri**
1. Hakemin istediği sütunu ekle. Hakemin karşılaştırmasını regresyon testi yap. KABUL ver.
2. Basit bir etiket dosyası (`etiketler.csv`: oturum/ajan kimliği → `arastirma | forge-meta | ogrenme | diger`) ve bu etiketleri toplayan bir `ozet --hafta` alt komutu ekle.
3. Her pazar tek satırlık rapor: "bu hafta $X; araştırma %a, forge-meta %b, eşlenmemiş %c".

**(c) Beklenen kazanç**
- Ö2'deki öldürme kriteri mekanik olarak ölçülebilir hâle gelir.
- Forge, varlığını kendi aracıyla sınar.

**(d) Maliyet:** ~1–2 saat kod + haftada 5 dk etiketleme.

**(e) Metrik ve eşik**
- Regresyon: hakemin 19 ajanlık karşılaştırmasında sapma **≤ %0,5**.
- Haftalık raporda eşlenmemiş pay **≤ %10**. Bugün %35.

**(f) Öldürme kriteri:** 3 hafta üst üste etiketleme yapılmazsa (eşlenmemiş > %30) etiket katmanı silinsin. Araç yalnız sayaç olarak kalsın. Ö2'nin K2 koşulu da "ölçülemedi = başarısız" sayılsın.

---

### Ö7: Protokolü sadeleştir. ŞARTLI kalksın, eşik commit'i zorunlu olsun, denetçi farklı olsun

**(a) Sorun ve kanıt**
- "ŞARTLI" etiketi başarısız gapmine'ı sisteme sokmak için kullanıldı (hakem §2, §3.3).
- Denetçi aynı model, aynı oturumda çalıştı; brifini aracı yazan asistan yazdı. Altın set de aracı yazanın erişimindeydi.
- Stokastik araçlarda tek koşu yapıldı. Aynı iddiada hüküm YARALI'dan ÖLDÜ'ye döndü (DENETIM §4).
- Bu hâliyle protokol hiper şüpheci bir kullanıcıya güven vermiyor, yalnızca ritüel üretiyor.
- Dış örnek: Husain, testlerin hepsi geçiyorsa takımın muhtemelen yeterince zor test yazmadığını, ~%70 geçme oranının daha anlamlı olduğunu söylüyor ([aakashg özet](https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/)).

**(b) Öneri:** README'deki 5 adımlık protokol 4 kurala insin:
1. **Eşik = commit.** Eşik dosyası, aracın ilk kod commit'inden **önce** commit edilmiş olmalı. Değilse ölçüm geçersizdir. Bu, git log ile mekanik olarak kontrol edilir.
2. **İkili karar:** KABUL veya RED. "Bir rolde işe yarıyor" deniyorsa, o rol için yeni eşik yazılır ve sıfırdan ölçülür.
3. **k ≥ 3 koşu:** Stokastik araçlarda hüküm medyandan verilir; ayrıca en kötü koşu raporlanır.
4. **Ayrı denetçi:** Denetçi farklı bir model ya da öğrencinin kendisidir. Altın set aracı yazan ajanın erişemeyeceği bir klasörde durur. En az bir ölçümü öğrenci elle yapar; bu, Ö3'e de hizmet eder.
- Ayrıca README'de olup diskte olmayan `kanit/`, `sistem/` ve `KANIT.md` vaatleri silinsin.

**(c) Beklenen kazanç**
- Bir sonraki KABUL kararı kullanıcının güvenebileceği bir karar olur.
- "Onay damgası" riski (hakemin 1 numaralı riski) kapanır.

**(d) Maliyet:** ~30 dk README düzenleme. Her ölçüm turunun maliyeti k=3 nedeniyle ~3 katına çıkar. Bu, araç sayısını kendiliğinden azaltır, ve bu istenen bir yan etki.

**(e) Metrik ve eşik:** 2026-11-22'ye kadar sicildeki her yeni karar satırı için eşik commit zamanı < ilk kod commit zamanı olmalı. Hedef **%100**; tek ihlal = başarısız.

**(f) Öldürme kriteri:** 4 hafta içinde protokolden geçecek hiçbir araç çıkmazsa (Ö1 nedeniyle bu muhtemel) protokolün kendisi Ö2'nin hükmüne bağlanır. Ayrı bir bakım yapılmaz.

---

## Özet tablo

| # | Öneri | Maliyet | Ölçülecek eşik | Kesim tarihi |
|---|---|---|---|---|
| Ö1 | Yeni araç moratoryumu, ≥3 tekrar kuralı | 0 | Forge-meta ≤ %10; pitch ≤ 11-08 | 11-08 |
| Ö2 | Forge öldürme kriteri dosyası | 15 dk | K1–K4 | 11-22 |
| Ö3 | Kapalı-kitap geri anlatma kapısı | 20 dk/pilot | ≥3/5, sonra ≥4/5 | Her pilot |
| Ö4 | olum-testcisi iptal, gapmine arşiv, makale-okuyucu batık | 3 satır | İptallere 0 token | 11-22 |
| Ö5 | K5 rakip bekçisi (yalnız DEVAM'da) | ~2 sa | Canary 2/2, ≤5 yanlış alarm/hafta | K5 hükmü + 4 hafta |
| Ö6 | maliyet-sayaci KABUL + hedef etiketleri | 1–2 sa | Sapma ≤ %0,5; eşlenmemiş ≤ %10 | 11-08 |
| Ö7 | Protokol: ikili karar, commit'li eşik, k≥3, ayrı denetçi | 30 dk | Eşik-önce-kod %100 | 11-22 |

## Kaynaklar
- METR deneyi: https://www.theregister.com/2025/07/11/ai_code_tools_slow_down/ · https://eweek.com/news/news-ai-tools-slow-developer-productivity-study
- Bastani vd., PNAS 2025: https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education · https://papers.ssrn.com/abstract=4895486
- Lee vd., CHI 2025: https://www.microsoft.com/en-us/research/?p=1135061
- Kosmyna vd., "Your Brain on ChatGPT" (preprint): https://www.media.mit.edu/publications/your-brain-on-chatgpt/
- Beel vd., Sakana AI Scientist değerlendirmesi: https://arxiv.org/abs/2502.14297
- Answer.AI, Devin ile bir ay: https://www.answer.ai/posts/2025-01-08-devin
- Anthropic, Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Anthropic, Writing effective tools for agents: https://www.anthropic.com/engineering/writing-tools-for-agents
- Hamel Husain, evals: https://www.oreilly.com/radar/podcast/generative-ai-in-the-real-world-getting-beyond-the-demo-with-hamel-husain/ · https://simonwillison.net/tags/hamel-husain/ · https://www.aakashg.com/hamel-shreya-ai-evals-step-by-step/
