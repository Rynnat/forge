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
(Altın set oluşturulunca buraya eklenecek.)
