# P-B: Forge için mühendislik ve entegrasyon önerileri (2026-10-25)

Merceğim: mühendislik ve entegrasyon. Hiçbir dosya değiştirilmedi; yalnız bu rapor yazıldı.

**Okunanlar:** `README.md`, `KAYIT.md`, `HAKEM-RAPORU.md`, `araclar/makale-okuyucu/` (kod, README, SPEC, testler), `araclar/maliyet-sayaci/` (kod, SPEC, testler), `akademik-bosluk/gapmine/` (README, SPEC, `karsilastirma/DENETIM.md`, `llm.py`, `httpclient.py`, `config.py`).

**Koşulan testler (ağsız):** makale-okuyucu 67/67 geçti (38 sn). maliyet-sayaci 19/19 geçti (1,5 sn). Gerçek LLM ya da ağ koşusu yapılmadı.

**Genel teşhis (tek paragraf):** Forge'un iki sorunu var. (1) Kabul edilen aracı asistana bağlayan katman yok: README'deki `sistem/` ve `kanit/` diskte yok (`README.md:25-26`), yani "KABUL → skill/ajan olarak sisteme bağlanır" adımı tanımlı ama gerçekleşmemiş. (2) Araçlar birbirinden habersiz üretilmiş: kod kopyası, ayrı önbellek, ayrı log biçimi, ayrı kota davranışı. İkisi de araç sayısı 2'den 5'e çıkmadan çözülürse ucuz, sonra pahalı.

Öneriler önem sırasıyla. Süre ve token tahminleri kaba tahmindir, ölçüm değildir.

---

## Bağlama seçeneklerinin karşılaştırması (Öneri 1'in dayanağı)

