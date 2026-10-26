# Orkestra özeti
Soru: Karmaşık bellek erişim örüntülerini tahmin eden akıllı veri önceden getirme (prefetching) teknikleri üzerine en önemli çalışmalar ve açık problemler neler?
Kesim: 2026-05-08 | koşu: 20261026-043122-04b193
Durum: EKSİK (eksik: openalex, s2_zenginlestirme)
Maliyet (teorik, liste fiyatı): $0.566 | süre: 1281 s

## Funnel
- toplama:openalex: 0 → 0 (düşen: –)
- cozumleme:sef_capa: 25 → 25 (düşen: –)
- cozumleme:web: 33 → 17 (düşen: cozulemedi 13, tekrar_baslik 3)
- toplama:crossref: 4000 → 3872 (düşen: tur_disi:dataset 74, tur_disi:peer-review 31, basliksiz 23)
- toplama:dblp: 3 → 3 (düşen: –)
- toplama:arxiv: 5198 → 5198 (düşen: –)
- tekillestirme_1: 9115 → 6287 (düşen: birlesti 2828)
- kesim_1: 6287 → 6194 (düşen: tarih_belirsiz 92, tarih_yok 1)
- toplama:atif: 1496 → 485 (düşen: tavan_kesimi 1008, meta_yok 3)
- tekillestirme_2: 6679 → 6478 (düşen: birlesti 201)
- kesim_2: 6478 → 6446 (düşen: tarih_belirsiz 1, tarih_yok 31)
- okuyucu_kesimi: 6446 → 1200 (düşen: on_siralama_kesimi 5246)
- okuyucu: 1200 → 820 (düşen: kesin_alakasiz 380)
- damitma: 820 → 80 (düşen: ilk_kart_disi 740)
- sef_final: 80 → 30 (düşen: secilmedi 50)
Kaynaklar: sef_plan OK; openalex EKSİK [bütçe: günlük anahtarsız bütçe (80) doldu]; web OK; crossref OK; dblp OK; arxiv OK; s2_zenginlestirme EKSİK [s2: HTTP 429: 3 denemede 429]; atif OK; ozet_arxiv OK; sef_final OK

