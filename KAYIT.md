# Forge Araç Sicili

> 2026-10-25 hakem raporundan sonra düzeltildi (`HAKEM-RAPORU.md`).
> - gapmine'ın eşiği, sonuçlar görüldükten SONRA yazılmıştı. Bu protokol ihlali; kayıt dürüstçe RED'e çekildi.
> - Bundan sonra eşikler git commit'iyle zaman damgalanacak.

| Araç | Ne yapar | Durum | Kabul eşiği | Kanıt |
|---|---|---|---|---|
| maliyet-sayaci | Transkriptlerden token/maliyet raporu | Kabul testi `ONKAYIT-maliyet-sayaci.md` ile yeniden yapılıyor (protokol v2) | Ön kayıt dosyasında | Hakem: 19/19 ajanda toplamlar bağımsız betikle birebir; fiyatlar resmi sayfayla aynı. Resmi `subagent_tokens` = son çağrının bağlamı (11/15'te %0,00 sapma) |
| gapmine | İddia → literatür ön taraması | **ARŞİV** (2026-10-25, YARGI B-18). Hüküm aracı olarak RED. Geri açma koşulu: iki pilot da ELE ve elle yapılan aday taraması > $25 tutarsa; önce insan kaynaklı 10 iddialık altın set kurulur | (sonradan yazıldı, geçersiz) | DENETIM.md: recall %61, öldürenlerde 3/6. v2 canlı koşulmadı. Altın set kirli: v2'yi yazan ajan, makale adlarını içeren DENETIM.md'yi okudu |
| makale-okuyucu | PDF → kanıtlı kart | Kuruldu v0.1 (67 test; 36 sayfalık makale $0.04, 90 sn); kabul testi yapılmadı, DONDURULDU (pilotlar önce) | Bağımsız sorularda ≥%85 doğruluk; token ≤ 1/10. ("Uydurma alıntı %0" eşiği tautolojik olduğu için çıkarıldı) | — |
| olum-testcisi | Şüpheci aday öldürme ajanı | **İPTAL** (2026-10-25). 3 iddialık eşik bilgi taşımıyor (tesadüfle tutma olasılığı 0,34); iş yalnız 1 kez yapıldı | Bilinen 3 iddiada aynı hüküm; token ≤ 1/3 | — |

## gapmine'ı çözmek için ne gerekir
1. OpenAlex anahtarı.
2. Denetim bulguları #1–#3: arXiv sorgu kurgusu, top-N, tam metin seçimi.
3. **Yeni ve görülmemiş bir altın set.**


## Planlanan: ders-modu (literatür öğrenme)
Durum: plan aşamasında. Başka araçlar yazıldıktan sonra ele alınacak (kullanıcı kararı, 2026-10-25).

**Katmanlar:**
1. **Basit (~5 dk):** makale günlük dille 5 cümlede, "neden önemli" sorusuna bir benzetmeyle cevap.
2. **Kavramlar (~20 dk):** terimler, adım adım yöntem, sayılarla ana sonuç + 3-5 soruluk kendini sınama.
3. **Tam kapsam / savunma:**
   - Makalenin kendisiyle birlikte okunur; sayfa numaralı okuma haritası.
   - Bizim çalışmayla ilişkisi: neyi farklı yapıyoruz.
   - Olası hakem soruları ve cevaplarının sayfaları.
   - Son adım: kullanıcı makaleyi kendi cümleleriyle geri anlatır.

**Kurallar:**
- Kritik iddialar sayfa numarasıyla verilir.
- Makale okumanın yerine geçmez; okumayı yönlendirir.
- Önce tek bir makaleyle elle denenir (Mariposa). İşe yararsa araçlaştırılır ve kabul protokolünden geçer.
