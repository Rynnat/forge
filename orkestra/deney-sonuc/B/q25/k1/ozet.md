# Orkestra özeti
Soru: Büyük dil modellerinin eğitim verisinde belirli bir metnin yer alıp almadığını tespit etme (üyelik çıkarımı) ve test verisi kirlenmesi üzerine en önemli çalışmalar, güvenlik sonuçları ve açık problemler neler?
Kesim: 2026-04-21 | koşu: 20261026-045243-96b4f1
Durum: EKSİK (eksik: openalex, arxiv, s2_zenginlestirme, ozet_arxiv)
Maliyet (teorik, liste fiyatı): $0.630 | süre: 1552 s

## Funnel
- toplama:openalex: 0 → 0 (düşen: –)
- cozumleme:sef_capa: 25 → 23 (düşen: cozulemedi 2)
- toplama:crossref: 4000 → 3788 (düşen: tur_disi:peer-review 151, tur_disi:component 5, tur_disi:dataset 25, basliksiz 23, tur_disi:proceedings 7, tur_disi:report-series 1)
- cozumleme:web: 149 → 92 (düşen: cozulemedi 5, tekrar_baslik 52)
- toplama:dblp: 641 → 641 (düşen: –)
- toplama:arxiv: 4553 → 4553 (düşen: –)
- tekillestirme_1: 9097 → 5884 (düşen: birlesti 3213)
- kesim_1: 5884 → 5415 (düşen: tarih_belirsiz 469)
- toplama:atif: 1035 → 393 (düşen: tavan_kesimi 628, meta_yok 14)
- tekillestirme_2: 5808 → 5697 (düşen: birlesti 111)
- kesim_2: 5697 → 5689 (düşen: tarih_belirsiz 7, tarih_yok 1)
- okuyucu_kesimi: 5689 → 1200 (düşen: on_siralama_kesimi 4489)
- okuyucu: 1200 → 882 (düşen: kesin_alakasiz 318)
- damitma: 882 → 80 (düşen: ilk_kart_disi 802)
- sef_final: 80 → 30 (düşen: secilmedi 50)
Kaynaklar: sef_plan OK; openalex EKSİK [bütçe: günlük anahtarsız bütçe (80) doldu]; web OK; crossref OK; dblp OK; arxiv EKSİK [QuotaExhausted: 5 denemede 429]; s2_zenginlestirme EKSİK [s2: HTTP 429: 3 denemede 429]; atif OK; ozet_arxiv EKSİK [arXiv bu koşuda zaten tükendi: 5 denemede 429]; sef_final OK

