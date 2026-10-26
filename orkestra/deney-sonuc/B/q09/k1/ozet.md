# Orkestra özeti
Soru: SMT tabanlı sınırlı model denetimi ile C/C++ yazılımının biçimsel doğrulanması ve bu alandaki araçların gelişimi üzerine en önemli çalışmalar ve açık problemler neler?
Kesim: 2026-04-25 | koşu: 20261025-215432-289906
Durum: EKSİK (eksik: openalex, s2_zenginlestirme)
Maliyet (teorik, liste fiyatı): $0.528 | süre: 1151 s

## Funnel
- toplama:openalex: 0 → 0 (düşen: –)
- cozumleme:sef_capa: 23 → 17 (düşen: cozulemedi 6)
- toplama:crossref: 3500 → 3404 (düşen: tur_disi:dataset 20, tur_disi:proceedings 8, tur_disi:peer-review 42, basliksiz 26)
- cozumleme:web: 33 → 26 (düşen: cozulemedi 6, tekrar_baslik 1)
- toplama:dblp: 458 → 458 (düşen: –)
- toplama:arxiv: 3989 → 3989 (düşen: –)
- tekillestirme_1: 7894 → 5620 (düşen: birlesti 2274)
- kesim_1: 5620 → 5524 (düşen: tarih_belirsiz 96)
- toplama:atif: 6144 → 492 (düşen: tavan_kesimi 5639, meta_yok 13)
- tekillestirme_2: 6016 → 5891 (düşen: birlesti 125)
- kesim_2: 5891 → 5888 (düşen: tarih_yok 3)
- okuyucu_kesimi: 5888 → 1200 (düşen: on_siralama_kesimi 4688)
- okuyucu: 1200 → 1077 (düşen: kesin_alakasiz 123)
- damitma: 1077 → 80 (düşen: ilk_kart_disi 997)
- sef_final: 80 → 30 (düşen: secilmedi 50)
Kaynaklar: sef_plan OK; openalex EKSİK [QuotaExhausted: Retry-After=18298s]; web OK; crossref OK; dblp OK; arxiv OK; s2_zenginlestirme EKSİK [s2: HTTP 429: 3 denemede 429]; atif OK; ozet_arxiv OK; sef_final OK

