# Orkestra özeti
Soru: Bulut hizmetlerinde olay yönetimi için kök neden analizi (hata konumlandırma, nedensellik çıkarımı) yöntemleri üzerine en önemli çalışmalar ve açık problemler neler?
Kesim: 2025-09-22 | koşu: 20261026-053751-5636d5
Durum: EKSİK (eksik: openalex, dblp, arxiv, s2_zenginlestirme, ozet_arxiv)
Maliyet (teorik, liste fiyatı): $0.605 | süre: 1049 s

## Funnel
- toplama:openalex: 0 → 0 (düşen: –)
- toplama:crossref: 3500 → 3350 (düşen: tur_disi:proceedings 12, tur_disi:peer-review 35, tur_disi:component 3, tur_disi:dataset 86, basliksiz 14)
- toplama:dblp: 0 → 0 (düşen: –)
- cozumleme:sef_capa: 25 → 23 (düşen: cozulemedi 2)
- toplama:arxiv: 56 → 56 (düşen: –)
- cozumleme:web: 136 → 70 (düşen: cozulemedi 20, tekrar_baslik 46)
- tekillestirme_1: 3499 → 2350 (düşen: birlesti 1149)
- kesim_1: 2350 → 2248 (düşen: kesim_sonrasi 8, tarih_belirsiz 93, tarih_yok 1)
- toplama:atif: 825 → 538 (düşen: atif_yapan_kesim_sonrasi 124, tavan_kesimi 153, meta_yok 10)
- tekillestirme_2: 2786 → 2692 (düşen: birlesti 94)
- kesim_2: 2692 → 2674 (düşen: tarih_belirsiz 17, tarih_yok 1)
- okuyucu_kesimi: 2674 → 1200 (düşen: on_siralama_kesimi 1474)
- okuyucu: 1200 → 1034 (düşen: kesin_alakasiz 166)
- damitma: 1034 → 80 (düşen: ilk_kart_disi 954)
- sef_final: 80 → 30 (düşen: secilmedi 50)
Kaynaklar: sef_plan OK; openalex EKSİK [bütçe: günlük anahtarsız bütçe (80) doldu]; web OK; crossref OK; dblp EKSİK [tüm sorgular başarısız]; arxiv EKSİK [QuotaExhausted: 5 denemede 429]; s2_zenginlestirme EKSİK [s2: HTTP 429: 3 denemede 429]; atif OK; ozet_arxiv EKSİK [arXiv bu koşuda zaten tükendi: 5 denemede 429]; sef_final OK