Kaynaklar (Claude Code belgeleri, 2026-10-25'te okundu): Skills https://code.claude.com/docs/en/skills ; MCP https://code.claude.com/docs/en/mcp ; Hooks https://code.claude.com/docs/en/hooks ; Alt-ajanlar https://code.claude.com/docs/en/sub-agents . Belge sayfalarının sonu kesik okundu; aşağıdaki her madde okunan kısımdan alındı.

| Seçenek | Artı | Eksi | Forge'a uygunluk |
|---|---|---|---|
| **Skill** (`~/.claude/skills/<ad>/SKILL.md`) | Gövde yalnız çağrılınca bağlama girer; "uzun referans malzemesi ihtiyaç olana kadar neredeyse hiç maliyet yaratmaz". Yalnız `description` her zaman bağlamda (açıklama+`when_to_use` listede 1.536 karakterde kesilir). `scripts/` altındaki dosyalar "çalıştırılır, yüklenmez". `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/x *)` ile aracı önceden onaylatır. `context: fork` ile alt-ajanda koşturulabilir. | Tetiklenme `description` kalitesine bağlı (kaçırabilir). `allowed-tools` kısıtlamaz, yalnız izin verir. Yüklenen gövde sonraki turlarda bağlamda kalır (sıkıştırmada her skill'in ilk 5.000 token'ı korunur). Araç `.venv`'i skill klasöründe değil `forge/` altında; yol mutlak olmalı. | **En uygun varsayılan.** Araçlar zaten CLI; skill ince bir kullanım kılavuzu + çağrı satırı olur. |
| **MCP sunucusu** (stdio) | Türlü şema, tek süreçte kalıcı durum (ortak kota defteri/önbellek için doğal ev). Çıktı sınırı tanımlı: 10.000 token'da uyarı, varsayılan 25.000 tavan, 50.000 karakter üstü dosyaya yazılır. | Her araç için ayrı süreç ve `.venv` başlatma; `MCP_TIMEOUT` ile başlangıç sınırı; ilk bağlantı otomatik yeniden denenmez; tool search kapalıyken başarısız sunucu modele bildirilmez; stdio boşta 30 dk sonra düşer; araç tanımları bağlam maliyeti getirir. `claude -p` ve SDK proje kapsamlı sunucuları sormadan yükler (güvenlik yüzeyi). Windows'ta çocuk süreç/venv/UTF-8 sürtünmesi. | **Şimdilik hayır.** 2-3 araç için ağır. Ortak durum gerekirse SQLite dosyası aynı işi sunucusuz yapar (Öneri 4). |
| **Hook** (`settings.json`) | Deterministik: model "unutamaz". `PostToolUse` exit 2 ile stderr'i Claude'a gösterir, `Stop` hook'u "test geçmeden bitirme"yi zorlar, `SessionStart` bağlam enjekte eder. Alt-ajan frontmatter'ına gömülebilir (yalnız o ajan çalışırken). | Araç değil, kapıdır: çıktı üretmek için değil denetlemek için. `additionalContext` 10.000 karakterle sınırlı. Her oturumda çalışan hook hızlı olmalı. Exit 1 engellemez (yalnız 2). | **Regresyon ve bağımsızlık korumaları için** (Öneri 6, 7). Araç bağlama yolu olarak değil. |
| **Alt-ajan** (`~/.claude/agents/*.md`) | Kendi bağlam penceresi; yalnız son rapor ana bağlama döner. `model:` ayrı seçilebilir (bağımsız denetçi için kritik). `skills:` ile skill önyüklenir, `tools:` izin listesi. Kullanıcı zaten böyle ajan ekibi işletiyor (`dogrulayici`, `denetci-v2`...). | Ajan çağrısı pahalıdır (hakem: iddia başına 0,62–1,40 $). Sıradan bir CLI çağrısı için gereksiz. Alt-ajan içinde oluşturulan alt-alt-ajan 3 katmanla sınırlı. Eklenti ajanları `hooks`/`mcpServers`'ı desteklemez. | **Yalnız çok adımlı yargı gerektiren araçlar için** (olum-testcisi, ders-modu). Tek komutluk araç için skill yeter. |

**Sonuç:** Varsayılan kalıp = *CLI çekirdek + ince skill*; çok adımlı araçlarda *skill + alt-ajan*; kapılarda *hook*; MCP yok.

---

## Öneri 1 (en önemlisi): "Kabul → bağlama" hattını kur: ince skill + tek başlatıcı, önce maliyet-sayaci ile pilot

**(a) Sorun ve kanıt**
- `README.md:25-26` `kanit/` ve `sistem/` klasörlerini vaat ediyor; diskte yok (`ls forge` → `HAKEM-RAPORU.md KAYIT.md README.md araclar gelistirme`). Hakem de bunu yakaladı (`HAKEM-RAPORU.md` §3 madde 10).
- `~/.claude/skills/` altında yalnız `synced`, `~/.claude/agents/` altında yalnız Epic mekanizma ajanları var; hiçbir Forge aracı asistanın erişiminde değil. `KAYIT.md`: maliyet-sayaci "KABUL (koşullu)" ama asistan onu kendiliğinden çağıramıyor.
- Araçların çağrısı bugün `.\.venv\Scripts\python -m makale_okuyucu ...` (README "Komutlar"). `maliyet-sayaci` ise venv'siz sistem Python'u kullanıyor. İki farklı çağrı kalıbı, ikisi de mutlak yola bağımlı.
- Sonuç: kabul edilmiş bir araç ile kullanılabilir bir araç arasında boşluk var. Asıl hedef ("Claude'un kullanacağı araçlar") ölçülmüyor.

**(b) Öneri**
1. `forge/sistem/<arac>/SKILL.md` kaynak dosyaları + `forge/sistem/kur.ps1` (kopyalar/bağlar `~/.claude/skills/forge-<arac>/`). Bir araç yalnız KABUL/ŞARTLI olunca skill'i `sistem/`e girer; RED ise girmez. Böylece protokolün 4. maddesi mekanik hale gelir.
2. Tek başlatıcı `forge/bin/forge.cmd <arac> <argümanlar>`: aracın `.venv`'ini (varsa) bulur, `PYTHONUTF8=1` verir, çıkış kodunu aynen döndürür. Skill'ler yalnız bunu çağırır: `allowed-tools: Bash(C:\Users\LENOVO\Projeler\forge\bin\forge.cmd maliyet *)`.
3. Her SKILL.md şablonu: 1 cümle ne zaman kullanılır (anahtar kullanım önce), 3-5 örnek komut, çıkış kodu anlamları, "çıktı bütçesi" satırı (Öneri 2), "ne yapmaz" satırı (örn. "bulunamadı ≠ aranamadı"), kabul kararının rolü (ŞARTLI ise rol).
4. Pilot: önce `maliyet-sayaci` (koşullu kabul, en yakın). Sonra `makale-okuyucu` kabul olursa. gapmine DONDURULDU, girmez.
5. Çok adımlı araçlar (olum-testcisi, ders-modu) için aynı skill'e `context: fork` + `agent:` ya da `~/.claude/agents/forge-<ad>.md` eklenir; `model:` ve `tools:` açık yazılır.

**(c) Beklenen kazanç:** Kabul edilen araç, kullanıcı hatırlatmadan ve komut yazmadan asistan tarafından seçilir. Maliyet-sayaci'nın hakemin bulduğu bilgisi ("resmi alt-ajan token sayısı gerçek kullanımın 9–44'te 1'i") her büyük harcama kararında otomatik devreye girer.

**(d) Maliyet:** 3–4 saat (şablon, kur.ps1, forge.cmd, 2 skill, 10 istemlik tetik testi). Token: ~60–100 bin (yazım + tetik testi için 10–20 kısa oturum; çoğu Haiku/ucuz).

**(e) Metrik ve eşik (önceden kayıt):** 10 hazır istem (5'i araca ait, 5'i ilgisiz) taze oturumlarda çalıştırılır. Eşik: doğru araç çağrısı ≥ 8/10 ve ilgisiz istemlerde yanlış çağrı = 0. İkinci eşik: tüm Forge skill açıklamalarının toplam her-zaman-bağlamda maliyeti ≤ 400 token (karakter/4 tahmini). Eşik dosyası (`sistem/ESIK.md`) ilk koşudan önce commit edilir.

**(f) Öldürme kriteri:** Açıklama iki kez revize edilse bile tetiklenme < 6/10 ise otomatik tetikleme bırakılır: skill'ler `disable-model-invocation: true` ile yalnız `/forge-x` ile çağrılır ve konu CLAUDE.md'ye tek satır olarak taşınır. Tek araç kalırsa (yalnız maliyet-sayaci) `sistem/` hattı kaldırılır, tek skill elle bakılır.

---

## Öneri 2: Çıktı bütçesi sözleşmesi: stdout ≤ N token, taşan her şey dosyaya + yol + önizleme

**(a) Sorun ve kanıt**
- "Araç bana özet verir, döküm vermez" (`README.md` Felsefe) ilkesi araç başına ayrı ayrı uygulanmış, ortak bir sözleşme yok.
- maliyet-sayaci: 40 satır tavanı sabitlenmiş (`maliyet_sayaci.py:23`, `VERI_SATIRI`), gizli satır sayısı yazılıyor (`:504`). İyi.
- makale-okuyucu: `read` Markdown'u ≤1.500 token bütçeli (`render.py`, `config.md_max_tokens`), ama `read --json` tüm kartı basar: `data/papers/arxiv_*/card.json` ≈ 17,7–17,9 KB (≈ 4,5–5 bin token, kendi karakter/3,5-4 tahminiyle). Bu bayrak sınırsız. Ayrıca `ask` çıktısı JSON ve içinde `llm` istatistik bloğu var (`data/smoke/ask_a3.json` 2.462 bayt, `ask_b1.json` 772 bayt); asistanın karar için ihtiyaç duymadığı sayılar her çağrıda bağlama giriyor.
- gapmine raporları (`reports/*.md|.json`) için böyle bir sözleşme yok; `verify` konsol çıktısı ve rapor boyutu denetlenmemiş.
- Claude Code'un kendi sınırları referans: MCP 10.000 token'da uyarır, 25.000 tavan (`MAX_MCP_OUTPUT_TOKENS`); hook `additionalContext` 10.000 karakterde kesilir, fazlası dosyaya gider ve yalnız yol + 2.000 karakter önizleme geçer (Hooks/MCP belgeleri). Yani platform zaten "taşanı dosyaya yaz" modelini kullanıyor.

**(b) Öneri**
- Sözleşme (SPEC şablonunun zorunlu bölümü): her komut `--max-tokens N` (varsayılan 1.500) kabul eder; stdout yalnız "bağlam çıktısı"dır. Taşan içerik `forge/veri/cikti/<arac>-<zaman>.json`'a yazılır ve stdout sonuna tek satır: `TAM: <yol> (N token, ilk M gösterildi)`.
- Hata/durum satırı HER ZAMAN başta ve kısa: `DURUM: OK|PARTIAL|EKSİK|ARANAMADI ...`. Böylece kesilse bile "aranamadı" bilgisi kaybolmaz.
- İstatistik/maliyet bloğu stdout'tan stderr'e ya da log dosyasına (Öneri 5) taşınır; `ask` çıktısı: cevap + alıntı + sayfa + `dogrulanmis`. `--json` varsayılanı da bütçeli; tam döküm için `--tam`.
- Ortak ölçüm: tek test `assert tokens(stdout) <= bütçe` her araç için.

**(c) Beklenen kazanç:** Asistan bağlamına giren araç çıktısı üst sınırlı ve öngörülebilir olur; yanlışlıkla 5 bin tokenlık JSON dökümü ortadan kalkar. Sessiz kesilme olmaz çünkü durum satırı başta.

**(d) Maliyet:** 3 saat (sözleşme + makale-okuyucu `ask`/`read --json` ve maliyet-sayaci'na ince bir sarmalayıcı + testler). Token: ~30–50 bin.

**(e) Metrik ve eşik:** Her araç için 10'ar tipik komutun stdout'u ölçülür (karakter/3,5 tahmini). Eşik: p95 ≤ 1.500 token, max ≤ 2.500 token; `DURUM:` satırı 10/10 komutta ilk satırda. Başlangıç ölçümü (tahmin, ölçülmeli): `read --json` ≈ 4,5–5 bin token → ihlal.

**(f) Öldürme kriteri:** Dosyaya taşıma asistanın ikinci bir okuma çağrısına yol açıp toplam token'ı artırıyorsa (10 görevde ortalama toplam bağlam, taban çizgisine göre ≥ %20 artarsa) varsayılan bütçe 3.000'e çıkarılır; yine artarsa bütçe sözleşmesi yalnız `--json` modunda zorunlu bırakılır.

---

## Öneri 3: `forge-core` ortak paketi: llm, quotecheck, HTTP/kota; kopyalamayı bitir

**(a) Sorun ve kanıt**
- `makale_okuyucu/llm.py` (336 satır) başlığında "gapmine/llm.py'den kopyalandı" yazıyor; gapmine'daki aslı 395 satır. Ad değişikliği (`gapmine`/`makale_okuyucu`) normalize edilince bile iki dosya arasında 213 satırlık fark satırı var (diff `<`/`>`): kopya zaten ayrışmış (recorder geri çağrısı, iş parçacığı kilidi, farklı Config).
- `quotecheck.py`: makale-okuyucu sürümü "gapmine/quotecheck.py'den kopya + sayfa bulma" (91 satır vs 79). 14 satır fark, yani `locate_page` eklenmiş. Alıntı doğrulama Forge felsefesinin çekirdeği ("kanıt kodla doğrulanır"); iki yerde yaşıyor.
- Her ikisinde de aynı `claude -p` bayrak seti (`--tools ""`, `--strict-mcp-config`, `--setting-sources ""`, `--no-session-persistence`, boş cwd, stdin) ayrı ayrı test ediliyor (`makale-okuyucu/tests/test_llm.py`, `gapmine/tests/test_llm.py`). Claude CLI bir sürümde bayrak adı değiştirirse iki yerde düzeltmek gerekir; bu bayraklar çağrı başına ~20× maliyet farkı yaratıyor (gapmine README, duman testi 1).
- Her aracın ayrı `.venv`'i var; paylaşımı zorlaştıran bu, ama çözülebilir (editable install).

**(b) Öneri**
- `forge/ortak/` altında paket `forge_core` (`llm`, `quotecheck`, `jsonparse`, `maliyetlog`, ve Öneri 4'ün `kota`/`httpcache`'i). Her araç `.venv`'ine `pip install -e ..\..\ortak` ile bağlanır; `requirements.txt`'e `-e ../../ortak` satırı.
- Geçiş sırası: (1) quotecheck (en küçük, en sağlam testli), (2) llm, (3) HTTP. Her adımda iki aracın eski testleri değişmeden geçmeli; gapmine dondurulmuş olduğu için ona dokunulmaz, yalnız makale-okuyucu ve yeni araçlar `forge_core` kullanır, gapmine'a "bu kopya eskidir" notu eklenir (kod değişikliği olmadan, dokümanda).
- `forge_core` kendi testlerine ve kendi sürümüne sahip olur; araç `KAYIT.md`'ye hangi core sürümüyle kabul edildiğini yazar.

**(c) Beklenen kazanç:** Tek yerde düzeltme; kabul sırasında "hangi quotecheck sürümü ölçüldü" belirsizliği biter. Yeni araç (olum-testcisi, ders-modu) sıfır kopyayla başlar.

**(d) Maliyet:** 5–6 saat (çıkarma, import yolları, 2 aracın testleri, venv bağlama). Token: ~150–250 bin. gapmine dondurulduğu için bu maliyet yalnız makale-okuyucu + gelecek araçlar adına.

**(e) Metrik ve eşik:** (i) Araçlar arası kopya satır sayısı (aynı içerikli ≥ 20 satırlık blok sayısı, basit `difflib` betiği): taban çizgisi 2 dosya çifti → hedef 0. (ii) Geçiş sonrası makale-okuyucu 67 testi değişmeden yeşil kalır. (iii) Yeni araç ilk güne kadar `llm`/`quotecheck`'i import ile alır (kopya = 0).

**(f) Öldürme kriteri:** olum-testcisi ve ders-modu'ndan hiçbiri 60 gün içinde `llm`/`quotecheck`'e ihtiyaç duyan üçüncü bir tüketici olarak yazılmazsa ve gapmine dondurulmuş kalırsa (yani yalnız 1 canlı tüketici), paketleme iptal edilir; yalnız `quotecheck` için "tek doğru kopya" belirlenir ve diğeri silinir. Geçiş sırasında bir araç testi değişmeden geçmiyorsa o adım geri alınır.

---

## Öneri 4: Ortak kota defteri ve HTTP önbelleği (OpenAlex'i tek kapıdan geçir)

**(a) Sorun ve kanıt**
- `DENETIM.md`: OpenAlex anahtarsız günlük bütçesi (≈ 0,10 $) aynı IP'de paylaşılıyor ve ~83 istekte bitti ("günde ~4,5 iddia"); 10 iddianın 7'si EKSİK koştu; 8/92 altın makale (K8'in asıl öldüreni UnReason dahil) yalnız OpenAlex'ten gelebilirdi. gapmine README "Bilinen sınırlar": "Başka bir araç bitirirse gapmine EKSİK döner (koşu A)".
- makale-okuyucu `fetch.py:161-170` (`openalex_work`) OpenAlex'i kendi `get` fonksiyonuyla, anahtarsız ve gapmine'ın hız sınırlayıcısından bağımsız çağırıyor. İki araç aynı kotayı birbirinden habersiz tüketiyor.
- Kota durumu yalnız süreç içinde tutuluyor: `httpclient.py:75,160,206,230` (`st.quota_exhausted` bellekte, `SourceStats`). Retry-After değeri (koşu A'da 8.604 sn) bir sonraki süreçte bilinmiyor; araç yine istek atıp bütçeyi ve süreyi harcıyor.
- Önbellekler ayrı: gapmine `data/gapmine.db` `raw_responses`, makale-okuyucu `data/cache.db`; aynı DOI için OpenAlex yanıtı iki kez getirilebilir.
- `DENETIM.md` §5 madde 3: geçici 429 kalıcı kota sayılıyor (`httpclient.py:229-233`): "kaynak koşunun geri kalanında hiç sorulmuyor". Bu ayrım ortak katmanda bir kez doğru yapılabilir.
- Not: anahtar alınırsa sorunun büyük kısmı çözülür (gapmine README öneri 1). Bu öneri anahtarın yerine geçmez; anahtardan sonra da lazım olan kısmı (tek kapı, kalıcı durum, tek önbellek) yapar.

**(b) Öneri**
- `forge_core.kota`: `forge/veri/kota.db` (SQLite, WAL) içinde `istekler(kaynak, ts, durum)` ve `engel(kaynak, bitis_ts, neden, kalici_mi)`. Her HTTP çağrısı önce engel tablosuna bakar: engel sürüyorsa HTTP atılmaz, `ARANAMADI(kaynak, bitis_ts)` döner (bulunamadı değil). 429 + Retry-After ≥ eşik → engel yazılır; Retry-After yoksa "geçici" sayılır (60–300 sn engel), kalıcı kota sayılmaz.
- `OPENALEX_API_KEY` ve `mailto` tek yerden (`forge/ayar.toml`, repoda yok) okunur; tüm araçlar aynı anahtarla aynı kapıdan geçer. Anahtar gelince tablo hâlâ "bugün kaç istek" ölçer.
- Ortak yanıt önbelleği (`forge/veri/http.db`): anahtar = kaynak+URL+param. OpenAlex DOI/arXiv aramaları araçlar arasında paylaşılır; TTL kaynak başına (OpenAlex metaverisi 30 gün, arama sonuçları 7 gün) ve TTL dolunca "bayat" etiketi yazılır.
- `maliyet-sayaci tools` bu tablodan günlük istek ve engel durumunu da raporlar (yalnız sayı).
- MCP gerekmez: SQLite dosyası çok süreçli kilidi çözer; MCP bu durumda gereksiz süreç ekler.

**(c) Beklenen kazanç:** İki araç birbirinin bütçesini habersiz yemez; kota bitince hızlıca ve doğru etiketle ("ARANAMADI, X saatte açılır") döner. Gereksiz tekrar istek ve gereksiz bekleme (gapmine duman koşusunda ~38 sn arXiv nezaketi, kota bitikken boşuna denemeler) azalır. Geçici 429'un koşuyu öldürmesi (K2, K6–K9 ilk koşular) engellenir.

**(d) Maliyet:** 6–8 saat (tasarım, SQLite kilit testleri, iki araca bağlama). Token: ~200–300 bin. gapmine'a bağlama dondurma nedeniyle isteğe bağlı.

**(e) Metrik ve eşik:** Sentetik test: 2 süreç aynı anda aynı sahte kaynağa 100'er istek atar, kaynak 50. istekten sonra 429+Retry-After verir. Eşik: (i) toplam gerçek HTTP isteği ≤ 50 + 2 (yarış payı), (ii) Retry-After süresince 0 ek istek, (iii) 5 dakika sonra geçici 429'da yeniden deneme. Canlı ölçüt (anahtar yoksa): ilk 10 iddialık partide EKSİK koşu oranı, DENETIM taban çizgisi 7/10 → hedef ≤ 4/10; (anahtar varsa bu ölçüt anlamsızlaşır, yerine "429 sayısı = 0").

**(f) Öldürme kriteri:** OpenAlex anahtarı alınıp 30 gün boyunca hiçbir araç 429 almazsa kota defteri iptal edilir (yalnız ortak önbellek kalır). Ortak önbelleğin isabet oranı (aynı URL'ye ikinci istek) 30 günde < %10 ise önbellek de bırakılır.

---

## Öneri 5: Tek koşu günlüğü sözleşmesi, hata görünürlüğü ve sürüm damgası

**(a) Sorun ve kanıt**
- maliyet-sayaci `tools` modu yalnız `gapmine/reports/*.json` ile `forge/araclar/*/logs/maliyet*.json[l]` okuyor (`maliyet_sayaci.py:448-454`). makale-okuyucu böyle bir dosya yazmıyor; maliyet verisi `data/cache.db` `runs`/`llm_calls` tablolarında (`store.py:15-30`). SPEC bunu kendisi söylüyor: "makale-okuyucu henüz yok; bu sözleşmeye uyarak yazdığında otomatik okunur." Yani kabul edilen sayaç, kendi kardeş aracının harcamasını göremiyor, ve "hiçbir uyarı söylemiyor" (hakem raporu, maliyet-sayaci "Eksik" maddesi, 20 denetim koşusu görünmüyor).
- Hata görünürlüğü araç başına farklı: makale-okuyucu stderr'e tek satır `LOG:` basıyor (`cli.py:15-24`), gapmine `errors` tablosu + `data/logs/gapmine.log`. Asistan stderr'i çoğu zaman görmez (Hooks belgesi: exit 0 olan hook'un stderr'i Claude'a gitmez; benzer şekilde Bash çıktısında stderr ayrı yorumlanır). Yani "dürüst durum bilgisi" ilkesi çıkışa değil log'a bağlı kalıyor.
- Sürümleme: `config.VERSION = "0.1.0"` kartlara yazılıyor (`core.py:143,149`) ama `Store.resolve` yalnız `card_json IS NOT NULL` bakıyor (`store.py:59-64`); sürüm değişince eski kart sessizce "geçerli önbellek" olarak dönüyor. README bunu "Önbellek süresiz, sürüm değişince kartlar otomatik yenilenmez" diye kabul ediyor. gapmine için de aynı (`raw_responses` hiç eskimiyor).
- KAYIT.md hangi sürümün kabul edildiğini yazmıyor (maliyet-sayaci'nın sürüm sabiti yok; `grep -n VERSION` boş).

**(b) Öneri**
- `forge_core.kosu`: her komut sonunda `forge/veri/kosular.jsonl`'e tek satır JSON ekler: `{ts, arac, surum, core_surum, komut, durum (OK|PARTIAL|EKSİK|HATA), eksik_nedenler[], hatalar[kod:sayı], llm{calls,failed,input_tokens,output_tokens,cache_read_tokens,cache_write_tokens,cost_usd}, sure_s, girdi_ozeti}`. Maliyet-sayaci `tools` modu bu dosyayı okur (mevcut `llm` bloğu sözleşmesiyle uyumlu, yeni dosya adı eklenir).
- Kural: sıfırdan farklı `eksik_nedenler` ya da `hatalar` varsa stdout'un ilk satırı `DURUM: ...` olur (Öneri 2'deki gibi). Başarısızlık stdout'a girer, stderr'e değil.
- Her aracın `--version` komutu ve çıktısında sürüm; `kosular.jsonl` her satırda sürüm taşır. Kart/önbellek kayıtları `(arac_surum, sema_surum)` damgalı; `resolve` şema sürümü uyuşmazsa "bayat, `--force` öner" der (otomatik yeniden okuma yapmaz çünkü LLM maliyeti var).
- Doğrulama: "enjekte edilmiş sessiz hata" testi: LLM'i %30 oranında PARSE_FAIL döndüren mock ile koş; kart `PARTIAL` işaretlenmeli, `kosular.jsonl`'de `hatalar` dolu, stdout ilk satırı `DURUM: PARTIAL`.

**(c) Beklenen kazanç:** Tüm araçların harcaması ve başarısızlığı tek dosyada; maliyet-sayaci hakemin istediği "20 denetim koşusu görünmüyor" körlüğünü kapatır. Sürüm bilgisi kabul kayıtlarında izlenebilir olur.

**(d) Maliyet:** 3–4 saat. Token: ~60–100 bin.

**(e) Metrik ve eşik:** (i) `maliyet-sayaci tools` toplamı, bağımsız `sqlite` sorgusuyla `cache.db` toplamına ±%2 içinde eşit (hakemin kullandığı eşikle tutarlı). (ii) Görünürlük: 20 rastgele koşunun %100'ü `kosular.jsonl`'de var. (iii) Enjekte hata testinde 10/10 koşuda ilk satır `DURUM:` ≠ OK.

**(f) Öldürme kriteri:** `kosular.jsonl` 30 gün boyunca kimse (asistan ya da kullanıcı) tarafından okunmazsa (maliyet-sayaci `tools` çağrılmaz) ve araçların kendi SQLite log'ları zaten yeterliyse, ortak jsonl kaldırılır; maliyet-sayaci doğrudan `runs` tablosunu okuyan ek bir okuyucu ile yetinilir.

---

## Öneri 6: Otomatik regresyon ve "eşik kilidi": yerel pre-commit + `kontrol.ps1`; eşik dosyası commit'ten önce yazılmadan kabul koşusu başlamaz

**(a) Sorun ve kanıt**
- Protokolün 5. maddesi "kanıt testi kalıcıdır; her değişiklikten sonra yeniden koşulur" diyor (`README.md`), ama bunu zorlayan bir şey yok. Testler elle koşuluyor (`pytest` iki farklı venv'de: makale-okuyucu `.venv`, maliyet-sayaci sistem Python'u). Süreler kısa: 38 sn ve 1,5 sn (ölçtüm), yani otomasyonun önünde teknik engel yok.
- Hakem: eşikler sonradan yazıldı, ve "git yok, commit zamanı yok" (§2 Forge). Sonradan `forge/.git` oluşturulmuş (3 commit: `27f60e3`, `a636c35`, `bea1d08`) ama commit'e bağlayan bir kapı yok; `.gitignore` `data/` ve `*.db`'yi dışarıda bırakıyor, yani kanıt verisi (kartlar, smoke çıktıları) repoda değil.
- Testler mock LLM ve fixture ile koşuyor: gapmine'ın 168 testi "recall'u ölçmüyor" (hakem), makale-okuyucu'nunki de `ask` doğruluğunu ölçmüyor. Birim regresyon ile kabul regresyonu karışmış durumda.
- `HAKEM-RAPORU.md`: "ŞARTLI" rolünün eşiği yok; "stokastik araçlarda en az 3 koşu" şartı yok.

**(b) Öneri**
- İki katman: (1) **birim regresyon**: `forge/kontrol.ps1` her aracın kendi Python'uyla `pytest` koşar, ≤ 2 dk, çıkış kodu toplanır. Git `pre-commit` hook'u bunu çağırır; ayrıca isteğe bağlı Claude Code `PostToolUse` hook'u (`Edit|Write`, yol `forge/araclar/<ad>/` altındaysa o aracın hızlı alt kümesi) hata olursa exit 2 ile stderr'i Claude'a gösterir. (2) **kabul regresyonu**: `@pytest.mark.kabul` işaretli testler yalnız elle/PR öncesi koşar (LLM/ağ gerektirebilir), sonuç `kanit/<arac>/<tarih>.json`'a düşer.
- **Eşik kilidi:** her araç klasöründe `ESIK.json` (metrik adı, eşik, koşu sayısı k≥3, rol, tarih). `kontrol.ps1 kabul <arac>` yalnız şu koşulda başlar: `ESIK.json` git'te commit edilmiş, çalışma ağacında değişmemiş ve commit zamanı ilk `kanit/` sonuç dosyasından önce. Aksi halde "ESIK_KILIDI_ACIK" ile reddeder. Bu, hakemin "ön kayıt kanıtı yok" bulgusunun mekanik karşılığı.
- `.gitignore`: küçük kanıt dosyaları (`kanit/**/*.json`, kartlar) repoda tutulur; `*.db` ve PDF'ler dışarıda kalır.
- Not: uzak bir CI (GitHub Actions) bu tek-kullanıcılı yerel sistem için fazla; repo uzağa itilirse eklenir.

**(c) Beklenen kazanç:** Regresyon unutulamaz; eşik sonradan değiştirilemez (ya da değiştirildiği commit zamanıyla görünür). Protokolün "ön kayıt" iddiası mekanik olarak kanıtlanabilir olur.

**(d) Maliyet:** 3–4 saat. Token: ~50–80 bin.

**(e) Metrik ve eşik (mutasyon testiyle):** Her araca 5 kasıtlı hata enjekte et (örn. quotecheck'te normalizasyonu kapat, fiyat tablosunda cache_read'i 10 kat yap, `ask`'te `references` filtresini kaldır...). Eşik: `kontrol.ps1` ≥ 4/5'ini yakalar ve toplam süre ≤ 3 dk. Kilit testi: `ESIK.json`'u commit etmeden `kabul` koşusu 3/3 denemede reddedilir; commit'ten sonra kabul eder.

**(f) Öldürme kriteri:** Mutasyon testinde yakalama < 3/5 ise birim testler "regresyon koruması" olarak sayılmaz (bu kendi başına bulgu: testler gerçek hata yakalamıyor); hook otomasyonu durdurulur, test yazımına dönülür. Pre-commit hook 30 günde ≥ 5 kez `--no-verify` ile atlanırsa hook kaldırılır ve yalnız `kontrol.ps1` elle kalır.

---

## Öneri 7: SPEC → inşa → denetim hattını şablon + rol tanımı + bağımsızlık korumasıyla standartlaştır

**(a) Sorun ve kanıt**
- Üç araç üç farklı SPEC düzeni: gapmine SPEC (81 satır, "Yasak" bölümüyle altın seti koruma), makale-okuyucu SPEC (90 satır, kabul bölümü "eşik denetçi tarafından yazılır"), maliyet-sayaci SPEC (88 satır, gizlilik sözleşmesi). Ortak zorunlu bölümler (çıktı bütçesi, log sözleşmesi, eşik, altın set konumu, sürüm) yok.
- Bağımsızlık ihlali somut: gapmine SPEC'in "Yasak" maddesi altın set klasörünü okumayı yasaklıyor, ama altın set sonradan `gapmine/karsilastirma/altin/gold.json` (aracın klasörü) içine kondu ve v2'yi yazan ajan `DENETIM.md`'yi okudu (hakem §2, §3 madde 5). Yasak yalnız metindi; mekanik korumaz.
- Denetçi aynı oturum/model (hakem §2: "aynı model, `a38f17e9`"), brifi aracı yazan yazdı.
- `~/.claude/agents/` altında zaten SPEC→inşa→denetim zincirinin Epic sürümü var (`planlayici`, `cad-tasarimci-v2`, `denetci-v2`, `dogrulayici`, `agent flow v2`); Forge yazılım araçları için buna denk bir zincir tanımlamamış.
- Belgeler: subagent frontmatter'ında `model`, `tools`, `skills`, `hooks` var; alt-ajan hook'u (`PreToolUse`) yalnız o ajan çalışırken yol-engeli uygulayabilir.

**(b) Öneri**
- `forge/sablon/SPEC.md`: zorunlu bölümler: Amaç, İş bölümü tablosu (kod/ucuz LLM/pahalı), Girdi/Çıktı, **Çıktı bütçesi (Öneri 2)**, **Log/durum sözleşmesi (Öneri 5)**, Kota/ağ, Gizlilik, **Kabul: taban çizgisi yöntemi, metrik, eşik, k koşu sayısı, rol (ŞARTLI ise) (Öneri 6 `ESIK.json`'a kopyalanır)**, Altın set konumu (`forge/kanit/`, araç klasörü dışı), Bilinen zayıflıklar.
- Üç rol, üç alt-ajan tanımı (`~/.claude/agents/forge-spec.md`, `forge-insa.md`, `forge-denetci.md`):
  - `forge-insa`: `tools` = Read/Write/Edit/Bash/Glob/Grep; **`hooks: PreToolUse`** `forge/kanit/**` ve `**/DENETIM*.md` yollarını okumayı/aramayı reddeder. Girdi: yalnız `SPEC.md` + `forge_core`.
  - `forge-denetci`: farklı `model:` (aracı yazandan farklı model ailesi ya da en azından farklı bir model; hakemin önerisi), Write izni yalnız kendi rapor dosyasına; brifi aracı yazan değil **şablondan** gelir (sabit metin), yazarın yorumu eklenmez. Altın seti yalnız o görür.
  - `forge-spec`: gereksinimi şablona döker, eşiği `ESIK.json`'a yazar ve commit ister (Öneri 6).
- Paralel hat: SPEC onaylandıktan sonra bağımsız araçlar (olum-testcisi, ders-modu...) ayrı `isolation: worktree` ile paralel inşa edilir; her biri `kontrol.ps1`'i yeşil yapmadan denetime geçmez. Denetim bulguları, Epic'teki `dogrulayici` kalıbıyla "DOĞRULANDI/ÇÜRÜTÜLDÜ/ÖLÇÜLEMEZ" sınıfına girer; inşacı yalnız DOĞRULANDI olanı düzeltir (hakemin yakaladığı "yanlış bulguyu uygula" riskini keser; zaten `cad-tasarimci-v2` aynı mantıkla yazılmış).
- Şablonun uyum denetimi: `kontrol.ps1 spec <arac>` zorunlu başlıkların varlığını grep'le doğrular (LLM yok).

**(c) Beklenen kazanç:** Yeni araç için "SPEC yaz → başla" 1 oturumda; bağımsızlık sözlü yasak değil mekanik engel; denetim kalıbı tekrar kullanılır, her seferinde sıfırdan kurulmaz. Hakemin 3 metodolojik bulgusu (eşik sonradan, aynı model denetçi, kirli altın set) süreçte kapanır.

**(d) Maliyet:** 5–6 saat (şablon, 3 ajan tanımı, hook betiği, uyum denetleyicisi) + ilk denemede olum-testcisi için bir tam hat koşusu (~$5–10 liste fiyatıyla; maliyet-sayaci ile ölçülür). Token: ~250–400 bin (hattı gerçek bir araçla denemeyi içerir).

**(e) Metrik ve eşik:** Olum-testcisi bu hatla inşa edilir. Eşik: (i) `kontrol.ps1 spec` 11/11 zorunlu başlık; (ii) inşa transkriptinde `forge/kanit/` ve `DENETIM*` yollarına okuma = 0 (hook log'u + transkript `grep`, içerik okumadan yalnız yol alanı); (iii) denetçi ajanın `model` değeri inşacının değerinden farklı; (iv) SPEC onayından kabul kararına kadar insan müdahalesi ≤ 3 (onay, eşik, nihai karar); (v) toplam harcama maliyet-sayaci ile ölçülür ve öncesinde yazılan tavanın (örn. 15 $) altında.

**(f) Öldürme kriteri:** İlk tam hat koşusunda toplam maliyet (liste fiyatı) elle yapılan eşdeğer işin 2 katını geçerse ya da hat 2 araçtan sonra (olum-testcisi + bir tane daha) hiç yeniden kullanılmazsa, tek-seferlik süreç olarak kalır: şablon korunur, 3 ajan tanımı silinir. Hook bağımsızlık koruması ilk 3 denemede ≥ 1 yanlış-pozitif engel (meşru okumayı reddetme) üretirse hook yerine "yol listesi brife yazılır + sonradan transkript denetimi" yöntemine dönülür.

---

## Uygulama sırası ve toplam maliyet (tahmin)

| Sıra | Öneri | Saat | Token | Neden bu sırada |
|---|---|---|---|---|
| 1 | Öneri 1 (bağlama, pilot maliyet-sayaci) | 3–4 | 60–100 B | Kabul edilmiş araç hâlâ kullanılamıyor; en ucuz kazanç |
| 2 | Öneri 2 (çıktı bütçesi) | 3 | 30–50 B | Öneri 1'in skill şablonuna girer |
| 3 | Öneri 6 (regresyon + eşik kilidi) | 3–4 | 50–80 B | Yeni araçtan önce kural; hakem bulgusunu doğrudan kapatır |
| 4 | Öneri 5 (günlük sözleşmesi) | 3–4 | 60–100 B | maliyet-sayaci körlüğünü kapatır |
| 5 | Öneri 3 (forge-core) | 5–6 | 150–250 B | 3. araç yazılmadan önce |
| 6 | Öneri 7 (hat) | 5–6 | 250–400 B | 2, 5, 6 hazır olunca anlamlı |
| 7 | Öneri 4 (kota defteri) | 6–8 | 200–300 B | OpenAlex anahtarı sonrası değeri ölçülür; anahtar sorunu çözerse küçülür |

Toplam ≈ 28–35 saat, ≈ 0,8–1,3 milyon token. Not: Öneri 4 anahtara bağımlı; anahtar alınırsa en sona kalır.

## Dürüstlük notları
- Süre ve token rakamları öngörüdür, ölçüm değildir. Ölçülen: iki test paketinin süresi (38 sn ve 1,5 sn), dosya satır sayıları, diff satır sayıları, `card.json`/`ask_*.json` bayt boyutları.
- Token tahminleri karakter/3,5–4 ile yapıldı (makale-okuyucu'nun kendi tahmini); gerçek sayım değil.
- Claude Code belge sayfaları kesik okundu (her biri ilk ~100.000 karakter); ilgili bölümlerin hepsi kapsandığı iddia edilmez. Özellikle MCP tool search bağlam maliyeti sayısı belgede bulunamadı; bu yüzden MCP için bağlam maliyeti rakam verilmedi.
- `kosular.jsonl`, `forge_core`, `ESIK.json` ve alt-ajan hook yolları tasarım önerisidir; hiçbiri denenmedi. Alt-ajan frontmatter `hooks` ile `PreToolUse` yol engelinin okuma yollarını gerçekten engellediği kurulum öncesi küçük bir deneyle doğrulanmalı (Öneri 7'nin ilk adımı).
