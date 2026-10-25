# Yerel arXiv dizini: eşdeğerlik ve kurulum sonuçları (2026-10-26)

Tasarım: `forge/gelistirme/ONERI-arxiv-yerel.md`. Kabul 1 (eşdeğerlik, ağsız) ve 3 (boyut/iş) bu dosyada.
Kabul 2 (uçtan uca) YAPILMADI (ağ ve deney kısıtı).

## Dizin
- Dosya: `forge-veri/arxiv_yerel.sqlite`, **5 158 MB** (≤ 8 GB: geçti).
- Kurulum: **659 s ≈ 11 dk** (satır 632 s + FTS 8 s; ≤ 30 dk: geçti), tek iş parçacığı. Bu oturumda yeniden kurulmadı; önceki ajanın kurulumu doğrulandı.
- Tutarlılık:
  - `PRAGMA quick_check` = ok (33 s).
  - `kayit` 3 215 242 satır = `meta.kayit_sayisi` = FTS `ara_docsize` satırı.
  - Id'ler tekil.
  - Parquet toplamı 3 215 335 satır; fark 93 = `tekrar_id` (meta). Tutarlı.
- Anlık görüntü: en yeni v1 2026-10-15, en yeni update_date 2026-10-16.

## Testler
`orkestra/tests`: **82 geçti, 7 deselected** (işaretli, ağlı testler). Yerel-dizin testleri dahil, hepsi yeşil.
Bu oturumda tek kod değişikliği: `sources/arxiv_yerel.by_titles` (aşağıdaki bulgu 4); değişiklikten sonra da 82 geçti.

## Eşdeğerlik (Kabul 1)
Yöntem: `http_cache.sqlite` salt-okunur URI ile açıldı, sqlite3 backup API ile `gelistirme/esdeger/http_cache_kopya.sqlite`
(git dışı, `*.sqlite`) kopyalandı; asıl dosyaya yazılmadı, ağ yok. Önbellekte **962** benzersiz arXiv sorgusu
(ifade + kesim) var, `ti:` ve `id_list` istekleri ayrı. Çıktı `arxiv_esdeger.py`: her canlı sorgunun ifadesi FTS5'e
birebir çevrilip aynı kesimle (`v1_tarih < kesim`) yerelde koşuldu.

Tüm 962 sorgu bu makinede zaman olarak mümkün olmadı: deney CPU/disk'i paylaştığı için (dizin 5 GB, soğuk önbellek) 300'lük
rastgele örnek (seed 1) başlatıldı; **269 sorgu** tamamlanmadan başlık aşaması takıldı ve işlem durduruldu. Sayılar, çalışan işlemin
bellek durumundan okundu (`py-spy dump --locals`); `esdeger_sonuc.json` üretilemedi. Aşağıda yalnız okunabilen sayılar var; top-10
ve kademe kırılımı okunamadı.

| ölçüt | değer |
|---|---|
| tamamlanan sorgu (örnek) | 269 (23'ü OR kademesi) |
| canlı sonuç id | 16 177 |
| **yerel tüm eşleşmede bulunan** | **15 546 = %96,1** |
| yerel kademe tavanı içinde (AND 100 / MAJ 100 / OR 200, bm25 sırası) | 10 707 = %66,2 |
| başlık araması (örnek, canlı eşleşen başlık) | 18 / 19 = %94,7 |

**Karar: Kabul 1 geçti** (%96,1 ≥ %90, tüm eşleşme tabanında). Uyarı: tavan tabanında oran %66; bu, sıralamanın
arXiv'inkinden farklı olmasından geliyor (canlıda ilk 100'e giren kayıt yerelde 100'ün ötesinde kalabilir). Kabul
metni "aynı kesimle bulunma" dedi, tavan sınırı koymadı; bu yüzden asıl sonuç %96,1. Ama uçtan uca recall (Kabul 2) tavan
farkından etkilenebilir; orada ölçülmeli.

### Kaçanlar (631 = %3,9)
| sebep | sayı | yorum |
|---|---|---|
| metin_eslesmiyor (başlık+özet) | 476 | Canlı `all:` başlık+özet dışında yorum, yazar, dergi künyesi, kategori alanlarını da tarar; yerel yalnız başlık+özet. Sistematik, beklenen. |
| baska (terimler metinde var, FTS eşleşmedi) | 128 | Tokenizer/kök farkı (porter ≠ arXiv'in kökleyicisi, tire/nokta/sayı bölme) ya da ifade yapısı. Tanı gevşek (ilk 5 harf) olduğundan üst sınır. |
| dizinde_yok | 27 | Anlık görüntüde olmayan id (snapshot sonrası ya da eksik). |

- **Tarih anlamı: eşdeğer.** Canlı `published` ile yerel `v1_tarih` karşılaştırılan 16 150 kayıtta 16 150 kez aynı gün (0 fark). `versions[0]` = v1 varsayımı doğrulandı; kesim süzgeci güvenli.
- **Kategoriler:** tanı başlık+özet eşleşmesine bakar, kategori sistematik kaçak olarak ayrılamadı (canlı sorgular `all:` kullanıyor, kategori süzgeci yok).
- **Tokenizer:** `io_uring` kararı (bölünür, tırnaklı ifade) kayda değer kayıp yaratmadı; 128'lik "baska" kümesi asıl tokenizer riski, ayrıştırılmadı.

## Bulgular / öneri
1. Eşdeğerlik yeterli; kalan fark çoğunlukla alan kapsamı (yorum/künye alanları dizinde yok).
2. **Performans riski:** sıcak önbellekte sorgular 0,0–2 s, ama deney yükü altında/soğuk dizinde geniş OR/MAJ sorguları ve bm25 sıralaması dakikalar sürdü. Kabul "toplama ≪ 10 s" bu koşullarda doğrulanmadı; kurulum sonrası dizinin önbelleğe ısıtılması ve OR kademesinde ön-süzgeç gerekebilir.
3. Kabul 2 (uçtan uca, n ≥ 10 soru, yeni altın set) yapılmadı.
4. **`by_titles` düzeltmesi:** yaygın kelimeli uzun başlıklarda (ör. "... Deep Learning Model ...") AND ifadesi milyonlarca eşleşmeyi bm25 ile sıraladı; tek başlık ~1 saat sürdü. Artık önce bitişik ifade (tam başlık) denenir, sonra AND, sonra OR; denemede aynı sorgular 0,6–2,3 s. Düzeltilmiş hâli tam eşdeğerlik koşusunda doğrulanamadı (testler yeşil).
5. `arxiv_esdeger.py`: `--sample N`, `--title-sample N`, ilerleme çıktısı eklendi; yanlış-yavaş `MATCH ... AND rowid=` tanısı Python'a taşındı.
