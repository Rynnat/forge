# Ön Kayıt: Orkestra v0 ile Tek Opus Ajanının Karşılaştırması (2026-10-25)

Bu dosya, orkestra kodunun ve altın setin oluşturulmasından ÖNCE commit edilir.

## Soru
Geniş kapsamlı bir literatür araştırmasında Forge orkestrası (Opus şef + ucuz çalgıcılar), Claude'un bugünkü yönteminden (tek bir Opus ajanı) daha geniş ve daha ucuz sonuç verir mi? Kalite kaybı olur mu?

## Görev ve altın set (insan yapımı)
- **Kaynak:** 2025-07 ile 2026-10 arasında yayımlanmış **30 survey veya SoK makalesi**.
  - Farklı CMPE alanlarından seçilir: en az 6 alan, tek bir alandan en fazla 6.
  - Seçimi, sistemi yazmayan ayrı bir ajan yapar.
- **Soru:** survey'in konusu, bir araştırma sorusu olarak yazılır. Örnek: "X alanındaki en önemli çalışmalar ve açık problemler neler?"
- **Kesim tarihi:** survey'in ilk yayın tarihinden 1 ay öncesi. Sistemler yalnız bu tarihten önce yayımlanmış çalışmaları raporlayabilir. Böylece survey'in kendisi ve kaynakçasını kopyalama yolu kapanır.
- **Altın:** survey kaynakçasındaki, kesimden önce yayımlanmış ve arXiv id ya da DOI ile çözülebilen çalışmalar.
- **Saklama:**
  - Altın set `C:\Users\LENOVO\Projeler\forge-altin\` adlı ayrı bir repoda tutulur.
  - Orkestrayı yazan ajan bu klasörü okumaz.
  - Altın dosyanın SHA-256 hash'i, oluşturulduğu gün bu dosyanın sonuna commit edilir.

## Sistemler
- **A — Taban çizgisi:** tek bir Opus general-purpose alt-ajanı. Standart prompt: "Kesim tarihinden önceki en önemli 30 çalışmayı önem sırasıyla, arXiv/DOI ile listele".
- **B — Orkestra v0:**
  - Opus şef planlar ve sonunda sıralar.
  - Ucuz çalgıcılar toplar, okur ve damıtır: arXiv, DBLP, Crossref, (anahtar varsa) OpenAlex, Haiku web arama işçileri, atıf takibi.
  - Çıktı: aynı biçimde 30 çalışma + şefe giden özet.

## Metrikler
- **Birincil — recall@30:** sistemin listelediği 30 çalışmadan kaçı altın kaynakçada. Altına bölünür: |altın ∩ liste| / min(30, |altın|). Eşleme arXiv id, DOI ya da normalize başlık (≥0,90) ile yapılır.
- **Maliyet:** soru başına teorik $. maliyet-sayaci ve CLI maliyet logları ile ölçülür.
- **Bağlam:** şefe ya da ana oturuma dönen son raporun token sayısı.
- **Sadakat:**
  - B'nin raporlarından rastgele 30 iddia (çalışma + gerekçe cümlesi) seçilir.
  - Farklı bir model (Sonnet) bunları kaynağa karşı denetler.
  - Kontrol edilenler: çalışma gerçekten var mı, gerekçe kaynakta destekleniyor mu?
- **Kararlılık:** B, rastgele seçilmiş 10 soruda k=3 kez koşulur. recall@30'un soru içi standart sapması raporlanır.

## Eşikler: KABUL için hepsi gerekli
1. **Eşli recall farkı:** n=30 soruda ortalama(B − A) **≥ +10 puan** VE tek yönlü işaret testi **p < 0,05**.
2. **Maliyet:** ortalama $(B) **≤ %50** × ortalama $(A).
3. **Sadakat:** **≥ 28/30** destekleniyor (Wilson alt sınırı ≥ 0,79) VE **uydurma çalışma = 0**.
4. **Bağlam:** B'nin son raporu ortalama **≤ 4000 token**.

## Öldürme ve RED
- 1–4'ten herhangi biri tutmazsa → **RED**.
- Ortalama(B − A) < 0 ya da $(B) > $(A) ise → v0 **ARŞİV**. Dersler yazılır; `OLUM-KRITERI.md`'ye göre tek bir v1 hakkı doğar.
- **Ara durdurma:** ilk 10 soruda ortalama(B − A) ≤ −10 puan çıkarsa kalan koşular yapılmaz ve hüküm RED olur. Bu bir kez bakılır, tek kontroldür.

## Bütçe
- Taban çizgisi (A) yaklaşık 30 × ~$1,3 = ~$40 teorik tutar. Bu, tek iş tavanını ($10) aştığı için **kullanıcıya sorulur**.
- B'nin hedefi soru başına < $0,65.

## Altın set hash
- `forge-altin/altin.json` SHA-256: `3aa01a9fe2b04af88eca025342bb954de4f76e0108125228e13ef50b98ec8681`
  (forge-altin commit `817ca51`, 2026-10-25). Diskteki dosya ve git blob'u aynı hash'i verir; `.gitattributes` ile json satır sonu sabit.
- 30 survey, 10 alan × 3; 4089 altın kaynak. Kalite kontrolü 3×10: 2/30 hata (kesik DOI bir bildiri kitabına çözülmüş),
  sistematik süzgeçle 26 kayıt (%0,6) atıldı; süzgeç sonrası yeni örneklem çekilmedi. Kesim ihlali 0/30.
- Altını, orkestrayı yazan/koşan oturum görmedi; bu oturum yalnız hash ve sayıları gördü.

## Açıklama eki — 2026-10-25 (hiçbir deney koşusundan ve altın set görülmeden ÖNCE)
Puanlayıcı yazılırken iki belirsizlik çıktı. Eşikler değişmedi; yalnız okunuşları sabitlendi.
1. **Sadakat eşiği:** bağlayıcı ölçüt sayıdır: **≥ 28/30 destekleniyor**. Parantezdeki Wilson değeri
   betimseldir: z = 1,96 ile 28/30 → 0,787 (≈ 0,79). Wilson alt sınırı raporlanır ama ayrı bir eşik değildir.
   Kontrol edilemeyen iddia "desteklenmiyor" sayılır.
2. **Eşleme sırası:** önce arXiv id, sonra DOI, sonra başlık (≥ 0,90). Başlık eşleşmesi, sayı / roma rakamı /
   farklı arXiv id çakışmasında reddedilir ("Part I" ≠ "Part II"). Her altın ve her liste öğesi en çok bir kez eşleşir.
   Altını boş soru eşli istatistikten çıkarılır; işaret testinde eşitlik = fark tam 0.

## Değişiklik eki — 2026-10-25: taban çizgisi A1 + A0 (kullanıcı kararı; altın set görülmeden, deney koşusundan önce)
**Gerekçe:** Ön kayıttaki standart istemle (D2'de tek deneme) Opus **hiç web araması yapmadı**: 30 çalışmayı hafızadan
yazdı, $0,16 / 68 s. Ön kayıt ise A'yı "Claude'un bugünkü yöntemi, araştırma yapan tek bir Opus ajanı" olarak tanımlıyor
ve bütçeyi ~$1,3/soru varsayıyordu. Hafızadan cevaplayan bir A'ya karşı maliyet eşiği (≤ %50) ölçtüğü şeyi kaybediyordu.
- **A1 — birincil (KABUL / RED buna göre):** aynı soru ve kesim metni + "web araması ZORUNLU, her çalışmanın başlığını,
  tarihini ve kimliğini web'de doğrula" + B şefinin kullandığı "kesimden hemen sonra yayımlanacak dikkatli bir uzman
  survey'inin atıf yapacağı türden" çerçevesi (iki sistem aynı hedef tanımını alsın diye). İstem: `orkestra/deney/taban.py` → `PROMPT_A1`.
- **A0 — ek, betimsel:** ön kayıttaki istem aynen (`PROMPT`). Karar vermez; raporlanır. "Orkestra, hafızadan cevaplayan
  Opus'u recall'da geçebiliyor mu?" sorusuna cevap verir.
- Eşikler, n, metrikler, altın set **değişmedi**. Tek model/araç: `claude -p --model opus`, yalnız WebSearch + WebFetch.
- Bütçe: A1 ~30 × (deneme ile ölçülecek) + A0 ~30 × $0,16 ≈ $5. Toplam > $10 olduğu için koşu yine kullanıcı onayına bağlı.
