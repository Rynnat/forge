# YARGI: Forge geliştirme önerileri (P-A, P-B, P-C), 2026-10-25

Yargıç hiçbir dosyayı değiştirmedi; yalnız bu rapor yazıldı. Kontroller salt okunur yapıldı: `sed`/`grep`/`diff`, Wilson ve binom hesabının yeniden yapılması, `maliyet_sayaci.py sessions|agents --json` (yalnız sayısal alanlar) ve 3 dış sayfanın okunması.

Raporların mercekleri şöyle: P-A metodoloji, P-B mühendislik ve entegrasyon, P-C strateji ve batık yatırım. Hangi raporun kimden geldiğine bakılmadı.

---

## 0. Tek paragraf hüküm

Üç rapor aynı teşhiste buluşuyor: Forge bugün bir onay damgası, kalite kapısı değil. Ayrıldıkları yer çözümün **büyüklüğü**.
- P-A'nın planı ~26 saat ve ~12 saat insan etiketi istiyor.
- P-B'nin planı ~28–35 saat ve ~1 M token istiyor.
- P-C ise "durun, önce pilot" diyor.

Kanıt P-C'den yana. Bunun dört nedeni var:
1. Forge'da ölçülecek araç kalmadı. gapmine RED/donduruldu, makale-okuyucu donduruldu, olum-testcisi beklemede, maliyet-sayaci da neredeyse bitti.
2. P-B'nin altyapı önerilerinin çoğu, kendi öldürme kriteriyle daha doğarken ölüyor (§2, Ç1).
3. Asıl hedefe (makale) hizmet eden tek iş, K5 pilotu, şu an koşuyor. Base aşaması 1505/1505 bitti, seed aşaması 50/1441'de (`pilot-k5/data/run_log.txt`).
4. Bu öneri turunun kendisi de meta-iş. Oturum `76053f18` P-C'nin yazdığı andan bu yana $74,13'ten $79,53'e çıktı.

P-A ve P-B'nin önerileri yanlış değil. Çoğu doğru ama **erken**. Bu yüzden "SONRA" listesine, açık tetikleyicilerle giriyorlar.

---

## 1. Kanıt kontrolü

Her rapordan en az 3 iddia bizzat doğrulandı. "✓" doğrulandı, "~" küçük sapma ya da abartı, "?" belirsiz (kontrol edilmedi ya da edilemedi) demek.

### P-A (8 iddia kontrol edildi)
| İddia | Sonuç | Not |
|---|---|---|
| `README.md:14` (eşik önceden), `:18` (ŞARTLI), `:20` (regresyon) | ✓ | Satırlar birebir tutuyor. |
| `DENETIM.md:11, 58, 121, 125, 130, 138, 154` | ✓ | Yedisi de söylenen içerikte. Örnek: :130'da "yanlış YES %23", :58'de "olum-testi raporlarından çıkarıldı". |
| gold.json'da KernJC, RingGuard, Mariposa için arXiv id `null` | ✓ | Kontrol edildi. |
| Wilson aralıkları: 22/36 → [.45,.75], 3/6 → [.19,.81], 6/10 → [.31,.83], 7/10 → [.40,.89] | ✓ | Yeniden hesaplandı, aynı çıktı. |
| Kör taban %70'i yenmek için gereken: n=10'da 10/10, n=30'da 26/30, n=50'de 41/50 | ✓ | Tek yönlü binom testi. p değerleri sırasıyla .028, .030, .040. |
| 3/3 tesadüfi uyuşma olasılığı 0,34 | ✓ | 0,7³ = 0,343. |
| "İşaret testi: 6/6 aynı yönde, p = 0,03" | ~ | Bu çift yönlü değer. Tek yönlü değer 0,016. Sonucu değiştirmiyor. |
| Makale-okuyucu eşiği "≥27/30 (Wilson alt sınırı ≥ 0,75)" | ~ **iç çelişki** | 27/30'un Wilson alt sınırı **0,744**. Eşik kendi koşulunu sağlamıyor. Doğrusu 28/30: alt sınır 0,79. |
| 3 forge commit'i 13:13–13:22 arasında; hiçbiri koşudan önce atılmış bir eşik commit'i değil | ✓ (kapsam notuyla) | Forge için doğru. Ama `akademik-bosluk` commit'i b4b2b53 (13:13), K5'in D0 adımından (13:18) **önce** atılmış. Yani pilot için ön kayıt aslında yapıldı. P-A bunu görmüyor. |
| Dış kaynak: Anthropic "Demystifying evals for AI agents" (pass^k, insan kalibrasyonu, "Read the transcripts!", 20–50 görev, regresyon ~%100) | ✓ | Sayfa okundu (9 Oca 2026). Beşi de var. |
| Husain: "etiket başına 30–50, 60'ın altında aralıklar fazla geniş" | ? | Kontrol edilmedi. |

**Abartı:** P-A'nın asıl sorunu kanıt değil, **orantı**. Örnekler:
- Held-out şifreli zip ve "parola yalnız kullanıcıda" (A2).
- Kabul başına 60 insan etiketi (A3).
- Her ölçümde üçlü taban (A5).

