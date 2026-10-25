# Öneri: CAD döngüsü aracı (build → check → render → kompakt özet) — 2026-10-25

Durum: **tasarım + ön kayıt taslağı**. Kod yok. Yalnız yerel transkriptler okundu (usage alanları, araç adları/komutlar, sonuç uzunlukları; ağ yok).
Ölçüm betikleri: `scratchpad/cad.py … cad6.py` (oturum 243dc754 scratchpad'i). Fiyat: `fiyatlar.json` Opus-5 listesi (5/25/6.25/0.5 $/M); OLCUM-ajanlar.md'deki $654 başka fiyat tabanı, **sıralama aynı, mutlak $ farklı**.

## Kısa sonuç
OLCUM-ajanlar'daki hipotez ("koşu başı maliyet ≥%40 düşer") **veriyle desteklenmiyor**. Tek komutlu döngü + kompakt özet tahminen **%4–12** kazandırır. Maliyetin büyük kısmı döngü çıktısında değil, (a) bağlam büyümesi × tur sayısında, (b) önbellek yeniden kurulumunda, (c) kaynak/README gezinmesinde. Araç yine de ucuz ve düşük risklidir; ama "en büyük kalem" iddiası düzeltilmeli.

## 1. Maliyet nereye gidiyor? (cad-tasarimci-v2: 23 koşu, 4115 tur, 4104 araç çağrısı)
Koşular: `subagents/*.meta.json` içinde `agentType=cad-tasarimci-v2` (oturumlar 2ab53b0d, d3d97074, caa2939f, 8412c107; örn. adbc05c9 $104, a0001d84 $119, a121cb6c $106).

| Kalem | $ | Pay |
|---|---|---|
| Toplam | 981 (ort. 42,7; medyan 31,4; max ~104 koşu başı = 312/3) | |
| cache-okuma (bağlam × tur) | 521 | %53 |
| cache-yazma | 428 | %44 |
| — bunun "yeniden kurulum" turları (yeni yazma > bağlamın %50'si ve >20k) | 335 (180 tur, turların %4,4'ü) | **%34** |
| — artımlı yazma | 92 | %9 |
| çıktı tokenı | 32 | %3 |

Kanıtlar:
- **Bağlam büyümesi doğrusal-üstü maliyet:** koşu başına tur ≤130: $12,7/koşu, $0,121/tur, azami bağlam ~205k; 130–250 tur: $39,6, $0,221/tur, ~389k; >250 tur (5 koşu): $102, $0,328/tur, ~559k (maks 741k). Ortalama tur başına okunan bağlam ≈ 253k token. Kaçırılan bir tur ≈ $0,13 (yalnız okuma) + sonucunun taşıma maliyeti.
- **Yeniden kurulum:** 180 turda önbellek yeniden yazıldı (TTL 5 dk). 63'ü `sleep/until` bekleme çağrısından hemen sonra ($132, medyan boşluk 596 s), 35'i gezinme/uzun komut sonrası ($47), 76'sı öncesinde araç çağrısı yok ($149; nedeni ölçülmedi: devam ettirme/yeniden başlatma olabilir, boşluk medyanı 2 s ama bazıları saatlerce). 87 yeniden kurulumun boşluğu <300 s — TTL açıklaması hepsine uymuyor.
- **Araç sonucu başına taşıma maliyeti** (sonuç token ≈ karakter/3,2; kalan tur sayısı × okuma fiyatı + bir yazma): toplam $146 (= toplamın %15). Dağılım:
  - Betik dışı Python/`cat` kaynak okuma %40 (860 çağrı), gezinme/ls/grep %21 (346), `Read` metin %16 (59) → **%77 = ~$113 = toplamın %11,5**. Tipik: `cat checks/*.py`, `cat params.py`, `PLAN.md` (30k karakter), `eye_v5.py` (38k).
  - check %7,1 (222 çağrı), params %4,9, build %4,6, regresyon %1,4, render %1,0, onizleme %0,2, görsel Read %1,7 (222 PNG, 57,6 MB base64; token sayımı kaba) → **döngü çıktıları toplam ~$29 = toplamın ~%3**.
- **Check çıktısı şişkinliği abartılı:** 186 check çağrısının medyanı 751 karakter, p90 7,6k, p99 25k (OLCUM'daki 28k p90 tüm araçlar içindi). check_report.txt'i yeniden okuma: 53 okuma, 136k karakter, taşıma maliyeti **$3,4 (%0,35)**. Rapor zaten `SONUC:` 1. satırda; v6 raporu 52 KB ama ilk satır TEMIZ.
- **Döngü gerçekte "build→check→render" ardışık değil:** bitişik build→check çifti yalnız 13; araya satır içi Python ve inceleme giriyor. Koşu başına check çağrısı medyan 11 (0–42). Yani "tekrarlı, deterministik zincir" varsayımı kısmen doğru: tekrarlı ama zincir kopuk.
- Bekleme: 144 bekleme çağrısı (OLCUM: 95); her biri ayrı tur → ~144 × $0,13 ≈ $19 yalnız okuma.
- Ölçülmeyen: AMD (`amd-tasarimci`) koşuları; assistant'ın yazdığı kod/düşünce taşıması (çıktı tokenı küçük ama sonra taşınır; kalan ~%85'in bir kısmı bu + temel bağlam 16k).

## 2. Mekanik vs şef yargısı
**Betik (Haiku bile gerekmez):**
- `build --only` → `check` → `render` sırası, çıkış kodu, süre, çıktı dosya listesi.
- Özet çıkarma: `SONUC:` satırı, başarısız/uyarı kontrol adları + ilk rakam, KAPSAM'daki `OLCULMEDI` satırları (aynen), önceki koşuya göre **değişen** ölçüler (amdcheck `--onceki` ve `--metin` bunu zaten yapıyor; Epic'te `check_report.txt` formatı sabit).
- Uzun işi arka planda koşup bitince tek bildirim (bekleme turlarını siler).
- Proje durum özeti (STATE.md, son rapor özeti, params farkı) — gezinme turlarını azaltır.
- Render: PNG üretimi ve boyut/sayı; küçük küçük-resim sayfası (contact sheet) tek görüntü.

