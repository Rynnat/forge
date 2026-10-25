# Orkestra özeti
Soru: Veri ve yapay zeka ekosistemlerini yöneten LLM tabanlı veri ajanları (otonomi seviyeleri, sorgu ve veri analizi görevleri) üzerine en önemli çalışmalar ve açık problemler neler?
Kesim: 2025-09-27 | koşu: 20261025-175137-954e08
Durum: EKSİK (eksik: openalex, s2_zenginlestirme)
Maliyet (teorik, liste fiyatı): $0.652 | süre: 1151 s

## Funnel
- toplama:openalex: 0 → 0 (düşen: –)
- cozumleme:sef_capa: 25 → 24 (düşen: cozulemedi 1)
- toplama:crossref: 3500 → 3339 (düşen: tur_disi:peer-review 81, tur_disi:dataset 42, tur_disi:proceedings 9, tur_disi:component 9, basliksiz 20)
- toplama:dblp: 408 → 193 (düşen: kesim_sonrasi(yil) 215)
- toplama:arxiv: 3594 → 3594 (düşen: –)
- cozumleme:web: 163 → 121 (düşen: cozulemedi 25, tekrar_baslik 17)
- tekillestirme_1: 7271 → 5691 (düşen: birlesti 1580)
- kesim_1: 5691 → 5280 (düşen: tarih_belirsiz 411)
- toplama:atif: 918 → 393 (düşen: atif_yapan_kesim_sonrasi 201, tavan_kesimi 316, meta_yok 8)
- tekillestirme_2: 5673 → 5601 (düşen: birlesti 72)
- kesim_2: 5601 → 5570 (düşen: tarih_belirsiz 31)
- okuyucu_kesimi: 5570 → 1200 (düşen: on_siralama_kesimi 4370)
- okuyucu: 1200 → 1085 (düşen: kesin_alakasiz 115)
- damitma: 1085 → 80 (düşen: ilk_kart_disi 1005)
- sef_final: 80 → 30 (düşen: secilmedi 50)
Kaynaklar: sef_plan OK; openalex EKSİK [QuotaExhausted: Retry-After=32860s]; crossref OK; web OK; dblp OK; arxiv OK; s2_zenginlestirme EKSİK [s2: HTTP 429: 3 denemede 429]; atif OK; ozet_arxiv OK; sef_final OK