Bunların hepsi, önümüzdeki 4 hafta içinde ölçülecek **hiçbir aracı olmayan** bir sistem için tasarlanmış. Tek kullanıcılı, kendini kandırmaya karşı korunması gereken bir sistemde tehdit "rakip" değil, "kendi kendine kanmak". Buna git commit'i yeter. P-A'nın "git tarihi elle değiştirilebilir" itirazı doğru ama bu tehdit modeline göre aşırı.

### P-B (9 iddia kontrol edildi)
| İddia | Sonuç | Not |
|---|---|---|
| makale-okuyucu `llm.py` 336 satır, gapmine'ınki 395; başlıkta "kopyalandı" yazıyor; ad normalize edilince 213 fark satırı | ✓ | `diff` ile birebir 213. |
| `quotecheck.py` 91'e karşı 79 satır, 14 fark satırı | ✓ | |
| `maliyet_sayaci.py:23` VERI_SATIRI, `:448-454` tools modu yalnız gapmine raporlarını ve `*/logs/maliyet*` dosyalarını okuyor | ✓ | |
| `grep VERSION` maliyet-sayaci'da boş dönüyor | ✓ | |
| `fetch.py:161-170` openalex_work anahtarsız ve kendi `get`'iyle çalışıyor | ✓ | |
| `store.py:59-64` resolve sürüm kontrolü yapmıyor | ✓ | |
| card.json 17.748 ve 17.857 B; ask_a3.json 2.462 B; ask_b1.json 772 B | ✓ | Bayt değerleri birebir. Token karşılıkları tahmin. |
| `~/.claude/skills` altında yalnız `synced` var; agents klasöründe yalnız Epic/AMD ajanları var | ✓ | |
| Claude Code belgesi: açıklama 1.536 karakterde kesiliyor; sıkıştırmada her skill'in ilk 5.000 token'ı korunuyor; `scripts/` "executed, not loaded"; `context: fork` | ✓ | code.claude.com/docs/en/skills okundu. |
| Alt-ajan `hooks: PreToolUse` ile okuma yolu engellenebilir (B7) | ? | P-B kendisi "denenmedi" diyor. |

**Abartı:** Ölçülen her şey doğru. Ama ölçülen şey **sorunun varlığı**, **sorunun önemi** değil. Üç örnek:
- **Kod kopyası (B3):** Gerçek, ama yalnız bir canlı tüketicisi var, çünkü gapmine donduruldu. P-B'nin öldürme kriteri "60 günde 3. tüketici yoksa iptal" diyor. Ö1/Ö4 ile birlikte bu kriter neredeyse kesin tetiklenir.
- **OpenAlex çakışması (B4):** Varsayımsal. makale-okuyucu OpenAlex'e yalnız DOI başına tek istek atıyor; gapmine de koşmuyor.
- **`read --json` 5k token (B2):** Gerçek, ama dondurulmuş bir araçta.

### P-C (9 iddia kontrol edildi)
| İddia | Sonuç | Not |
|---|---|---|
| gapmine v2 + denetim maliyeti $27,23 | ✓ | a39ba301 $13,21 + a38f17e9 $14,02. |
| Ölüm testi R1–R5 maliyeti $10,73 | ✓ | Toplam $10,72; yuvarlama farkı. |
| Eşlenmeyen pay %35 ($26,21) | ✓ | 11,91 + 14,30 = 26,21; 26,21 / 74,13 = %35,4. |
| Oturum toplamı $74,13; tüm oturumlar $1.624,74 | ✓ (zamanla) | Şimdi $79,53 ve $1.631,5. Aradaki fark bu yargılama turu. |
| 00-SKOR'un "önce 1 günlük pilot" kararı 21:18'de | ✓ | Dosyanın mtime'ı 00:18 +03, yani 21:18 UTC. İçerik 00-SKOR satır 20'de. |
| K5 eşiği b4b2b53'te commit'li; D0 ve D1 13:18'de | ✓ | |
| Karar günlüğünde 14 analiz kararı var | ✓ | D1'de 14 madde. |
| Beel vd. 2502.14297: Sakana'nın literatür taraması köklü fikirleri "yeni" diye etiketliyor | ✓ / ~ | Özet bunu söylüyor. "Yüzeysel anahtar kelime araması" ifadesi özette yok; gövdede var mı kontrol edilmedi. |
| METR deneyi (%19 yavaş, %20 hızlı sanma); Bastani PNAS 2025 (sınav notu −%17); Lee vd. CHI 2025 (n=319); Answer.AI–Devin (20 görevde 3 başarı) | ✓ (bilgiyle) | Bilinen sonuçlarla tutarlı; bu oturumda yeniden açılmadı. |
| "Son ~13 günün tüm oturumları" | ~ | En pahalı oturum (b64869a9, $432,7) 2026-09-28'de başlamış. Pencere 13 gün değil, ~27 gün. Toplam rakam yine doğru. |
| Husain'in "~%70 geçme oranı daha anlamlı" ifadesi | ? | Kontrol edilmedi. Ö7'nin kararı buna dayanmıyor. |