**Şef (cad-tasarimci-v2 / Opus) kalır:**
- Hangi parçayı nasıl değiştireceği, plan sapması, DECISIONS.
- Görsel yargı (PNG'yi planla karşılaştırma; en çok 2 tur).
- OLCULMEDI satırının kabul edilebilir olup olmadığı, muaf çift gerekçesi.
- denetci-v2 bulguları, dogrulayici sınıfları (zaten ayrı ajan; dogrulayici Sonnet).
**Haiku için aday (kuşkulu):** yalnız "gezinme": belirtilen dosyalardan sabit şablonlu özet. Şüpheli içerik şefe çıkar (Forge ilkesi). Kanıt yok; ilk sürümde kullanma.

## 3. Beklenen tasarruf ve bilgi kaybı riski
Varsayım: aracın bitişik çağrıları birleştirmesi ve beklemeyi bildirime çevirmesi ~250 (zincir) + 144 (bekleme) ≈ 400 turu siler (4115 turun %10'u; en kötü 250, en iyi 550); her tur ≈ $0,13–0,25.
- Tur silme: 400 × 0,13–0,25 = **$52–100 → %5–10**.
- Çıktı diyeti: döngü çıktısı ~$29'un yarısı → +%1,5.
- Yeniden kurulum: bekleme turları yok olsa da 5 dk TTL aşan **uzun koşu** TTL'yi yine aşar → sayılmadı; yalnız koşu süresi kısalırsa ek %0–5 (belirsiz).
- **Toplam aralık %4–12, orta ~%8.** Bu "%40" hipotezini reddeder (eşik %10 önerildi, aşağıda).
- Daha büyük kaldıraç (ayrı öneri, bu aracın dışında): kısa koşu bölme/devir. >250 tur koşuları $0,33/tur, ≤130 tur koşuları $0,12/tur; bir koşuyu ikiye bölmek bağlamı sıfırlar. Ayrıca `cat checks/*.py`, README, PLAN okumaları koşular arası tekrarlanıyor (check_report.txt 175, check.py 59, params.py 35, README 30 kez geçti) → "proje kılavuz özeti" (≤2k token) %11,5'lik gezinme kalemini hedefler. Bunlar da ölçülmeden yapılmaz.

**Bilgi kaybı riskleri (önem sırasıyla):**
1. **Gömülü başarısızlık:** özet "N hata" yerine yalnız ilk 3'ü gösterir; ya da sınıflayıcı bir uyarıyı geçer sayar. Önlem: özet **tam sayım + her FAIL/UYARI adı** içermeli; bütçe aşılırsa kesme değil "…ve K tane daha: <dosya>" + ham raporun yolu; `SONUC` satırını betik raporun kendisinden **aynen** kopyalar, yorumlamaz.
2. **KAPSAM kaybı:** OLCULMEDI/muaf çift satırları en kolay atılan şey; denetci-v2'nin ilk bakacağı yer. Önlem: bu bloğu daima, sıkıştırmadan, değişiklikle (diff) birlikte ver.
3. **Sessiz düşme:** betik bir kontrolü çalıştıramadıysa "temiz" demesi. Önlem: girdi/çıktı/düşen sayısı (Forge ilkesi), kontrol sayısı < bir önceki koşunun sayısı ise HATA.
4. **Görsel bilgi:** kompakt özet render'ı anlatamaz; görsel yargı şefte kalmalı, araç yalnız PNG yollarını + contact sheet verir.
5. **Eski/bayat çıktı:** build başarısızken eski STL'i check'lemek; araç md5/mtime ile "bu koşunun çıktısı" doğrulamalı.
6. Şefin ham rapora hiç bakmaması (güven kayması): her N. koşuda ham rapor örneği.

## 4. Ön kayıt taslağı — `ONKAYIT-cad-dongusu.md` (ilk kod commit'inden ÖNCE)
- **Hipotez (düzeltilmiş):** `cad_dongusu` aracı cad-tasarimci-v2'nin bir "değiştir→doğrula" döngüsünün maliyetini düşürür ve hiçbir başarısız kontrolü gizlemez. (Eski ≥%40 hipotezi 23 koşuluk ölçümle reddedildi, bkz. §3.)
- **Birim:** "döngü" = donmuş bir proje durumundan başlayıp tek küçük değişikliği uygulama + build/check/render + SONUC kararı. Tam koşu birimi (≈$40, n=30 × 2 kol ≈ $2.400) pahalı → **birim döngüdür**; tam koşu için pilot.
- **Örneklem:** n = 30 döngü (3 proje × 10: project-eye v5/v6, sonar-beta, bir amd örneği), her biri iki kolda, **eşli**, sırası rastgele; stokastik olduğundan k = 3 tekrar ya da (bütçe) k=2 + n=30'u koruma. Tahmini maliyet ≈ 30 × 2 × ~$2–4 ≈ $120–240 (kabul öncesi kullanıcı onayı: >$10 kuralı).
- **Taban çizgisi:** bugünkü `cad-tasarimci-v2` (aynı model, aynı istem, aracı kullanmadan, kendi yoluyla).
- **Birincil metrik:** döngü başına $ (maliyet-sayaci, aynı fiyat dosyası) — eşli fark.
  - Eşik: medyan eşli azalma ≥ %25 **ve** işaret testi p < 0,05 (tek yönlü) **ve** %95 eşli-bootstrap alt sınırı > 0.
  - İkincil: tur sayısı, yeniden kurulum turu, SONUC/kararın tabanla aynı olması (≥ %95 uyum).
- **Bilgi kaybı kapısı (zorunlu):** 30 tohumlanmış hata (çakışma, havada ada, ince et, montaj-sökme, tolerans, KAPSAM'da gizli muaf çift gibi; her biri bilinen yanlış sonuç) → özetin hatayı gösterme oranı **Wilson %95 alt sınırı ≥ %90 ve ham-rapor tabanıyla eşit ya da daha iyi**; "temiz" denen fakat gerçekte HATA olan = 0 (sıfır tolerans).
- **Ek kapı (ham rapora geri dönüş):** şefin özetten sonra ham rapora başvurma oranı raporlanır; >%50 ise tasarruf iddiası geçersiz.
- **Tam koşu pilotu:** n = 4 eşli tam koşu (aynı PLAN.md). n < 30 olduğundan **"pilot, karar yok"**; yalnız §3'ün %4–12 tahminini kaba doğrular.
- **Öldürme kriteri:** (a) döngü bazında medyan azalma < %10; ya da (b) tohumlanmış hatalardan **herhangi biri** "temiz" olarak sunulursa; ya da (c) araç bakım/yazım maliyeti 5 sonraki koşuda kazancı aşarsa (tahmin: tek komutun yazımı ~$5–10; kazanç koşu başı ~$3 ⇒ ~3 koşuda amorti) → RED, araç silinir, ISTEK-GUNLUGU kaydı kapanır.
- **Denetçi:** sistemi yazandan farklı: denetci-v2 (Opus) tohumlama listesini ve karşılaştırmayı görmeden değerlendirir; ya da kullanıcı.
- **Altın set:** tohumlanmış hatalar insan/kullanıcı tarafından onaylı listeden (mevcut `check_report` geçmişi: v2→v6 gerçek bulgular, `dogrulama.md` DOĞRULANDI satırları) seçilir; aracı yazanın tohumlamasına bırakılmaz.
- **Regresyon:** kabul testi kalıcı; `check_report` format değişirse test düşer.
- **Önce (ücretsiz) adım:** mevcut 23 transkriptte "karşı-olgusal yeniden oynatma": hangi turlar birleşebilirdi? Tahmin bu sayımla bağlanır, sonra pilot.

## Öneri
1. ISTEK-GUNLUGU kaydını "kanıt" sütununda düzelt: döngü çıktısı toplamın ~%3'ü; asıl kalemler bağlam büyümesi (%53 okuma), yeniden kurulum (%34 yazma) ve kaynak gezinmesi (%11,5).
2. Moratoryum bitince önce **ucuz sürüm**: yalnız `cad_dongusu.py` (build→check→render, arka plan, ≤1,5k token özet, KAPSAM aynen); Haiku yok.
3. Paralelde (ölçülecek) "koşu bölme/devir" ve "proje kılavuz özeti" ayrı kayıt.