## 30 çalışma (önem sırasıyla)
1. arXiv:2412.14222 — A Survey on Large Language Model-based Agents for Statistics and Data Science (2024-12-18). LLM tabanlı veri bilimi ajanlarını 'data agents' olarak adlandırıp veri analizi paradigmasındaki dönüşümü kapsamlı biçimde derleyen merkezi… «In recent years, data science agents powered by Large Language Models…»
2. arXiv:2509.00997 — Supporting Our AI Overlords: Redesigning Data Systems to be Agent-First (2025-08-31). LLM ajanlarının veri sistemlerinde baskın iş yükü olacağını öngörüp veri sistemlerinin ajan-öncelikli yeniden tasarımını tartışıyor. «Large Language Model (LLM) agents, acting on their users' behalf to m…»
3. arXiv:2305.03111 — Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs (2023-05-04). BIRD, 95 veritabanı ve 12.751 örnekle büyük ölçekli, veritabanı değerlerine dayalı Text-to-SQL değerlendirmesi için temel benchmark. «we present Bird, a big benchmark for large-scale database grounded in…»
4. arXiv:1809.08887 — Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task (2018-09-24). Spider, 200 veritabanı ve 138 alanı kapsayan, alanlar arası Text-to-SQL için temel ve öncü insan etiketli veri seti. «It consists of 10,181 questions and 5,693 unique complex SQL queries…»
5. arXiv:2411.07763 — Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows (2024-11-12). Spider 2.0, kurumsal veritabanı kullanımından türetilmiş 632 gerçek Text-to-SQL iş akışı problemiyle ajan düzeyinde değerlendirme sunuyor. «We introduce Spider 2.0, an evaluation framework comprising 632 real-…»
6. arXiv:2407.11418 — Semantic Operators: A Declarative Model for Rich, AI-based Data Processing (2024-07-16). Doğal dil tanımlarına dayalı, bildirimsel ve genel amaçlı yapay zeka dönüşümleri için ilk biçimsel model olan semantik operatörleri tanıtıy… «We introduce semantic operators, the first formalism for declarative…»
7. arXiv:2402.18679 — Data Interpreter: An LLM Agent For Data Science (2024-02-28). Hiyerarşik graf modellemeyle karmaşık problemleri alt problemlere ayıran, uçtan uca veri bilimi iş akışları için LLM ajanı. «Our Data Interpreter incorporates two key modules: 1) Hierarchical Gr…»
8. arXiv:2410.07095 — MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering (2024-10-09). Kaggle kaynaklı görevlerle yapay zeka ajanlarının makine öğrenmesi mühendisliği performansını ölçen önemli bir benchmark. «We introduce MLE-bench, a benchmark for measuring how well AI agents…»
9. arXiv:2308.15363 — Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation (2023-08-29). LLM tabanlı Text-to-SQL için sistematik prompt mühendisliği benchmark'ı ve DAIL-SQL yöntemini sunarak etkin ve ekonomik tasarımı inceliyor. «Large language models (LLMs) have emerged as a new paradigm for Text-…»
10. arXiv:2304.11015 — DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction (2023-04-21). Ayrıştırılmış bağlam içi öğrenme ve öz-düzeltmeyle LLM'lerin Text-to-SQL doğruluğunu yaklaşık %10 artıran etkili bir yöntem. «Our experiments with three LLMs show that this approach consistently…»
11. arXiv:2312.11242 — MAC-SQL: A Multi-Agent Collaborative Framework for Text-to-SQL (2023-12-18). Ayrıştırıcı çekirdek ajan ve araç kullanan yardımcı ajanlarla çoklu ajan iş birliğine dayalı Text-to-SQL çerçevesi. «Our framework comprises a core decomposer agent for Text-to-SQL gener…»
12. arXiv:2405.16755 — CHESS: Contextual Harnessing for Efficient SQL Synthesis (2024-05-27). Şema budama ve birim testleri içeren, verimli ve ölçeklenebilir SQL sentezi için LLM tabanlı çoklu ajan çerçevesi. «We introduce CHESS, a Large Language Model (LLM) based multi-agent fr…»
13. arXiv:2410.01943 — CHASE-SQL: Multi-Path Reasoning and Preference Optimized Candidate Selection in Text-to-SQL (2024-10-02). Farklı LLM üreteçleriyle çok yollu akıl yürütme ve tercih optimizasyonlu aday seçimiyle güçlü bir Text-to-SQL yaklaşımı. «CHASE-SQL leverages LLMs' intrinsic knowledge to generate diverse and…»
14. arXiv:2402.17453 — DS-Agent: Automated Data Science by Empowering Large Language Models with Case-Based Reasoning (2024-02-27). Vaka tabanlı akıl yürütmeyle görev gereksinimlerini anlayıp uygun ML modelini kuran ve eğiten veri bilimi ajanı. «In this work, we investigate the potential of large language models (…»
15. arXiv:2409.07703 — DSBench: How Far Are Data Science Agents from Becoming Data Science Experts? (2024-09-12). 466 veri analizi ve 74 veri modelleme göreviyle veri bilimi ajanlarının uzman düzeyine uzaklığını ölçen benchmark. «This benchmark includes 466 data analysis tasks and 74 data modeling…»
16. arXiv:2312.01454 — D-Bot: Database Diagnosis System using Large Language Models (2023-12-03). Teşhis belgelerinden otomatik bilgi edinen LLM tabanlı veritabanı teşhis sistemi; veritabanı operasyonları için öncü ajan. «we propose D-Bot, an LLM-based database diagnosis system that can aut…»
17. arXiv:2311.03157 — GPTuner: A Manual-Reading Database Tuning System via GPT-Guided Bayesian Optimization (2023-11-06). Kılavuz okuyan, GPT yönlendirmeli Bayes optimizasyonuyla DBMS ayar parametrelerini belirleyen LLM tabanlı ayarlama sistemi. «Determining the appropriate values for these knobs to improve DBMS pe…»
18. arXiv:2403.09060 — GenRewrite: Query Rewriting via Large Language Models (2024-03-14). Geleneksel kuralların ötesinde sorgu yeniden yazımı için LLM'lerden yararlanan ilk bütünsel sistem olarak tanıtılıyor. «In this paper, we present GenRewrite, the first holistic system that…»
19. arXiv:2205.09911 — Can Foundation Models Wrangle Your Data? (2022-05-20). Beş veri temizleme ve entegrasyon görevini prompt görevlerine dönüştürerek temel modellerin veri düzenlemedeki yeteneğini değerlendiren önc… «we cast five data cleaning and integration tasks as prompting tasks a…»
20. arXiv:2312.01678 — Jellyfish: A Large Language Model for Data Preprocessing (2023-12-04). Ham veriyi temiz formata dönüştüren veri ön işleme için talimatla ince ayarlanmış LLM çalışması. «This paper explores the utilization of LLMs for data preprocessing (D…»
21. arXiv:2410.12189 — DocETL: Agentic Query Rewriting and Evaluation for Complex Document Processing (2024-10-16). Karmaşık belge işleme hatlarında maliyetin yanında doğruluğu iyileştirmek için ajan tabanlı sorgu yeniden yazımı ve değerlendirme sunuyor. «However, these frameworks focus on reducing cost when executing user-…»
22. arXiv:2407.10956 — Spider2-V: How Far Are Multimodal Agents From Automating Data Science and Engineering Workflows? (2024-07-15). Veri bilimi ve mühendislik iş akışlarını SQL, Python ve GUI işlemleriyle otomatikleştiren çok modlu ajanlar için benchmark. «VLM-based agents could potentially automate these workflows by genera…»
23. arXiv:2401.04398 — Chain-of-Table: Evolving Tables in the Reasoning Chain for Table Understanding (2024-01-09). Tablo verisini akıl yürütme zincirinde ara düşünceler olarak kullanarak tablo anlamayı geliştiren Chain-of-Table çerçevesi. «We propose the Chain-of-Table framework, where tabular data is explic…»
24. arXiv:2506.08800 — Measuring Data Science Automation: A Survey of Evaluation Tools for AI Assistants and Agents (2025-06-10). Veri bilimi ajanlarının değerlendirmesini derleyip ara insan-yapay zeka iş birliği otonomi seviyelerinin ihmal edildiğini açık problem olar… «a concentration on pure assistance or fully autonomous agents, withou…»
25. arXiv:2505.10468 — AI Agents vs. Agentic AI: A Conceptual Taxonomy, Applications and Challenges (2025-05-15). Yapay zeka ajanları ile ajan tabanlı yapay zekayı çoklu ajan iş birliği ve koordineli otonomi üzerinden ayıran kavramsal taksonomi. «We then characterize Agentic AI systems, which, in contrast to AI Age…»
26. arXiv:2408.05109 — A Survey of Text-to-SQL in the Era of LLMs: Where are we, and where are we going? (2024-08-09). LLM destekli Text-to-SQL tekniklerini tüm yaşam döngüsü boyunca kapsamlı biçimde derleyen ve gelecek yönleri tartışan anket. «In this survey, we provide a comprehensive review of Text-to-SQL tech…»
27. arXiv:2410.20424 — AutoKaggle: A Multi-Agent Framework for Autonomous Data Science Competitions (2024-10-27). Kod yürütme, hata ayıklama ve birim testiyle tablo verisi yarışmalarını otonom çözen çoklu ajan veri bilimi çerçevesi. «AutoKaggle implements an iterative development process that combines…»
28. arXiv:2409.00847 — The Design of an LLM-powered Unstructured Analytics System (2024-09-01). Doğal dil sorgularından semantik plan üretip büyük yapılandırılmamış belge koleksiyonlarında yürüten bildirimsel LLM analitik sistemi. «With Aryn, users specify queries in natural language and the system a…»
29. arXiv:2210.03629 — ReAct: Synergizing Reasoning and Acting in Language Models (2022-10-06). Akıl yürütme izleri ile eylemleri iç içe üreten ReAct, veri ajanlarının yeniden kullandığı temel ajan paradigmasıdır. «we explore the use of LLMs to generate both reasoning traces and task…»
30. arXiv:2503.16416 — Survey on Evaluation of LLM-based Agents (2025-03-20). LLM ajan değerlendirmesinde maliyet verimliliği, güvenlik ve sağlamlık gibi kritik açık boşlukları belirleyen derleme. «We also identify critical gaps that future research must address, par…»