**Abartı:** P-C Ö4 makale-okuyucu için "batık sayılsın" diyor. Bu zaten KAYIT'ta DONDURULDU olarak duruyor; yeni bir karar değil, yalnız yeniden ifade. Ö1'in "Forge-meta ≤ %10" eşiği ise bugün **ölçülemez**: tüm oturumlar tek proje klasöründe (`C--Users-LENOVO`), etiket katmanı yok. Ö1 bu yüzden Ö6'ya bağımlı. P-C bunu kendisi de söylüyor.

### Yargıcın ek bulgusu (karar için önemli)
- maliyet-sayaci'ya göre 50 oturumun tamamı tek proje klasöründe.
- En pahalı iki oturum ($432,7 ve $318,2) toplam harcamanın **%46'sı**. Hangi projeye ya da ajana gittikleri araçtan **okunamıyor**.
- Yani "hangi ajan pahalı, hangisi melezleştirilmeli" sorusunun bugün **verisi yok**. Bu bulgu §6'nın temeli.

---

## 2. Çelişkiler ve çözümleri

**Ç1: İnşa et (P-B) mi, dondur (P-C Ö1/Ö4) mi?** Bu ana çelişki.
- **P-B'nin önerdikleri:**
  - Skill hattı.
  - forge-core.
  - Kota defteri.
  - Koşu günlüğü.
  - 3 ajanlı hat.
  - Hepsi birlikte ~28–35 saat.
- **P-C'nin önerdiği:** Pilotlar hüküm alana kadar yeni araç ya da özellik yok; araç ancak gerçek işte ≥3 kez tekrarlanan bir elle işten doğar.
- **Kanıt P-C'den yana:**
  1. Kabul edilmiş araç sayısı 0. Bağlanacak bir şey yok, maliyet-sayaci hariç.
  2. P-B'nin ölçtüğü sorunların hepsi ya dondurulmuş araçlarda ya da varsayımsal çakışmalarda (§1).
  3. Hakemin "meta-iş asıl işi yiyor" bulgusu sayıyla duruyor. gapmine ve denetime %37 gitti, karşılığında 0 KABUL çıktı. Pilot başlar başlamaz da ilerledi.
  4. P-B'nin kendi öldürme kriterleri (B3: "3. tüketici yok"; B1: "tek araç kalırsa `sistem/` hattı kaldırılır") bugünkü durumda kendiliğinden tetikleniyor.
- **Karar: P-C kazanır.**
  - P-B'nin 3, 4, 5 ve 7. önerileri **YAPMA (şimdilik)**.
  - P-B'nin 1., 2. ve 6. önerileri **SONRA**, tetikleyiciyle.
- **P-B'den alınan doğru ilke:** "Araç = CLI çekirdek + ince skill, MCP yok". Bu, araç gerçekten doğduğunda geçerli kalıp. Belgeyle de doğrulandı.

**Ç2: Ağır protokol (P-A) mı, sade protokol (P-C Ö7) mı?**
- **Ortak zemin:**
  - Eşik commit'te durur.
  - ŞARTLI ya kalkar ya da rol eşiğine bağlanır.
  - Stokastik araçta k≥3 koşu.
  - Ayrı bir denetçi.
- **Ayrıldıkları yer:**
  - P-A: n≥30, insan etiketi 30P+30N, held-out zip, üçlü taban, KANIT şeması.
  - P-C: 30 dakikalık README düzeltmesi.
- **Karar: P-C'nin 4 kuralı bugün uygulanır.** P-A'nın istatistik kuralları da ucuz oldukları için bugün **metin olarak** ön kayıt şablonuna girer:
  - Wilson alt sınırı.
  - n < 30 ise "pilot, karar yok".
  - Taban çizgisiyle eşli kıyas.
- **Ertelenen:** P-A'nın pahalı altyapısı (altın karantinası, 60 insan etiketi, üçlü taban, A/B). Bir araç gerçekten kabul ölçümüne geldiği gün devreye girer.
- **Gerekçe:** Altyapının değeri, ölçülecek araç sayısıyla orantılı. Bu sayı önümüzdeki 4 hafta için ~0.

**Ç3: Eşik kilidi nasıl kurulsun?**
- Üç seçenek var:
  - P-A: SHA-256 + koşu log'u.
  - P-B: `ESIK.json` + pre-commit + `kontrol.ps1`.
  - P-C: git log ile "eşik commit'i ilk kod commit'inden önce" kontrolü.
- **Karar: P-C'nin yöntemi**, P-A'nın şablon alanlarıyla birlikte.
- **Gerekçe:**
  - Tehdit kendini kandırmak, kasıtlı sahtecilik değil.
  - Git zaten kuruldu ve çalıştı: K5 eşiği 13:13'te, koşu 13:18'de.
  - Pre-commit ve hook altyapısı ancak çok sayıda araç olduğunda değer.