## 30 çalışma (önem sırasıyla)
1. doi:10.1007/3-540-49059-0_14 — Symbolic Model Checking without BDDs (1999-01-04). BDD'siz sembolik model denetimini tanıtan, SAT tabanlı sınırlı model denetiminin temel makalesi; BMC temellerini kurar. «alıntı yok: özet erişilemedi»
2. doi:10.1007/s10009-008-0091-0 — Bounded Model Checking of Software Using SMT Solvers Instead of SAT Solvers (2006). BMC'de SAT çözücüler yerine SMT çözücülerin kullanımını ele alan temel çalışma; SAT'tan SMT'ye geçişi temsil eder. «alıntı yok: özet erişilemedi»
3. doi:10.1007/978-3-540-24730-2_15 — A Tool for Checking ANSI-C Programs (2004). ANSI-C programlarını denetleyen CBMC aracının özgün tanıtım makalesi; C için BMC araçlarının başlangıç noktası. «alıntı yok: özet erişilemedi»
4. arXiv:0907.2072 — SMT-Based Bounded Model Checking for Embedded ANSI-C Software (2009-07-12). Gömülü ANSI-C için SMT tabanlı BMC; bit-vektör, dizi, yapı, birlik ve işaretçiler için daha doğru kodlamalar sunar. «We have extended the encodings from previous SMT-based bounded model checkers to provide more accurate support for finite variables, bit-vector operations, arrays, structures, unions and pointers.»
5. arXiv:2302.02384 — CBMC: The C Bounded Model Checker (2014). CBMC'nin, döngüleri belirli derinliğe açılmış C programlarını formüle bit-hassas çevirisini açıklayan temel araç tanıtımı. «CBMC implements a bit-precise translation of an input C program, annotated with assertions and with loops unrolled to a given depth, into a formula.»
6. doi:10.3233/978-1-58603-929-5-457 — Bounded Model Checking (2003). BMC temellerini ve k-tümevarım ile interpolasyon gibi tam uzantıları kapsamlı biçimde tartışan bölüm. «In addition, a considerable part of this chapter discusses complete extensions, including k-induction and interpolation.»
7. doi:10.1007/978-3-540-78800-3_24 — Z3: An Efficient SMT Solver (2008). BMC araçlarında yaygın kullanılan temel SMT çözücü Z3'ü tanıtır. «alıntı yok: özet erişilemedi»
8. doi:10.1007/978-3-642-27705-4_12 — LLBMC: Bounded Model Checking of C and C++ Programs Using a Compiler IR (2012). Derleyici ara temsili kullanarak C ve C++ programlarını sınırlı model denetimiyle doğrulayan LLBMC aracı. «alıntı yok: özet erişilemedi»
9. doi:10.1145/3238147.3240481 — ESBMC 5.0: an industrial-strength C model checker (2018-09-03). Endüstriyel güçte C model denetleyicisi olarak sunulan ESBMC 5.0; başlıca SMT tabanlı BMC aracı. «alıntı yok: özet erişilemedi»
10. arXiv:2107.01093 — Model Checking C++ Programs (2021-07-02). C++ programlarını BMC ve SMT ile biçimsel olarak doğrulayan yeni bir yaklaşımı tanımlar ve değerlendirir. «Here we describe and evaluate a novel verification approach based on bounded model checking (BMC) and satisfiability modulo theories (SMT) to verify C++ programs formally.»
11. doi:10.1145/1985793.1985839 — Verifying multi-threaded software using smt-based context-bounded model checking (2011-05-21). Çok iş parçacıklı yazılımı SMT tabanlı bağlam sınırlı model denetimiyle doğrulama; eşzamanlılık için temel çalışma. «alıntı yok: özet erişilemedi»
12. doi:10.1007/978-3-540-31980-1_7 — Context-Bounded Model Checking of Concurrent Software (2005). Eşzamanlı yazılım için bağlam sınırlı model denetimini tanıtan çalışma; eşzamanlılık doğrulamasının temeli. «alıntı yok: özet erişilemedi»
13. doi:10.1007/978-3-319-08867-9_39 — Bounded Model Checking of Multi-threaded C Programs via Lazy Sequentialization (2014). Çok iş parçacıklı C programlarının tembel sıralama (lazy sequentialization) ile sınırlı model denetimi. «alıntı yok: özet erişilemedi»
14. doi:10.1007/978-3-642-39799-8_9 — Partial Orders for Efficient Bounded Model Checking of Concurrent Software (2013). Eşzamanlı yazılımın verimli BMC'si için kısmi sıra yaklaşımı; eşzamanlılık doğrulamasında önemli yöntem. «alıntı yok: özet erişilemedi»
15. doi:10.1007/978-3-642-23702-7_26 — Software Verification Using k-Induction (2011). k-tümevarım ile yazılım doğrulaması; BMC'yi sınırsız doğrulamaya genişleten yöntem ailesi. «alıntı yok: özet erişilemedi»
16. doi:10.1007/s10009-015-0407-9 — Handling loops in bounded model checking of C programs via k-induction (2015-11-23). C programlarındaki döngüleri k-tümevarım yoluyla ele alarak BMC'yi sınırsız doğrulamaya taşır. «alıntı yok: özet erişilemedi»
17. arXiv:1502.00096 — Combining k-Induction with Continuously-Refined Invariants (2015-01-31). BMC'yi hata bulmadan doğrulamaya genişleten k-tümevarımı sürekli iyileştirilen değişmezlerle birleştirir. «Bounded model checking (BMC) is a well-known and successful technique for finding bugs in software. k-induction is an approach to extend BMC-based approaches from falsification to verification.»
18. doi:10.1007/978-3-642-00768-2_16 — Boolector: An Efficient SMT Solver for Bit-Vectors and Arrays (2009). Bit-vektör ve dizi teorileri için verimli SMT çözücü Boolector; BMC performansını etkileyen teori çözümü. «alıntı yok: özet erişilemedi»
19. doi:10.1007/978-3-031-37703-7_1 — Bitwuzla (2023-07-18). Bit-vektör, dizi ve kayan nokta aritmetiği teorilerini destekleyen yeni SMT çözücü Bitwuzla. «Bitwuzla is a new SMT solver for the quantifier-free and quantified theories of fixed-size bit-vectors, arrays, floating-point arithmetic, and uninterpreted functions.»
20. doi:10.1007/978-3-030-99524-9_24 — cvc5: A Versatile and Industrial-Strength SMT Solver (2022-03-30). CVC4 kod tabanı üzerine kurulu, çok yönlü ve endüstriyel güçte SMT çözücü cvc5. «cvc5 is the latest SMT solver in the cooperating validity checker series and builds on the successful code base of CVC4»
21. arXiv:2004.12699 — An Efficient Floating-Point Bit-Blasting API for Verifying C Programs (2020-04-27). ESBMC'nin SMT arka ucunda C programlarını doğrulamak için verimli kayan nokta bit-blasting API'si. «The new floating-point API is part of the SMT backend in ESBMC, a state-of-the-art bounded model checker for C and C++.»
22. arXiv:2406.04696 — PolySAT: Word-level Bit-vector Reasoning in Z3 (2024-06-07). Z3'te kelime düzeyi bit-vektör çözümü; çarpma/bölmede bit-blasting ölçeklenmediğinde model denetimine potansiyel katkı. «PolySAT is integrated into the SMT solver Z3 and has potential applications in model checking and smart contract verification where bit-blasting techniques on multipliers/divisions do not scale.»
23. doi:10.1007/978-3-642-28756-5_38 — Competition on Software Verification (2012). Doğrulama araçlarını karşılaştırma çerçevesi olan SV-COMP yarışmasının tanımı. «Competition on Software Verification»
24. doi:10.1007/978-3-032-22749-2_23 — Evaluating Software Verifiers for C, Java, and SV-LIB (2026-04-15). 36 402 C doğrulama görevi ve SV-LIB ile en güncel SV-COMP karşılaştırmalı değerlendirmesi. «The verification track of the competition was executed on a benchmark set of 36 402 verification tasks with C programs»
25. doi:10.1007/978-3-031-90660-2_9 — Improvements in Software Verification and Witness Validation: SV-COMP 2025 (2025-05-01). 33 353 C doğrulama görevli SV-COMP 2025; büyük ölçekli kıyaslama ve tanık doğrulama. «The verification track of the competition was executed on a benchmark set of 33 353 verification tasks with C programs»
26. doi:10.1007/s10009-017-0469-y — Reliable benchmarking: requirements and solutions (2017-11-03). Araç ve algoritmaların karşılaştırmalı değerlendirmesi için güvenilir kıyaslama gereksinimleri ve çözümleri. «Benchmarking is a widely used method in experimental computer science, in particular, for the comparative evaluation of tools and algorithms.»
27. doi:10.1007/s10703-020-00344-2 — Model checking boot code from AWS data centers (2020-04-15). Amazon Web Services veri merkezlerindeki ilk önyükleme kodunun bellek güvenliğinin kanıtlanması; endüstriyel uygulama örneği. «We have proved that the initial boot code running in data centers at Amazon Web Services is memory safe, an essential step in establishing the security of any data center.»
28. doi:10.1007/s00165-017-0419-1 — Incremental bounded model checking for embedded software (2017-09). Gömülü yazılım için artımlı BMC; endüstriyel araçların yinelemeli açma kullanımını ele alır. «Existing industrial tools for embedded software use an off-the-shelf bounded model checker and apply it iteratively to verify the program with an increasing number of unwindings.»
29. arXiv:2012.11223 — FuSeBMC: A White-Box Fuzzer for Finding Security Vulnerabilities in C Programs (2020-12-21). Fuzzing ve sembolik yürütmeyi birleştirip BMC uygulayarak C programlarında güvenlik açıkları bulan FuSeBMC. «We describe and evaluate a novel white-box fuzzer for C programs named FuSeBMC, which combines fuzzing and symbolic execution, and applies Bounded Model Checking (BMC) to find security vulnerabilities in C programs.»
30. arXiv:2305.14752 — A New Era in Software Security: Towards Self-Healing Software via Large Language Models and Formal Verification (2023-05-24). ESBMC ve önceden eğitilmiş transformer modelini birleştiren ESBMC-AI ile LLM ve biçimsel doğrulama ile kendi kendini onaran yazılım. «We present the ESBMC-AI framework as a proof of concept, leveraging the well-recognized and industry-adopted Efficient SMT-based Context-Bounded Model Checker (ESBMC) and a pre-trained transformer model»