## 30 çalışma (önem sırasıyla)
1. doi:10.1145/3627703.3629553 — Automatic Root Cause Analysis via Large Language Models for Cloud Incidents (2024-04-22). Bulut olayları için büyük dil modelleriyle otomatik kök neden analizi; kartlar arasında en çok atıf alan LLM tabanlı RCA çalışması. «alıntı yok: özet erişilemedi»
2. doi:10.1109/icse48619.2023.00149 — Recommending Root-Cause and Mitigation Steps for Cloud Incidents using Large Language Models (2023-05). Bulut olaylarında kök neden ve azaltma adımlarını büyük dil modelleriyle önermeye yönelik öncü çalışma. «alıntı yok: özet erişilemedi»
3. doi:10.1109/tse.2018.2887384 — Fault Analysis and Debugging of Microservice Systems: Industrial Survey, Benchmark System, and Empirical Study (2021-02-01). Mikroservis arıza analizi için endüstriyel anket, kıyaslama sistemi ve ampirik çalışmayı tek çalışmada birleştiriyor. «alıntı yok: özet erişilemedi»
4. doi:10.1145/3501297 — Anomaly Detection and Failure Root Cause Analysis in (Micro) Service-Based Cloud Applications: A Survey (2022-02-03). Çok servisli uygulamalarda anomali tespiti ve kök neden analizi tekniklerine yapılandırılmış genel bakış ve nitel analiz sunan derleme. «The objective of this survey is to provide a structured overview and qualitative analysis of currently available techniques for anomaly detection and root cause analysis in modern multi-service applications.»
5. doi:10.1109/noms47738.2020.9110353 — MicroRCA: Root Cause Localization of Performance Issues in Microservices (2020-04). Mikroservislerde performans sorunlarının kök neden konumlandırması için yüksek atıflı temel yöntem. «alıntı yok: özet erişilemedi»
6. arXiv:2206.05871 — Causal Inference-Based Root Cause Analysis for Online Service Systems with Intervention Recognition (2022-06-13). Bir izleme değişkeninin kök neden göstergesi olması için yeterli koşula dayanan, müdahale tanımalı nedensel çıkarım tabanlı RCA. «The core idea is a sufficient condition for a monitoring variable to be a root cause indicator»
7. doi:10.1145/3691620.3695065 — Root Cause Analysis for Microservice System based on Causal Inference: How Far Are We? (2024-10-27). Nedensel çıkarım tabanlı mikroservis kök neden analizi yöntemlerinin mevcut durumunu ampirik olarak değerlendiriyor. «alıntı yok: özet erişilemedi»
8. doi:10.1145/3701716.3715290 — RCAEval: A Benchmark for Root Cause Analysis of Microservice Systems with Telemetry Data (2025-05-08). Telemetri verisiyle mikroservis kök neden analizi için kıyaslama sistemi sunuyor. «alıntı yok: özet erişilemedi»
9. doi:10.1145/3627673.3680016 — RCAgent: Cloud Root Cause Analysis by Autonomous Agents with Tool-Augmented Large Language Models (2024-10-21). Araç destekli büyük dil modeli ajanlarıyla bulut kök neden analizi yapan otonom ajan yaklaşımı. «alıntı yok: özet erişilemedi»
10. arXiv:2403.04123 — Exploring LLM-based Agents for Root Cause Analysis (2024-03-07). Kök neden analizinde tanı bilgisini dinamik toplamak için LLM tabanlı ajanların kullanımını inceliyor. «In this work, we explore the use of LLM based agents for RCA to address this limitation.»
11. doi:10.1007/978-3-030-03596-9_1 — Microscope: Pinpoint Performance Issues with Causal Graphs in Micro-service Environments (2018-11-07). Mikroservis ortamlarında performans sorunlarını nedensel grafiklerle saptayan erken ve etkili yöntem. «alıntı yok: özet erişilemedi»
12. doi:10.1109/ccgrid.2018.00076 — CloudRanger: Root Cause Identification for Cloud Native Systems (2018-05). Bulut-yerel sistemlerde kök neden tanımlama için temel nedensellik grafiği tabanlı çalışma. «alıntı yok: özet erişilemedi»
13. doi:10.1109/infocom.2014.6848128 — CauseInfer: Automatic and distributed performance diagnosis with hierarchical causality graph in large distributed systems (2014-04). Büyük dağıtık sistemlerde hiyerarşik nedensellik grafiğiyle otomatik ve dağıtık performans teşhisi yapan klasik çalışma. «alıntı yok: özet erişilemedi»
14. doi:10.1145/3442381.3449905 — MicroRank: End-to-End Latency Issue Localization with Extended Spectrum Analysis in Microservice Environments (2021-04-19). Mikroservislerde uçtan uca gecikme sorunlarını genişletilmiş spektrum analiziyle konumlandırıyor. «alıntı yok: özet erişilemedi»
15. doi:10.1109/iwqos52092.2021.9521340 — Practical Root Cause Localization for Microservice Systems via Trace Analysis (2021-06-25). İz analizine dayalı pratik mikroservis kök neden konumlandırma yöntemi. «alıntı yok: özet erişilemedi»
16. doi:10.1109/icse48619.2023.00150 — Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data (2023-05). Çok kaynaklı veri üzerinde mikroservisler için uçtan uca sorun giderme çerçevesi. «alıntı yok: özet erişilemedi»
17. doi:10.1145/3611643.3616249 — Nezha: Interpretable Fine-Grained Root Causes Analysis for Microservices on Multi-modal Observability Data (2023-11-30). Çok modlu gözlemlenebilirlik verisiyle yorumlanabilir, ince taneli mikroservis kök neden analizi. «alıntı yok: özet erişilemedi»
18. arXiv:2108.00344 — Groot: An Event-graph-based Approach for Root Cause Analysis in Industrial Settings (2021-08-01). Metrik, log ve sistem etkinliklerini özetleyen olaylardan gerçek zamanlı nedensellik grafiği kuran endüstriyel RCA yaklaşımı. «Groot constructs a real-time causality graph based on events that summarize various types of metrics, logs, and activities in the system under analysis.»
19. doi:10.1145/3660805 — BARO: Robust Root Cause Analysis for Microservices via Multivariate Bayesian Online Change Point Detection (2024-07-12). Çok değişkenli Bayesçi çevrimiçi değişim noktası tespitini sağlam mikroservis kök neden analiziyle birleştiriyor. «BARO leverages the Multivariate Bayesian Online Change Point Detection technique to model the dependency within multivariate time-series metrics data»
20. doi:10.1109/iwqos49365.2020.9213058 — Localizing Failure Root Causes in a Microservice through Causality Inference (2020-06). Bir mikroserviste arıza kök nedenlerini nedensellik çıkarımıyla konumlandıran etkili çalışma. «alıntı yok: özet erişilemedi»
21. doi:10.1109/icse-seip52600.2021.00043 — MicroHECL: High-Efficient Root Cause Localization in Large-Scale Microservice Systems (2021-05). Büyük ölçekli mikroservis sistemlerinde yüksek verimli kök neden konumlandırma; ölçeklenebilirlik konusunu ele alıyor. «alıntı yok: özet erişilemedi»
22. doi:10.1145/3483424 — A Survey of AIOps Methods for Failure Management (2021-11-30). AIOps arıza yönetimi katkılarını 5 kategori ve 14 alt kategoride sınıflandıran derleme. «In this work, we focus on AIOps for Failure Management (FM), characterizing and describing 5 different categories and 14 subcategories of contributions»
23. doi:10.1145/3746635 — A Survey of AIOps in the Era of Large Language Models (2025-09-09). 2020-2024 arasındaki 183 makaleyi inceleyen, büyük dil modelleri çağında AIOps derlemesi. «We analyzed 183 research articles published between January 2020 and December 2024 to answer four key research questions (RQs).»
24. doi:10.1145/3696630.3728619 — AIOpsLab In Action: An Open Platform For AIOps Research (2025-06-23). AIOps araştırması ve olay giderme kıyaslaması için açık platform. «alıntı yok: özet erişilemedi»
25. doi:10.1109/issre.2019.00015 — Generic and Robust Localization of Multi-dimensional Root Causes (2019-10). Çok boyutlu kök nedenleri genel ve sağlam biçimde konumlandıran yöntem. «alıntı yok: özet erişilemedi»
26. doi:10.1145/3338906.3338961 — Latent error prediction and fault localization for microservice applications by learning from system trace logs (2019-08-12). Sistem iz günlüklerinden öğrenerek mikroservislerde gizli hata tahmini ve hata konumlandırma yapan yüksek atıflı çalışma. «Latent error prediction and fault localization for microservice applications by learning from system trace logs»
27. doi:10.1145/3701716.3715225 — Flow-of-Action: SOP Enhanced LLM-Based Multi-Agent System for Root Cause Analysis (2025-05-08). Standart işletim prosedürleriyle (SOP) güçlendirilmiş, LLM tabanlı çok ajanlı kök neden analizi sistemi. «alıntı yok: özet erişilemedi»
28. doi:10.1016/j.compchemeng.2023.108453 — Graph attention network with Granger causality map for fault detection and root cause diagnosis (2024-01). Granger nedensellik haritasını graf dikkat ağıyla birleştirerek arıza tespiti ve kök neden teşhisi yapıyor. «alıntı yok: özet erişilemedi»
29. doi:10.1145/3540250.3549092 — Actionable and interpretable fault localization for recurring failures in online service systems (2022-11-07). Çevrimiçi servis sistemlerinde tekrarlayan arızalar için eyleme dönük ve yorumlanabilir hata konumlandırma; açıklanabilirlik problemine katkı sağlıyor. «alıntı yok: özet erişilemedi»
30. doi:10.1145/3637528.3671530 — Microservice Root Cause Analysis With Limited Observability Through Intervention Recognition in the Latent Space (2024-08-24). Sınırlı gözlemlenebilirlik koşulunda gizli uzayda müdahale tanıma ile mikroservis kök neden analizi. «alıntı yok: özet erişilemedi»