**Ç4: Bağımsız denetçi kim olsun?**
- Üç seçenek var:
  - P-B: aynı aileden de olabilen "farklı bir `model:`".
  - P-A: farklı aile + insan kalibrasyonu.
  - P-C: farklı model ya da öğrencinin kendisi + en az bir ölçümün elle yapılması.
- **Karar: P-C + P-A.** İnsan (öğrenci) altın kaynaktır; mümkünse farklı aileden bir model eklenir.
- **P-B'nin "aynı aile, farklı model" seçeneği yetersiz.** Panickssery vd. 2024, kendi-tercih yanlılığının kendini tanımayla ilişkili olduğunu gösteriyor. Aynı ailedeki farklı boyutlu modellerde bu yanlılığın ne kadar sürdüğü **belirsiz**. Bu belirsizlikte ucuz olan güvenli seçenek insan.
- Öğrencinin elle ölçmesi Hedef 2'ye (öğrenme) de hizmet ediyor.

**Ç5: makale-okuyucu'nun yeri.**
- P-B onu ikinci bağlanacak araç sayıyor ve çıktı bütçesini istiyor.
- P-A yorum-sadakati kabul testi istiyor.
- P-C "≥10 makalelik gerçek ihtiyaç doğana kadar dondur" diyor.
- **Karar: P-C.** KAYIT zaten DONDURULDU diyor. P-A'nın yorum-sadakati metriği ve P-B'nin `--json` bulgusu, araç çözüldüğü gün ön kayda girecek maddeler olarak saklanır.

**Ç6: Forge'un öldürme tarihi ve ölçütü.**
- P-C Ö2: 4 hafta (11-22), K1 = "maliyet-sayaci dışında ≥1 KABUL'lü araç kullanılıyor".
- P-A: 60 gün, "≥1 KABUL ve ≥1 RED".
- **İç çelişki:** P-C'nin kendi Ö1'i (moratoryum) 11-22'ye kadar yeni bir KABUL'ü fiilen imkânsız kılıyor. Bu yüzden K1 tasarım gereği başarısız olur. K1, Forge'u değil moratoryumu ölçmüş olur.
- **Karar:**
  - 11-22'de yalnız K2, K3 ve K4 ölçülür (tanımlar §5, madde 2).
  - K1 (yeni bir aracın gerçek kullanımı) P-A'nın 60 günlük ufkuna, yani **2026-12-24**'e taşınır.
  - Kural: K3 tutmazsa DONDUR. K2 ve K4 birlikte tutmazsa ÖLDÜR.

**Ç7: P-C'nin içindeki çelişki (Ö1 ile Ö6).**
- Ö1 "mevcut araçlara özellik eklenmesin" diyor. Ö6 ise maliyet-sayaci'ya etiket ve `ozet --hafta` ekliyor.
- **Karar: İstisna geçerli.** Ö6, Ö1'in kendi eşiğini ölçen alet; o olmadan moratoryum denetlenemez. Ama istisna en küçük biçimde tutulur:
  - Hakemin istediği sütun.
  - Bir CSV dosyası.
  - Toplayan tek bir alt komut.
  - Başka hiçbir şey eklenmez.

---

## 3. Birleştirilmiş öneriler (tekrarlar)

