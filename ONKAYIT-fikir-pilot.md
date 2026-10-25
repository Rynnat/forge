# Ön Kayıt: Fikir pilotu — "bana gerçekleştirebileceğim yüksek potansiyelli bir araştırma fikri ver" (2026-10-25)

Bu dosya pilot kodundan ÖNCE commit edilir. **PİLOT: n = 3 konu → karar yok, yön gösterir.**

## Kullanıcının iddiası (test edilen)
Bu işi Claude tek başına yaparsa:
- çok token harcar,
- kalite düşer.

Orkestrada ise ucuz çalgıcılar geniş tarar ve doğrular, Claude yalnız damıtılmışı yargılar. Sonuç hem daha ucuz hem daha iyi olmalı.

## Görev
Her konu için **3 araştırma fikri**. Her fikirde:
- başlık,
- boşluk (literatürde ne eksik),
- neden şimdi,
- 3. sınıf CMPE öğrencisinin 3–6 ayda yapabileceği ilk adım,
- dayandığı 2–5 çalışma (arXiv/DOI).

Kesim: bugün (2026-10-25); her şey sayılır.

**Konular** (altın setle ilgisiz, kullanıcının ilgi alanına yakın, 3 farklı alan):
- **T1:** non-invasive EEG brain-computer interfaces with deep learning
- **T2:** LLM-based agents for automated software testing
- **T3:** learning robotic manipulation from human video demonstrations

## Sistemler
- **A — Claude tek elden:**
  - Tek bir `claude -p --model opus` çağrısı, WebSearch + WebFetch.
  - İstem: konuyu araştır ve aynı biçimde 3 fikir ver.
  - Fikirlerin yeni olduğunu web'de kontrol et.
- **B — Orkestra:**
  1. orkestra v0 (donmuş kod) konuyu tarar → 80 kart + özet.
  2. Opus şef **yalnız bu özetten** 6 aday fikir üretir.
  3. 6 Haiku web işçisi her aday için paralel "daha önce yapılmış mı" taraması yapar.
  4. Opus şef bu kanıtlarla en iyi 3 fikri seçer.
  - Şefin bağlamına yalnız damıtılmış girdi girer.

## Ölçümler (denetçiler sistemi yazandan farklı model: Sonnet)
1. **Token ağırlığı:** konu başına API-liste-fiyatı ağırlıklı token. maliyet-sayaci / CLI logu ile ölçülür.
2. **Genişlik:** sistemin gerçekten incelediği farklı çalışma sayısı.
   - B: okuyucunun okuduğu aday sayısı.
   - A: raporladığı ya da açtığı kaynak sayısı (tahmini; web_arama sayısı ile birlikte raporlanır).
3. **Yenilik:** bağımsız Sonnet + web denetçisi her fikre şu hükmü verir:
   - YENİ / KISMEN (yakın iş var, fark anlamlı) / YAPILMIŞ (aynısı yayımlanmış).
   - En yakın işi kanıt olarak verir.
   - Oran = (YENİ + KISMEN) / 3.
4. **Dayanak:** fikirlerde gösterilen çalışmalar gerçek mi?
   - Kodla kontrol edilir: arXiv / Crossref çözümleme.
   - Uydurma kaynak sayısı raporlanır.
5. **Kör ikili tercih:**
   - Her konu için Sonnet hakem iki sistemin 3'er fikrini görür. Sistem adı yok, sıra rastgele, tohum kayıtlı.
   - Rubrik: potansiyel etki, yenilik, öğrenci için yapılabilirlik, dayanağın sağlamlığı.
   - Çıktı: hangi set daha iyi + gerekçe.
   - Kullanıcı isterse aynı kör karşılaştırmayı kendisi yapar. Kullanıcının hükmü Sonnet'inkinden önce gelir.

## Beklenti (yön; pilot olduğu için karar değil)
- **H1:** B'nin token ağırlığı ≤ %60 × A.
- **H2:** B'nin YAPILMIŞ sayısı ≤ A'nınki.
- **H3:** kör hakem 3 konudan ≥ 2'sinde B'yi seçer.
- **H4:** B'de uydurma kaynak 0.

Sonuç bu dört maddeyle "B lehine / A lehine / karışık" diye özetlenir. Gerçek kabul için n ≥ 30 konuluk ayrı bir ön kayıt gerekir.

## Bütçe
- **Tahmini ağırlık:**
  - B: 3 × (~$0,65 orkestra + ~$0,4 fikir adımı).
  - A: 3 × (~$1–2).
  - Denetim: ~$3.
  - **Toplam ≈ $12.**
- Kullanıcı deneyi açıkça istedi (2026-10-25: "istersen bir deney yaparak küçük çaplı bir ispatta bulun").

## Çalıştırma düzeni
- Tüm konuların B toplama aşaması tek tek ve arXiv'e giden başka iş yokken koşar.
- A'nın WebFetch'i aynı IP'den arXiv'e gidebilir; A bu yüzden B'den sonra koşar.
- Denetim en sonda yapılır.
