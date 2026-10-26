# Orkestra özeti
Soru: LSM-ağacı tabanlı anahtar-değer depolarında sıkıştırma (compaction) kaynaklı performans dalgalanması ve optimizasyon teknikleri üzerine en önemli çalışmalar ve açık problemler neler?
Kesim: 2025-06-13 | koşu: 20261025-205656-493172
Durum: EKSİK (eksik: openalex, s2_zenginlestirme)
Maliyet (teorik, liste fiyatı): $0.537 | süre: 1221 s

## Funnel
- toplama:openalex: 0 → 0 (düşen: –)
- cozumleme:sef_capa: 25 → 11 (düşen: cozulemedi 14)
- toplama:crossref: 3800 → 3688 (düşen: tur_disi:dataset 24, tur_disi:peer-review 45, tur_disi:component 8, tur_disi:journal-issue 8, basliksiz 5, tur_disi:proceedings 22)
- cozumleme:web: 44 → 25 (düşen: cozulemedi 12, tekrar_baslik 7)
- toplama:dblp: 12 → 12 (düşen: –)
- toplama:arxiv: 5482 → 5482 (düşen: –)
- tekillestirme_1: 9218 → 6789 (düşen: birlesti 2429)
- kesim_1: 6789 → 6749 (düşen: tarih_belirsiz 40)
- toplama:atif: 3730 → 479 (düşen: atif_yapan_kesim_sonrasi 243, tavan_kesimi 3007, meta_yok 1)
- tekillestirme_2: 7228 → 7073 (düşen: birlesti 155)
- kesim_2: 7073 → 7069 (düşen: tarih_belirsiz 3, tarih_yok 1)
- okuyucu_kesimi: 7069 → 1200 (düşen: on_siralama_kesimi 5869)
- okuyucu: 1200 → 820 (düşen: kesin_alakasiz 380)
- damitma: 820 → 80 (düşen: ilk_kart_disi 740)
- sef_final: 80 → 30 (düşen: secilmedi 50)
Kaynaklar: sef_plan OK; openalex EKSİK [QuotaExhausted: Retry-After=21751s]; web OK; crossref OK; dblp OK; arxiv OK; s2_zenginlestirme EKSİK [s2: HTTP 429: 3 denemede 429]; atif OK; ozet_arxiv OK; sef_final OK