| Kod | Birleşik öneri | Kaynaklar |
|---|---|---|
| **B-1** | Önce pilot ve moratoryum: yeni araç yok; araç ancak ≥3 elle tekrardan doğar; K5/K8 hükmü ve hoca pitch'i | C-Ö1, C-Ö4 (kısmen), hakem §5 |
| **B-2** | maliyet-sayaci'yi bitir: "son bağlam + çıktı" sütunu, regresyon testi, KABUL, hedef etiketi | C-Ö6, A7 (ilk regresyon), B5 (tools körlüğü), hakem §5.5 |
| **B-3** | Ön kayıt ve sade protokol: eşik commit'i koddan önce; ikili karar (ŞARTLI ancak önceden yazılmış rol eşiğiyle); k≥3; Wilson alt sınırı; n<30 ise karar yok; ayrı denetçi; README'deki hayalet klasörleri sil | A1, A4 (metin kısmı), C-Ö7, B6 (eşik kilidi fikri), B7 (denetçi) |
| **B-4** | Forge'un kendi öldürme kriteri | C-Ö2, A'nın "Forge için öldürme kriteri" bölümü |
| **B-5** | Öğrenme kapısı: önce tahmin, sonra kapalı kitap geri anlatma | C-Ö3, KAYIT'taki ders-modu katman 3 (elle) |
| **B-6** | Bağımsız yargıç ve insan kalibrasyonu | A3, B7 (denetçi), C-Ö7.4 |
| **B-7** | Altın set karantinası ve insan kaynaklı altın | A2, B7 (hook yasağı), C-Ö7.4 |
| **B-8** | Üçlü taban, getirme canary'si, negatif kontrol | A5 |
| **B-9** | Görev-sonuç metriği (yorum sadakati, aşağı akış A/B) | A6 |
| **B-10** | KANIT.md şeması, regresyon, pre-commit, transkript kotası | A7, B6 |
| **B-11** | Skill bağlama hattı (CLI + ince skill) | B1 |
| **B-12** | Çıktı bütçesi sözleşmesi | B2 |
| **B-13** | forge-core ortak paket | B3 |
| **B-14** | Ortak kota defteri ve HTTP önbelleği | B4 |
| **B-15** | Koşu günlüğü ve sürüm damgası | B5 |
| **B-16** | SPEC → inşa → denetim ajan hattı | B7 |
| **B-17** | K5 rakip bekçisi (deterministik, LLM'siz) | C-Ö5 |
| **B-18** | olum-testcisi iptal, gapmine arşiv | C-Ö4 |

---

## 4. Puanlama

Her ölçüt 1–5 arası. Maliyet sütununda 5 en ucuz demek.

| Kod | Hedef etkisi | Kanıt | Maliyet | Geri alınabilir | Ölçerek ilerle | Toplam |
|---|---|---|---|---|---|---|
| B-1 Önce pilot ve moratoryum | 5 | 5 | 5 | 5 | 5 | **25** |
| B-2 maliyet-sayaci bitir | 4 | 5 | 5 | 5 | 5 | **24** |
| B-3 Ön kayıt ve sade protokol | 4 | 5 | 5 | 5 | 5 | **24** |
| B-4 Forge öldürme kriteri | 3 | 4 | 5 | 5 | 5 | **22** |
| B-5 Öğrenme kapısı | 4 | 3 | 4 | 5 | 4 | **20** |
| B-18 olum-testcisi iptal, gapmine arşiv | 3 | 4 | 5 | 4 | 4 | **20** |
| B-17 Rakip bekçisi | 3 | 3 | 4 | 5 | 4 | **19** |
| B-6 Bağımsız yargıç | 3 | 4 | 2 | 5 | 4 | 18 |
| B-8 Üçlü taban, canary, negatif kontrol | 2 | 4 | 3 | 5 | 4 | 18 |
| B-11 Skill bağlama | 3 | 3 | 4 | 5 | 3 | 18 |
| B-12 Çıktı bütçesi | 2 | 4 | 3 | 5 | 4 | 18 |
| B-10 KANIT, regresyon, pre-commit | 2 | 4 | 3 | 5 | 4 | 18 |
| B-9 Görev-sonuç, A/B | 3 | 4 | 1 | 5 | 4 | 17 |
| B-7 Altın karantinası | 3 | 4 | 2 | 4 | 4 | 17 |
| B-15 Koşu günlüğü | 2 | 4 | 3 | 5 | 3 | 17 |
| B-13 forge-core | 1 | 4 | 2 | 4 | 2 | 13 |
| B-14 Kota defteri | 1 | 3 | 1 | 4 | 2 | 11 |
| B-16 Ajan hattı | 2 | 2 | 1 | 4 | 2 | 11 |

---

## 5. Nihai karar

### ŞİMDİ YAP (3)

**1. Önce pilot: K5'i bitir, K8'i koş, pitch'i hazırla; moratoryum yürürlükte (B-1). Öğrenme kapısı bu maddeye bağlı (B-5).**

Yeni araç yazılmaz, mevcut araçlara özellik eklenmez. Tek istisna 2. madde. Araç fikirleri yalnız bir "istek günlüğü"ne tek satır olarak yazılır.

K5 hükmünden sonra ve pitch'ten önce, öğrenci 20 dakikalık bir kapalı kitap geri anlatma yapar. Konuları:
- Pilot neyi ölçtü?
- Eşik neden bu değer?
- Sonuç hangi durumda yanlış olabilir?
- 3 hakem sorusunun cevabı.

Öğrenci ayrıca K8 pilotundan **önce** tahminini commit eder.

Ön kayıt (bugün commit edilir):
- **Metrik ve eşikler:**
  - K5 hükmü (ELE/ARADA/DEVAM) **≤ 2026-10-29**. K5'in kendi D1 eşikleri değişmez.
  - K8 pilot hükmü + 1 sayfalık pitch + hoca görüşme isteği gönderilmiş **≤ 2026-11-08**.
  - Bu süre boyunca etiketli harcamada forge-meta payı **≤ %10**. Ölçüm 2. maddenin etiketleriyle yapılır.
  - Geri anlatma: K5'ten sonra rubrikte **≥ 3/5**, pitch'ten önce **≥ 4/5**. Rubrik bugün commit edilir.
- **Öldürme ve gevşetme kriterleri:**
  - **Moratoryum gevşer:** pilotlardan biri DEVAM çıkarsa ve 2 hafta içinde aynı elle iş istek günlüğünde ≥3 kez görülürse. O zaman yalnız o iş için araç ön kaydı açılır.
  - **Araç fikri kalıcı iptal edilir:** 4 hafta içinde 3 tekrara ulaşmazsa.
  - **Moratoryumun kendisi başarısız sayılır:** 11-08 kaçarsa ve aynı dönemde forge-meta payı > %10 ise. Bu durumda 4. maddedeki Forge DONDUR kuralı öne çekilir.
  - **Geri anlatma kapısı:**
    - İki ardışık geri anlatma ≤ 2/5 çıkarsa asistan yeni analiz kararı üretmeyi durdurur.
    - Kapı 2 kez atlanırsa Hedef 2 "ölçülmüyor" olarak dürüstçe yazılır.
    - P-C'nin "3 kez" sınırı 2'ye sıkılaştırıldı, çünkü bu 2 hafta içinde en fazla 2 pilot var.

**2. maliyet-sayaci'yi düzeltilmiş protokolle kabul et. Bu, yeni protokolün ilk gerçek sınavı (B-2 + B-3 + B-4).**

Yapılacaklar sırayla:
1. **README protokolünü düzelt (~30 dk):**
   - Eşik commit'i ilk kod ya da koşu commit'inden önce olmalı.
   - Karar ikili: KABUL ya da RED. ŞARTLI yalnız ön kayıtta rol eşiği yazılmışsa verilir.
   - Stokastik araçta k≥3.
   - Eşik "Wilson alt sınırı" ya da "eşli fark" biçiminde yazılır.
   - n < 30 ise "pilot, karar yok".
   - Denetçi farklı bir aileden model ya da öğrencinin kendisidir.
   - README'deki `kanit/`, `sistem/` ve `KANIT.md` vaatleri silinir.
2. **`ONKAYIT-maliyet-sayaci.md` yaz ve commit et.** Kod değişikliğinden **önce**.
3. **Kodu değiştir:**
   - "son bağlam + son çıktı" sütunu.
   - `etiketler.csv`: oturum/ajan → `arastirma | forge-meta | ogrenme | diger`.
   - `ozet --hafta` alt komutu.
   - Hakemin `usage_check.py` karşılaştırması regresyon testi olarak eklenir.
4. **Ölç ve karar ver.**
5. **Aynı gün `forge/OLUM-KRITERI.md`'yi commit et** (aşağıdaki sıkılaştırılmış hâliyle).

Ön kayıt:
- **Metrik ve eşik (sıkılaştırıldı):**
  - Hakemin 19 ajanı bu araçla zaten görüldü. Bu yüzden ölçüm, hakem raporundan **sonra** oluşmuş, görülmemiş ajanlar üzerinde yapılır: bu oturumdaki 10:00 UTC sonrası ajanlar ve sonraki ajanlar.
  - n ≥ 10 ajan. Her birinde yeni sütun ile resmi `subagent_tokens` arasındaki sapma **≤ %2**, ve **10/10** ajanda tutmalı.
  - Hakemin 19 ajanı regresyon setidir: sapma **≤ %0,5**.
  - Etiket katmanı ilk hafta raporunda eşlenmemiş pay **≤ %10** (bugün %35).
- **Öldürme kriterleri:**
  - Görülmemiş ajanlarda tek bir sapma > %2 ise karar RED. Araç sayaç olarak kullanılmaya devam eder ama KAYIT'ta KABUL yazmaz.
  - Etiket katmanında 3 hafta üst üste eşlenmemiş pay > %30 ise katman silinir. Forge kriterindeki K2 "ölçülemedi = başarısız" sayılır.
- **`OLUM-KRITERI.md` içeriği (Ç6'ya göre düzeltildi):**
  - **2026-11-22'de ölçülür:**
    - **K2:** forge-meta / araştırma harcaması ≤ %25.
    - **K3:** pilot hükümleri var ve hoca görüşmesi istendi.
    - **K4:** önceden commit edilmiş eşikle verilmiş en az bir gerçek KABUL ya da RED. maliyet-sayaci bunu sağlayabilir.
  - **Hüküm kuralları:**
    - K3 tutmazsa **DONDUR**.
    - K2 ve K4 birlikte tutmazsa **ÖLDÜR**.
  - **2026-12-24'te K1:** maliyet-sayaci dışında, gerçek işte ≥5 kez çağrılmış bir KABUL'lü araç. Tutmazsa Forge tek sayfalık bir ön kayıt şablonuna iner.
  - Dosya tarihinden sonra değiştirilirse Forge otomatik DONDUR'a geçer.

**3. Kapat: olum-testcisi İPTAL, gapmine ARŞİV (B-18).**

KAYIT'ta iki satır değişir. Sıfır maliyetli bir iş; ama ŞİMDİ listesinde olmasının nedeni şu: P-A'nın A2/A3/A6 önerileri ve P-B'nin B4'ü bu iki aracı canlandırma kapısını açık tutuyor. Kapı kapanmazsa altyapı bahanesiyle yeniden açılır.

- olum-testcisi'nin 3 iddialık eşiği bilgi taşımıyor: tesadüfi uyuşma olasılığı 0,34 (P-A'nın hesabı doğrulandı). İş de yalnız bir kez yapıldı.
- gapmine'ın altın seti kirli; hükmü kör tabandan kötü.
- **Ön kayıt:**
  - **Metrik:** 2026-11-22'ye kadar bu iki araca harcanan token ve dolar **= 0**. Etiket ve `tools` modu ile ölçülür.
  - **Öldürme kriteri (geri açma):** İki pilot da ELE çıkarsa ve yeni bir aday taraması elle **> $25** tutarsa gapmine yeniden açılabilir. O zaman bile önce aracı yazanın görmediği, insan kaynaklı 10 iddialık altın set kurulur; P-A'nın A2 öğesi burada devreye girer. Eşik kod yazılmadan commit edilir.

### SONRA (koşullu)

| Öneri | Tetikleyici | Not |
|---|---|---|
| **B-17 K5 rakip bekçisi** | K5 = DEVAM | ~2 saat, LLM'siz. Canary 2/2 (Zhou & Parno, Mariposa). Yanlış alarm ≤ 5/hafta. 4 hafta açılmazsa arşiv. Moratoryumun meşru ilk istisnası olur: gerçek ve tekrarlı bir ihtiyaç (haftalık tarama). |
| **B-11 Skill bağlama** (önce yalnız maliyet-sayaci) | maliyet-sayaci KABUL + 2 hafta içinde asistana komutun elle ≥3 kez hatırlatılması | P-B'nin 10 istemlik tetik testi ve ≤400 token açıklama bütçesi aynen kalır. Belge iddiaları doğrulandı (1.536 karakter, 5k token). |
| **B-6 Bağımsız yargıç** (insan 30P+30N, farklı aile) | Bir araç gerçek kabul ölçümüne geldiğinde | n tabanı P-A'dan. |
| **B-9 Görev-sonuç metriği** | makale-okuyucu çözülürse (Faz 1'de ≥10 makalelik gerçek okuma) ya da gapmine geri açılırsa | Yorum sadakati eşiği **≥ 28/30** (P-A'nın 27/30'u kendi Wilson koşulunu sağlamıyor). A/B önce 5 iddiayla pilot. |
| **B-7 Altın karantinası** (P-A'nın 5 insan kaynağı) | Altın set gerektiren ilk araç ölçümü | Şifreli zip yerine ayrı klasör + `--add-dir` verilmemesi yeter. |
| **B-8 Önemsiz ve ucuz taban** | Her yeni araç ön kaydında | "Hep çoğunluk" tabanı bedava; ucuz taban (BM25 vb.) yalnız LLM'li araçta. |
| **B-12 Çıktı bütçesi** | İkinci bir araç skill'e bağlandığında | `--json` döküm bulgusu doğru; ama araç dondurulmuş. |
| **B-10 Regresyon ve pre-commit** | Kabul edilmiş araç sayısı ≥ 2 | Tek araçta 2. maddedeki regresyon testi yeter. Mutasyon testi fikri (≥4/5) iyi; o gün kullanılır. |
| **B-15 Koşu günlüğü** | Etiketlerden sonra hâlâ "görünmeyen araç harcaması" > %10 ise | |

### YAPMA

1. **B-16 Forge ajan hattı (forge-spec, forge-insa, forge-denetci + worktree paralel inşa).** Bu, hakemin 2 numaralı riskinin ("meta-iş asıl işi yiyor") kurumsallaşmış hâli.
   - İlk denemesi olum-testcisi'yi inşa etmek. Oysa olum-testcisi bu kararla iptal.
   - ~$5–10 ve 250–400k token tutuyor.
   - Dayandığı hook yol engeli denenmemiş.
   - Yalnız şablon fikri (zorunlu SPEC başlıkları) B-3'ün ön kayıt şablonunda yaşar.
2. **B-14 Ortak kota defteri ve B-13 forge-core.**
   - İkisinin de tek canlı tüketicisi var.
   - Çözdükleri çakışma bugün yok: gapmine donduruldu, makale-okuyucu OpenAlex'e DOI başına tek istek atıyor.
   - Toplam 11–14 saat ve ~0,35–0,55 M token.
   - P-B'nin kendi öldürme kriterleri ("3. tüketici yok", "anahtar alınırsa iptal") bugünkü durumda neredeyse kesin tetiklenir. Kendi kriteri tetiklenecek bir şeyi kurmak tanım gereği batık yatırım.
   - **Tek istisna:** OpenAlex anahtarını almak. 5 dakikalık bir iş, sorunun büyük kısmını çözüyor ve geri alınabilir. Kod değil.
3. **P-A'nın tam paketi şimdi (A2 + A3 + A5 + A6 + A7 birlikte, ~26 saat / ~12 saat insan).** İçerik doğru, zamanlama yanlış. Ölçülecek araç yokken altyapı kurmak, P-A'nın kendi "Forge için öldürme kriteri"nin (meta-token, araştırma token'ının 2 katını aşmasın) ihlaline giden en kısa yol.
4. **ders-modu'nu araç olarak yazmak.** Elle denenir (Mariposa) ve 1. maddedeki geri anlatma kapısına bağlanır. Bu konuda P-C ve KAYIT aynı şeyi söylüyor.

---

## 6. Melezleştirme isteği nerede duruyor?

**Kısa hüküm: Şimdi değil. Ama en geç ~2026-11-08'den sonra ve tek bir ajanla, ön kayıtlı A/B olarak.**

**Neden şimdi değil?** Gerekçeler ölçüme dayanıyor:
1. **Hangi ajanın pahalı olduğu bilinmiyor.**
   - $1.631'lik harcamanın tamamı tek proje klasöründe.
   - En pahalı iki oturum toplamın %46'sı; içleri ayrıştırılmamış.
   - Melezleştirilecek hedef seçilemez. Seçilirse tahminle seçilir; bu da "ölçerek ilerle" ilkesinin ihlali olur.
   - 2. maddenin etiket katmanı tam bu boşluğu dolduruyor. Melezleştirmenin **ön koşulu** o.
2. **Forge'un kendi kanıtı uyarıyor.** gapmine zaten bir melezdi: kod + Haiku + deterministik alıntı doğrulama.
   - Sonuç: **50–100× ucuz**, ama **hükmü kör tabandan kötü** (6/10'a karşı 7/10).
   - Yani melez sistem getirme, filtreleme ve doğrulamada para kazandırdı; yargıyı ucuz katmana bırakınca kalite kaybetti.
   - Bu, "kod + ucuz model + pahalı yargı" tasarımının **doğru** olduğunu, ama sınırın **yargı** katmanında çizilmesi gerektiğini gösteriyor. Sınırın nerede olduğu ancak eşli ölçümle bulunur.
3. **Taban çizgisi bedavaya gelmeli.** Ö1'in "≥3 tekrar" kuralı burada da geçerli. Melezleştirilecek ajan, son 2 haftada gerçek işte ≥3 kez çağrılmış olmalı. Böylece taban çizgisi, maliyet-sayaci ile ölçülmüş gerçek koşulardan gelir.

**Hangi koşulda başlar?** Üç şartın üçü de gerekli:
- (a) maliyet-sayaci KABUL almış ve etiketlerle ≥2 haftalık veri toplanmış olmalı (eşlenmemiş pay ≤ %10).
- (b) En az bir pilot hüküm almış ve pitch gitmiş olmalı (11-08). Melezleştirme araştırmanın yerine geçmemeli.
- (c) Etiketlere göre en pahalı **ve** ≥3 kez tekrarlanmış tek bir ajan seçilmeli. Aday örnekleri: Epic hattındaki `dogrulayici` (zaten "betikle ölçer"; muhtemelen en kolay melez) ya da en pahalı araştırma ajanı. Bu seçim tahmin; etiket verisi karar verir.

**Nasıl ölçülür?** Bu metrik ve öldürme kriteri melezleştirme başlamadan commit edilmeli. Şablon P-A'nın A6'sındaki aşağı akış A/B'si:
- **Tasarım:**
  - Aynı ≥5 görevde (pilot), sonra ≥10 görevde, eşli koşu: pahalı ajan (A) ile melez (B).
  - Kalite yargıcı insan (öğrenci) artı mümkünse farklı aileden bir model.
- **Başarı eşiği:**
  - Kalite farkı ≥ −5 puan.
  - Gerçek maliyette (maliyet-sayaci, kümülatif token, resmi sayı değil) ≥ %50 düşüş.
  - Çiftlerin ≥9/10'unda B daha ucuz (işaret testi, tek yönlü, p ≈ 0,011).
- **Öldürme kriteri:**
  - 5 görevlik pilotta kalite > 10 puan düşerse ya da maliyet < %30 düşerse o ajanın melezleştirilmesi durur ve KAYIT'a RED yazılır.
  - İlk melezleştirmeden sonra 4 hafta içinde ikinci bir aday ≥3 tekrar koşulunu sağlamazsa "ölçeklenebilir melez sistem" bir program olarak açılmaz. Melezleştirme yalnız kanıtlanan ajanla kalır.

**Özet:** Melezleştirme, Forge'un var olma nedeni olan ilk felsefe maddesinin ("pahalı model yalnız yargı yapar") ilk gerçek sınavı olacak. Ama sınava girmek için önce ölçüm aleti (2. madde) ve gerçek iş (1. madde) gerekiyor. Sıra bu.

---

## Kaynaklar (yargıcın bizzat kontrol ettikleri)
- Yerel dosyalar:
  - `forge/README.md`, `KAYIT.md`, `HAKEM-RAPORU.md`
  - `araclar/makale-okuyucu/{SPEC.md, README.md, makale_okuyucu/llm.py, quotecheck.py, fetch.py, store.py, data/...}`
  - `araclar/maliyet-sayaci/maliyet_sayaci.py`
  - `akademik-bosluk/gapmine/{gapmine/llm.py, quotecheck.py, karsilastirma/DENETIM.md, altin/gold.json}`
  - `akademik-bosluk/olum-testi/00-SKOR.md`, `pilot-k5/{karar-gunlugu.md, data/run_log.txt}`
  - `git log`: forge ve akademik-bosluk.
- Sayısal ölçüm: `maliyet_sayaci.py sessions --json` ve `agents --session 76053f18 --json`. Yalnız usd, zaman ve kimlik alanları okundu.
- Dış kaynaklar:
  - https://code.claude.com/docs/en/skills
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - https://arxiv.org/abs/2502.14297