## 30 çalışma (önem sırasıyla)
1. doi:10.1109/12.381947 — Effective hardware-based data prefetching for high-performance processors (1995-05). Yüksek performanslı işlemciler için donanım tabanlı veri önceden getirmenin klasik temelini ve stride temelli yöntemleri sunar (S1). «alıntı yok: özet erişilemedi»
2. doi:10.1145/143365.143488 — Design and evaluation of a compiler algorithm for prefetching (1992-09). Derleyici tabanlı prefetching algoritmasının tasarım ve değerlendirmesini yapan, yazılım prefetching'inin klasik temel çalışmasıdır (S1). «alıntı yok: özet erişilemedi»
3. doi:10.1145/264107.264207 — Prefetching using Markov predictors (1997-05). Markov tahmincileriyle prefetching yapar; adres korelasyonlu prefetcher ailesinin klasik çıkış noktasıdır (S1, S2). «alıntı yok: özet erişilemedi»
4. doi:10.1109/mm.2005.6 — Data Cache Prefetching Using a Global History Buffer (2005-01). Global history buffer önerir; adres korelasyonlu zamansal prefetching için yaygın biçimde kullanılan temel yapıdır (S2). «alıntı yok: özet erişilemedi»
5. doi:10.1109/hpca.2007.346185 — Feedback Directed Prefetching: Improving the Performance and Bandwidth-Efficiency of Hardware Prefetchers (2007). Geri beslemeli prefetching ile donanım prefetcher'larının agresifliğini ve bant genişliği verimliliğini kontrol eden temel çalışmadır (S6). «alıntı yok: özet erişilemedi»
6. arXiv:1803.02329 — Learning Memory Access Patterns (2018-03-06). Prefetching stratejilerini n-gram modelleriyle ilişkilendirir ve tekrarlayan sinir ağlarını doğrudan ikame olarak önerir; ML prefetching'in merkezi çalışmasıdır (S4). «We relate contemporary prefetching strategies to n-gram models in natural language processing, and show how recurrent neural networks can serve as a drop-in replacement»
7. arXiv:2109.12021 — Pythia: A Customizable Hardware Prefetching Framework Using Online Reinforcement Learning (2021-09-24). Çevrimiçi pekiştirmeli öğrenmeyle özelleştirilebilir prefetcher sunar; önceki prefetcher'ların farklı iş yükü ve sistemlerde kazanç kaybettiğini gösterir (S4, S8). «We show that prior prefetchers often lose their performance benefit over a wide range of workloads and system configurations due to their inherent inability»
8. doi:10.1109/micro.2016.7783763 — Path confidence based lookahead prefetching (2016-10). Delta tabanlı SPP; yol güven skoruyla lookahead prefetching yapan etkili bir yöntem ailesini temsil eder (S3). «alıntı yok: özet erişilemedi»
9. doi:10.1109/hpca.2016.7446087 — Best-offset hardware prefetching (2016-03). En iyi offset'i seçen delta/offset tabanlı donanım prefetcher'ıdır; offset ailesinin temel çalışmasıdır (S3). «alıntı yok: özet erişilemedi»
10. doi:10.1145/1150019.1136508 — Spatial Memory Streaming (2006-05). Kod korelasyonlu uzamsal erişim örüntülerini tanıyıp blokları talep kaçırmalarından önce önbelleğe aktaran uzamsal prefetching'in temel çalışmasıdır (S3). «we propose Spatial Memory Streaming, a practical on-chip hardware technique that identifies codecorrelated spatial access patterns and streams predicted blocks to the primary cache ahead of demand misses»
11. doi:10.1145/1555815.1555766 — Spatio-temporal memory streaming (2009-06-15). Bölge erişimlerinin zamansal sırasını kaydedip oynatır ve bölge içi uzamsal ilişkileri kullanarak zamansal ve uzamsal streaming'i birleştirir (S2, S3). «STeMS records and replays the temporal sequence of region accesses and uses spatial relationships within each region»
12. doi:10.1109/hpca.2018.00021 — Domino Temporal Data Prefetcher (2018-02). Adres geçmişi tabanlı korelasyon kullanan önemli bir zamansal veri prefetcher'ıdır (S2). «alıntı yok: özet erişilemedi»
13. doi:10.1145/2540708.2540730 — Linearizing irregular memory accesses for improved correlated prefetching (2013-12-07). Düzensiz bellek erişimlerini doğrusallaştırarak korelasyonlu prefetching'i iyileştirir; düzensiz örüntüler için kilit yaklaşımdır (S2). «alıntı yok: özet erişilemedi»
14. doi:10.1109/hpca.2009.4798239 — Practical off-chip meta-data for temporal memory streaming (2009-02). Zamansal bellek akışı için pratik off-chip metaveri depolama önerir; metaveri depolama problemine doğrudan yanıt verir (S2). «alıntı yok: özet erişilemedi»
15. arXiv:2406.10627 — Triangel: A High-Performance, Accurate, Timely On-Chip Temporal Prefetcher (2024-06-15). Zamansal prefetching'in ticari tasarımlarda uygulanabilir hale geldiğini belirten, doğru ve zamanında çalışan on-chip zamansal prefetcher'dır (S2). «Temporal prefetching, where correlated pairs of addresses are logged and replayed on repeat accesses, has recently become viable in commercial designs.»
16. doi:10.1145/3445814.3446752 — A hierarchical neural model of data prefetching (2021-04-17). Veri prefetching için hiyerarşik sinir ağı modeli önerir; güncel ve sık atıf alan bir ML yaklaşımıdır (S4). «alıntı yok: özet erişilemedi»
17. doi:10.1145/3307650.3322207 — Perceptron-based prefetch filtering (2019-06-22). Perceptron tabanlı prefetch filtreleme sunar; öğrenme tabanlı yaklaşım ile isabetsiz prefetch'leri ayıklar (S4, S6). «alıntı yok: özet erişilemedi»
18. arXiv:1804.00478 — A Neural Network Prefetcher for Arbitrary Memory Access Patterns (2018-03-19). Program ve makine bağlam bilgisini erişim örüntüleriyle ilişkilendiren, çevrimiçi eğitimle uyum sağlayan sinir ağı prefetcher'ıdır (S4). «the proposed NN prefetcher correlates program and machine contextual information with memory accesses patterns, using online-training to identify and dynamically adapt to unique access patterns»
19. arXiv:2205.02269 — Fine-Grained Address Segmentation for Attention-Based Variable-Degree Prefetching (2022-05-01). İnce taneli adres bölütleme ve delta bitmap'leriyle attention tabanlı, değişken dereceli prefetching önerir; transformer ailesini temsil eder (S4). «To reduce vocabulary size, we use fine-grained address segmentation as input. To predict unordered sets of future addresses, we use delta bitmaps for multiple outputs»
20. doi:10.1109/hpca.2019.00053 — Bingo Spatial Data Prefetcher (2019-02). Bölgesel örüntü tabanlı Bingo uzamsal veri prefetcher'ı, uzamsal prefetching'in güçlü bir güncel temsilcisidir (S3). «alıntı yok: özet erişilemedi»
21. doi:10.1109/micro56248.2022.00072 — Berti: an Accurate Local-Delta Data Prefetcher (2022-10). Berti, yerel delta tabanlı doğru veri prefetching sunan güncel bir delta prefetcher ilerlemesidir (S3). «alıntı yok: özet erişilemedi»
22. arXiv:1910.03075 — DSPatch: Dual Spatial Pattern Prefetcher (2019-10-07). Mevcut bant genişliğine göre kapsamayı artıran veya doğruluk için kısan uyarlamalı uzamsal prefetcher'dır (S3, S6). «Prefetchers need the ability to dynamically adapt to available bandwidth, boosting prefetch count and prefetch coverage when headroom exists and throttling down to achieve high accuracy»
23. doi:10.1145/2907071 — A Survey of Recent Prefetching Techniques for Processor Caches (2016-08-02). İşlemci önbellekleri için güncel prefetching tekniklerinin uygulanmasını ve etkinliğini inceleyen kapsamlı bir derlemedir (S1, S8). «In this article, we survey several recent techniques that aim to improve the implementation and effectiveness of prefetching.»
24. doi:10.1145/285930.285958 — Retrospective: improving direct-mapped cache performance by the addition of a small fully-associative cache and prefetch buffers (1990-05). Küçük tam ilişkili önbellek ve prefetch tamponlarıyla erken donanım prefetching/stream tamponu önerilerinin klasik kökenidir (S1). «Small miss caches of 2 to 5 entries are shown to be very effective in removing mapping conflict misses in first-level direct-mapped caches.»
25. doi:10.1145/237090.237190 — Compiler-based prefetching for recursive data structures (1996-09). Özyinelemeli veri yapıları içeren işaretçi tabanlı uygulamalar için derleyici tabanlı prefetching'i inceler (S1, S2). «This paper investigates compiler-based prefetching for pointer-based applications---in particular, those containing recursive data structures»
26. doi:10.1109/icpp.2003.1240591 — A hardware-based cache pollution filtering mechanism for aggressive prefetches (2003). Agresif prefetch'lerin neden olduğu önbellek kirliliğini donanım tabanlı filtrelemeyle azaltır (S6). «alıntı yok: özet erişilemedi»
27. doi:10.1145/3090635 — Band-Pass Prefetching (2017-06-28). Çok çekirdekli sistemlerde bir uygulamanın prefetcher'ının paylaşılan kaynaklarda diğerlerine girişim yapması sorununu ele alır (S6, S8). «In multi-core systems, an application’s prefetcher can interfere with the memory requests of other applications using the shared resources»
28. doi:10.1145/2925426.2926254 — Graph Prefetching Using Data Structure Knowledge (2016-06). Graf analitiğinde veri yapısı bilgisini kullanarak prefetching yapar; komşu alan düzensiz erişimleri için önemlidir (S7). «alıntı yok: özet erişilemedi»
29. doi:10.1145/605397.605427 — A stateless, content-directed data prefetching mechanism (2002-10). İşletim sistemi bellek tahsisinden yararlanan, işaretçi yoğun uygulamalar için durumsuz içerik yönlendirmeli prefetching önerir (S2, S7). «This paper proposes Content-Directed Data Prefetching, a data prefetching architecture that exploits the memory allocation used by operating systems and runtime systems to improve the performance of pointer-intensive ap…»
30. doi:10.1109/ispass.2018.00028 — A Workload Characterization of the SPEC CPU2017 Benchmark Suite (2018-04). Prefetching değerlendirmelerinde kullanılan SPEC CPU2017 kıyaslama setinin iş yükü karakterizasyonunu sunar (S5). «alıntı yok: özet erişilemedi»