## 30 çalışma (önem sırasıyla)
1. arXiv:1610.05820 — Membership Inference Attacks against Machine Learning Models (2016-10-18). Shokri vd.'nin klasik çalışması, kara kutu erişimle bir kaydın eğitim verisinde olup olmadığını belirleyen gölge model tabanlı üyelik çıkar… «given a data record and black-box access to a model, determine if the…»
2. arXiv:2112.03570 — Membership Inference Attacks From First Principles (2021-12-07). LiRA'yı tanıtan temel çalışma, saldırıların düşük yanlış pozitif oranlarında gerçek pozitif oranıyla değerlendirilmesi gerektiğini savunur. «We argue that attacks should instead be evaluated by computing their…»
3. arXiv:2310.16789 — Detecting Pretraining Data from Large Language Models (2023-10-25). Ön-eğitim verisi tespiti için Min-K% Prob ailesini ve model eğitimi öncesi ve sonrası verilerle kurulan dinamik WikiMIA benchmark'ını sunar. «we introduce a dynamic benchmark WIKIMIA that uses data created befor…»
4. arXiv:2402.07841 — Do Membership Inference Attacks Work on Large Language Models? (2024-02-12). Pile üzerinde, çoğu ortamda üyelik çıkarımı saldırılarının rastgele tahminden zar zor daha iyi olduğunu göstererek alanın güvenilirlik tart… «We find that MIAs barely outperform random guessing for most settings…»
5. arXiv:2012.07805 — Extracting Training Data from Large Language Models (2020-12-14). Dil modelini sorgulayarak tek tek eğitim örneklerinin geri elde edilebildiğini gösterir; ezberleme ve gizlilik riskleri için temel çalışmad… «This paper demonstrates that in such settings, an adversary can perfo…»
6. arXiv:2202.07646 — Quantifying Memorization Across Neural Language Models (2022-02-15). Ezberlemenin model kapasitesi ve örnek tekrarı arttıkça belirgin biçimde büyüdüğünü nicel olarak ortaya koyar. «Memorization significantly grows as we increase (1) the capacity of a…»
7. arXiv:2404.02936 — Min-K%++: Improved Baseline for Detecting Pre-Training Data from Large Language Models (2024-04-03). Min-K%++, eğitim örneklerinin modellenen dağılımın yerel maksimumları olma eğilimine dayanan teorik temelli bir tespit yöntemi sunar. «we present a key insight that training samples tend to be local maxim…»
8. arXiv:2305.18462 — Membership Inference Attacks against Language Models via Neighbourhood Comparison (2023-05-29). Komşuluk karşılaştırma saldırısı, örneğin içsel karmaşıklığını hesaba katarak tek başına skor eşiklemenin yol açtığı yüksek yanlış pozitifl… «simple thresholding of the model score in isolation tends to lead to…»
9. arXiv:2406.06443 — LLM Dataset Inference: Did you train on my dataset? (2024-06-10). Dağılım kayması nedeniyle üyelik çıkarımı başarısının abartıldığını eleştirir ve veri kümesi düzeyinde çıkarım yaklaşımını önerir.
10. arXiv:2406.16201 — Blind Baselines Beat Membership Inference Attacks for Foundation Models (2024-06-23). Sekiz yayımlanmış veri kümesinde modele bakmayan kör saldırıların en güçlü üyelik çıkarımı saldırılarını geçtiğini göstererek değerlendirme… «For 8 published MI evaluation datasets, we show that blind attacks --…»
11. arXiv:2406.17975 — SoK: Membership Inference Attacks on LLMs are Rushing Nowhere (and How to Fix It) (2024-06-25). LLM üyelik çıkarımı literatürünü sistematik olarak inceler ve sonradan toplanan veri kümelerine dayanan değerlendirmeleri metodolojik açıda… «Contrary to traditional MIAs which rely on fixed-but randomized-recor…»
12. arXiv:2310.17623 — Proving Test Set Contamination in Black Box Language Models (2023-10-26). Ön-eğitim verisine veya model ağırlıklarına erişim olmadan test kümesi kirlenmesi için kanıtlanabilir garantiler sunar. «We show that it is possible to provide provable guarantees of test se…»
13. arXiv:2308.08493 — Time Travel in LLMs: Tracing Data Contamination in Large Language Models (2023-08-16). Kirlenmeyi önce örnek düzeyinde tespit eder, ardından bu bilgiyle bölüm düzeyinde değerlendiren etkili bir yöntem önerir. «At its core, our approach starts by identifying potential contaminati…»
14. arXiv:2402.09910 — DE-COP: Detecting Copyrighted Content in Language Models Training Data (2024-02-15). DE-COP, birebir metin ve parafrazları içeren çoktan seçmeli sorularla telifli içeriğin eğitim verisinde bulunup bulunmadığını tespit eder. «DE-COP's core approach is to probe an LLM with multiple-choice questi…»
15. arXiv:2311.04850 — Rethinking Benchmark and Contamination for Language Models with Rephrased Samples (2023-11-08). Parafraz ve çeviri gibi basit varyasyonların mevcut kirlilik temizleme önlemlerini kolayca aşabildiğini gösterir. «we show that these methods are insufficient, and simple variations of…»
16. arXiv:1802.08232 — The Secret Sharer: Evaluating and Testing Unintended Memorization in Neural Networks (2018-02-22). Secret Sharer, nadir veya benzersiz eğitim dizilerinin istemeden ezberlenme riskini nicel olarak test eden bir metodoloji sunar. «This paper describes a testing methodology for quantitatively assessi…»
17. arXiv:2311.17035 — Scalable Extraction of Training Data from (Production) Language Models (2023-11-28). Hizalanmış ChatGPT dahil üretim modellerinden ölçeklenebilir eğitim verisi çıkarımı için yeni bir sapma saldırısı geliştirir. «Existing techniques from the literature suffice to attack unaligned m…»
18. arXiv:2111.09679 — Enhanced Membership Inference Attacks against Machine Learning Models (2021-11-18). Referans model kullanan üyelik çıkarımı saldırıları için hipotez testi çerçevesi kurarak her yanlış pozitif oranında daha yüksek güç elde e… «that use reference models to achieve a significantly higher power (tr…»
19. arXiv:1709.01604 — Privacy Risk in Machine Learning: Analyzing the Connection to Overfitting (2017-09-05). Aşırı öğrenme ve etkinin, saldırganın eğitim verisi hakkında bilgi edinme yeteneği üzerindeki etkisini inceleyen klasik çalışmadır. «This paper examines the effect that overfitting and influence have on…»
20. arXiv:2310.18018 — NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark (2023-10-27). Bir benchmark'ın test bölümünde eğitilip aynı benchmark'ta değerlendirilmenin en kötü kirlenme türü olduğunu vurgular ve benchmark başına ö… «The worst kind of data contamination happens when a Large Language Mo…»
21. arXiv:2405.00332 — A Careful Examination of Large Language Model Performance on Grade School Arithmetic (2024-05-01). Yeni GSM1k benchmark'ında %8'e varan doğruluk düşüşleri bularak birçok model ailesinde sistematik aşırı uyum kanıtı sunar. «When evaluating leading open- and closed-source LLMs on GSM1k, we obs…»
22. arXiv:2406.19314 — LiveBench: A Challenging, Contamination-Limited LLM Benchmark (2024-06-27). Test kümesi kirlenmesini adil değerlendirmenin önünde bir engel olarak ele alır ve kirlenmesi sınırlı, dinamik bir benchmark önerir. «Test set contamination, wherein test data from a benchmark ends up in…»
23. arXiv:2403.07974 — LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code (2024-03-12). LiveCodeBench, zaman içinde sürekli yeni problemler toplayarak kod modelleri için kirlenmesiz değerlendirme sağlar. «we propose LiveCodeBench, a comprehensive and contamination-free eval…»
24. arXiv:2402.10892 — Proving membership in LLM pretraining data via data watermarks (2024-02-16). Veri filigranları sayesinde yalnızca kara kutu erişimiyle ön-eğitim üyeliğinin ilkeli biçimde tespit edilmesini önerir. «This work proposes using data watermarks to enable principled detecti…»
25. arXiv:2402.09363 — Copyright Traps for Large Language Models (2024-02-14). Özgün içeriğe kurgusal girdiler ekleyen telif tuzaklarıyla telifli materyalin LLM'lerde kullanımının tespit edilmesini önerir. «We here propose to use copyright traps, the inclusion of fictitious e…»
26. arXiv:2406.19234 — Generating Is Believing: Membership Inference Attacks against Retrieval-Augmented Generation (2024-06-27). Harici veritabanındaki örneklerin üretilen metinle anlamsal benzerliğine dayanarak RAG sistemlerine yönelik üyelik çıkarımını ortaya koyar. «Our basic idea is that if a sample is in the external database, it wi…»
27. arXiv:2210.17546 — Preventing Generation of Verbatim Memorization in Language Models Gives a False Sense of Privacy (2022-10-31). Birebir ezberin üretimini engellemenin yanıltıcı bir gizlilik güvencesi verdiğini göstererek savunmaların sınırlarına dikkat çeker.
28. arXiv:2410.18966 — Does Data Contamination Detection Work (Well) for LLMs? A Survey and Evaluation on Detection Assumptions (2024-10-24). Kirlenme tespiti yöntemlerinin varsayımlarını inceler ve örnek düzeyinde kirlenme tespitini üyelik çıkarımı saldırılarıyla ilişkilendirir. «Our case studies focus on detecting direct, instance-level data conta…»
29. arXiv:2411.00154 — Scaling Up Membership Inference: When and How Attacks Succeed on Large Language Models (2024-10-31). Üyelik çıkarımının LLM'lerde ancak test için birden fazla belge sunulduğunda işe yaradığını savunarak ölçek boyutunu netleştirir. «we argue that MIA still works on LLMs, but only when multiple documen…»
30. arXiv:2407.06460 — MUSE: Machine Unlearning Six-Way Evaluation for Language Models (2024-07-08). MUSE, altı farklı istenen özelliği sıralayarak dil modelleri için kapsamlı bir unlearning değerlendirme benchmark'ı sunar. «We address this issue by proposing MUSE, a comprehensive machine unle…»