## 30 çalışma (önem sırasıyla)
1. doi:10.1007/s002360050048 — The log-structured merge-tree (LSM-tree) (1996-06). LSM-ağacını tanımlayan temel çalışmadır ve tüm sıkıştırma araştırmalarının kavramsal başlangıç noktasıdır. «alıntı yok: özet erişilemedi»
2. arXiv:1812.07527 — LSM-based Storage Techniques: A Survey (2018-12-18). LSM-ağacı literatürünü sınıflandıran genel bir taksonomi sunar, çabaları ayrıntılı inceler ve güçlü yönler ile ödünleşimleri tartışır. «We provide a general taxonomy to classify the literature of LSM-trees, survey the efforts in detail, and discuss their strengths and trade-offs.»
3. arXiv:2202.04522 — Constructing and Analyzing the LSM Compaction Design Space (Updated Version) (2021-07). Sıkıştırma tasarım uzayını kurar; sıkıştırmanın yazma büyütmesi, verim, okuma, alan büyütmesi ve silme performansını temelden etkilediğini gösterir. «Compactions fundamentally influence the performance of an LSM-engine in terms of write amplification, write throughput, point and range lookup performance, space amplification, and delete performance.»
4. arXiv:1906.09667 — On Performance Stability in LSM-based Storage Systems (Extended Version) (2019-06-23). LSM-ağaçlarında hızlı bellek içi yazmalar ile yavaş arka plan G/Ç arasındaki uyumsuzluktan doğan yazma duraklamalarını ve performans varyansını inceler. «Despite the popularity of LSM-trees, they have been criticized for suffering from write stalls and large performance variances due to the inherent mismatch between their fast in-memory writes and slow background I/O ope…»
5. doi:10.1145/3380905 — SILK+ Preventing Latency Spikes in Log-Structured Merge Key-Value Stores Running Heterogeneous Workloads (2018-11-30). LSM anahtar-değer depolarındaki yüksek kuyruk gecikmesini belgeler ve verim odaklı tekniklerin bu sorunu çözmediğini gösterir. «We first document the fact that LSM KVs exhibit high tail latencies. The techniques that have been proposed for optimizing throughput do not address this issue»
6. doi:10.1145/3183713.3196927 — Dostoevsky (2018-05-27). LSM tasarım uzayını ve ödünleşimlerini ele alan, çok atıf almış etkili bir çalışmadır. «alıntı yok: özet erişilemedi»
7. doi:10.1145/3035918.3064054 — Monkey (2017-05-09). Bloom filtre ve birleştirme ayarını birlikte ele alan, çok atıf almış analitik LSM ayarlama çalışmasıdır. «alıntı yok: özet erişilemedi»
8. doi:10.1145/3299869.3319903 — The Log-Structured Merge-Bush &amp; the Wacky Continuum (2019-06-25). LSM tasarımında birleştirme politikalarını kapsayan bir süreklilik önerir; leveling ve tiering arasındaki uzayı genişletir. «alıntı yok: özet erişilemedi»
9. doi:10.1145/3132747.3132765 — PebblesDB (2017-10-14). Parçalı LSM yaklaşımıyla yazma büyütmesini azaltan, yüksek atıflı ve etkili bir veri yapısı çalışmasıdır. «alıntı yok: özet erişilemedi»
10. doi:10.1145/3033273 — WiscKey (2017-03-24). Anahtar-değer ayrımıyla yazma büyütmesini azaltan klasik çalışmadır ve bu yöntem ailesinin temelini oluşturur. «alıntı yok: özet erişilemedi»
11. doi:10.1145/2213836.2213862 — bLSM (2012-05-20). Birleştirme zamanlaması ve yazma duraklamaları konusunda erken dönem, çok atıf almış bir çalışmadır. «alıntı yok: özet erişilemedi»
12. doi:10.1145/1807128.1807152 — Benchmarking cloud serving systems with YCSB (2010-06-10). YCSB kıyaslama aracını tanıtır; LSM depolarının değerlendirilmesinde yaygın kullanılan standart iş yükü kaynağıdır. «alıntı yok: özet erişilemedi»
13. arXiv:2110.13801 — Endure: A Robust Tuning Paradigm for LSM Trees Under Workload Uncertainty (2021-10-26). İş yükü belirsizliği altında sıkıştırma politikası, boyut oranı ve bellek tahsisinin performansa etkisini ele alan sağlam bir ayarlama paradigması sunar. «Specifically, we focus on the impact of the choice of compaction policies, size-ratio, and memory allocation on the overall performance.»
14. doi:10.1145/3318464.3389757 — Lethe: A Tunable Delete-Aware LSM Engine (2020-05-31). Silme-farkında ve ayarlanabilir bir LSM motoru sunar; silme iş yükleri ile sıkıştırma etkileşimini ele alır. «alıntı yok: özet erişilemedi»
15. arXiv:2104.01305 — Nova-LSM: A Distributed, Component-based LSM-tree Key-value Store (2021-04-03). Bulut altyapısında monolitik depoları bileşenlere ayrıştıran dağıtık bir LSM deposudur ve paralel sıkıştırma içerir. «The cloud infrastructure motivates disaggregation of monolithic data stores into components that are assembled together based on an application's workload.»
16. doi:10.1145/3654927 — CaaS-LSM: Compaction-as-a-Service for LSM-based Key-Value Stores in Storage Disaggregated Infrastructure (2024-05-29). Depolama ayrıştırmalı altyapıda sıkıştırmayı hizmet olarak sunar ve depolama düğümlerine sıkıştırma boşaltma eğilimini ele alır. «Most of the existing studies focus on offloading the compaction to the storage nodes to mitigate the performance penalties caused by heavy network traffic between computing and storage.»
17. doi:10.1145/3538643.3539743 — Compaction-aware zone allocation for LSM based key-value store on ZNS SSDs (2022-06-27). ZNS SSD üzerinde sıkıştırma-farkında bölge tahsisi önerir ve yeni depolama aygıtlarına yönelik yüksek atıflı bir çalışmadır. «alıntı yok: özet erişilemedi»
18. doi:10.1109/icde48307.2020.00113 — FPGA-based Compaction Engine for Accelerating LSM-tree Key-Value Stores (2020-04). LSM anahtar-değer depolarını hızlandırmak için FPGA tabanlı bir sıkıştırma motoru önerir; donanım hızlandırma ailesini temsil eder. «alıntı yok: özet erişilemedi»
19. doi:10.1109/tpds.2022.3188268 — TriangleKV: Reducing Write Stalls and Write Amplification in LSM-Tree Based KV Stores With Triangle Container in NVM (2022-12-01). NVM'deki üçgen kapsayıcı ile LSM tabanlı KV depolarında yazma duraklamalarını ve yazma büyütmesini azaltır. «Reducing Write Stalls and Write Amplification in LSM-Tree Based KV Stores With Triangle Container in NVM.»
20. arXiv:2407.15581 — vLSM: Low tail latency and I/O amplification in LSM-based KV stores (2024-07-22). Sıkıştırma zincirleri kavramını tanıtır ve bunların kuyruk gecikmesini nasıl etkilediğini analiz eden güncel bir çalışmadır. «In this paper, we introduce the notion of compaction chains and we analyse how they affect tail latency.»
21. doi:10.14778/3611479.3611495 — WALTZ: Leveraging Zone Append to Tighten the Tail Latency of LSM Tree on ZNS SSD (2023-07). ZNS SSD'nin zone append özelliğiyle toplu grup yazmalarından kaynaklanan uzun kuyruk gecikmesi sorununu ele alır. «The long tail latency problem caused by the merging process of multiple parallel writes, called batch-group writes, is effectively addressed by the internal synchronization mechanism of ZNS SSD.»
22. doi:10.1109/icde55515.2023.00273 — The LSM Design Space and its Read Optimizations (2023-04). LSM tasarım uzayını ve okuma optimizasyonlarını inceler; sıkıştırma ile okuma performansı arasındaki etkileşime yöneliktir. «alıntı yok: özet erişilemedi»
23. doi:10.1145/3588726 — SplinterDB and Maplets: Improving the Tradeoffs in Key-Value Store Compaction Policy (2023-05-26). Agresif sıkıştırmanın alan ve sorgu kazancı ile ekleme verimi kaybı arasındaki ödünleşimi maplet tabanlı çözümle iyileştirir. «Aggressive compaction reduces the on-disk footprint of a key-value store and can improve query performance, but can reduce insertion throughput because it is I/O and CPU expensive.»
24. doi:10.1145/3588195.3592982 — Closing the Performance Gap between Leveling and Tiering Compaction via Bundle Compaction (2023-08-07). Bundle compaction ile leveling ve tiering sıkıştırma arasındaki performans boşluğunu kapatmayı hedefler. «alıntı yok: özet erişilemedi»
25. doi:10.14778/2757807.2757810 — Compaction management in distributed key-value datastores (2015-04). Dağıtık KV depolarında sıkıştırmanın, sıkıştırma süresince okuma performansını belirgin biçimde düşürdüğünü ele alır. «While compactions help keep read latencies in check over the long run, this comes at the cost of significantly degraded read performance over the course of the compaction itself.»
26. doi:10.1007/s00778-020-00638-1 — Comparison and evaluation of state-of-the-art LSM merge policies (2021-02-13). Ne zaman birleştirileceğini ve hangi SSTable'ların birleştirileceğini belirleyen güncel birleştirme politikalarını karşılaştırır ve değerlendirir. «A merge policy (a.k.a. compaction policy) specifies when to do merges and which SSTables to combine.»
27. doi:10.1109/ipdps.2014.85 — Pipelined Compaction for the LSM-Tree (2014-05). LSM-ağacı için boru hattı sıkıştırmasını önerir; sıkıştırma maliyetini ve duraklamaları azaltmaya yönelik erken bir tekniktir. «alıntı yok: özet erişilemedi»
28. doi:10.1016/j.aei.2023.102224 — Time-tired compaction: An elastic compaction scheme for LSM-tree based time-series database (2024-01). LSM tabanlı zaman serisi veritabanları için esnek bir sıkıştırma şeması önerir; özel iş yüklerini kapsar. «Time-tired compaction: An elastic compaction scheme for LSM-tree based time-series database.»
29. doi:10.1145/3662165.3662765 — KVBench: A Key-Value Benchmarking Suite (2024-06-09). Anahtar-değer depoları için güncel bir kıyaslama paketi sunar ve değerlendirme araçları alt sorusunu tamamlar. «alıntı yok: özet erişilemedi»
30. arXiv:1707.05354 — GPU LSM: A Dynamic Dictionary Data Structure for the GPU (2017-07-17). GPU üzerinde LSM tabanlı, hızlı ekleme ve silmeyi destekleyen dinamik sözlük yapısı geliştirir. «We develop a dynamic dictionary data structure for the GPU, supporting fast insertions and deletions, based on the Log Structured Merge tree (LSM).»
