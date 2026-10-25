# maliyet-sayaci kabul testi (2026-10-25)

Denetci: Sonnet 5.5 (aracin yazari Opus; bkz. Belirsizlikler 1).
Esikler `ONKAYIT-maliyet-sayaci.md`'den (git 74e36a9, 14:10 +03) aynen alindi; degistirilmedi. Aracin kodu ve KAYIT.md'ye dokunulmadi. Transkriptler salt okundu.
Dogrulama kodu aracin ayristiricisini KULLANMAZ (yalniz json/stdlib); arac yalnizca `--json` cikti kaynagi olarak calistirildi.

## Onkosullar
- ONKAYIT commit'i (74e36a9, 14:10:58) kod degisikliginden (3e2876f, 14:15:34) once. OK.
- Degisecek 4 sey mevcut: `son-bgl+cik` sutunu / `son_baglam_cikti` (agents), `etiketler.csv`, `ozet --hafta`, hakem regresyon testi (`tests/test_maliyet.py`). `pytest`: 27 test, 27 gecti.
- Not: 3e2876f'den sonra arac bir daha degisti (aacb434 WIP, 15:46: orkestra log okuma, yeni ajan etiketleri). Esikler degismedi; asagidaki testler guncel kodla kosuldu.

## Kriter 1: Ana test (gorulmemis ajanlar) -> GECTI
- Resmi referans: ana oturum transkriptindeki `<subagent_tokens>` (task-notification, `queue-operation`); bir ajan icin birden fazla bildirim varsa EN SON bildirim (ajan yeniden uyandirilmis olabilir).
- Kapsam: ilk zaman damgasi >= 2026-10-25T10:00:00Z olan ve bildirimi olan ajanlar. 11 aday cikti; `af755726` hakem anlik goruntusunde (agents.json, 19 ajan) zaten vardi (10:00:48'de basladi, hakem son 10:01:28'e kadar gordu) -> "hakem raporundan sonra olusmus" degil, DISARI. Kalan **n = 10** (ONKAYIT n>=10 saglandi, sinirda). 11'i de dahil etsek sonuc ayni.
- Olculen: aracin `son_baglam_cikti` degeri vs resmi sayi; ayrica bagimsiz betigin kendi son-cagri toplami.

| ajan | oturum | resmi | arac | bagimsiz | sapma (arac) |
|---|---|---|---|---|---|
| a1272bcf | 76053f18 | 136394 | 135586 | 135586 | -%0,592 |
| a541b52f | 76053f18 | 102975 | 102975 | 102975 | %0 |
| a562d68d | ec53bc40 | 119127 | 119127 | 119127 | %0 |
| a69bc967 | 76053f18 | 94126 | 94126 | 94126 | %0 |
| a83ad971 | 76053f18 | 126261 | 126261 | 126261 | %0 |
| a8b18801 | 76053f18 | 151624 (23 bildirimin sonuncusu) | 151624 | 151624 | %0 |
| a8f4da68 | 76053f18 | 157519 | 157519 | 157519 | %0 |
| abdc8fd5 | 76053f18 | 145402 | 145402 | 145402 | %0 |
| ace5b9fe | ec53bc40 | 152375 | 152375 | 152375 | %0 |
| af77a02f | 76053f18 | 265247 | 265247 | 265247 | %0 |

Olculen: 10/10 ajan <= %2; en buyuk |sapma| %0,592 (a1272bcf; resmi sayi arac+bagimsiz hesaptan 808 token buyuk, yani bizim son-cagri secimimizde bir fark var, ama esigin cok icinde). Esik: <= %2 ve 10/10. -> **GECTI**.
Kanit: `kabul/bagimsiz_dogrulama.py ana` (aday + resmi sayi + bagimsiz hesap), `kabul/ana_test.py <ana.json>` (arac `agents --json` ile karsilastirma).
Not: bu denetim ajani (243dc754/a7d171b2) kendisi henuz bildirimsiz oldugundan kapsam disi.

## Kriter 2: Regresyon (hakemin 19 ajani, toplam token) -> GECTI
- Referans: `scratchpad\hakem\agents.json` (hakemin 19 ajani: ana + 18; toplam = input+output+cache yazma+cache okuma).
- Transkriptler hakem sonrasi buyudugu icin (ana 71 -> 199 mesaj) canli veriyle birebir karsilastirma anlamsiz; bu yuzden transkriptler hakem goruntusunun sonuna (2026-10-25T10:01:28.951Z) KESILMIS bir kopyada araç calistirildi (kopya scratchpad'de; orijinale yazilmadi).
- Sonuc (kesik kopya): hakem 92.522.125, arac 92.522.125, bagimsiz sayim 92.522.125 -> sapma **%0,000**; 19/19 ajanda mesaj sayisi ve token birebir ayni. Esik <= %0,5 -> **GECTI**.
- Bilgi: kesilmemis canli veride arac toplami 142,8M (+%54,4); sebep yalnizca transkriptlerin buyumesi (ayni bagimsiz sayim da 142.818.383), arac hatasi degil. Bu okuma ("canli veri = hakem sayisi") kullanilsa olcut anlamsiz olurdu; Belirsizlikler maddesi 2.
- Kanit: `kabul/regresyon_hakem19.py <gecici_dizin>`.

## Kriter 3: Etiket katmani, eslenmemis pay -> GECTI (kosullu, asagidaki uyari ile)
- `ozet --hafta` (son 7 gun, 18-25 Eki): etiketsiz pay token %1,8, $ %1,8 (esik <= %10; baslangic %35). Bagimsiz hesap (`kabul/etiket_testi.py`, ayni csv kurallariyla, kendi tekillestirmem): %1,89 token. Arac 827,8M token / $494,58; bagimsiz 828,1M (fark: iki kosu arasinda gecen dakikalarda oturumun buyumesi).
- Etiketsiz kalan: bugunku oturumlar (243dc754 %1,40, 240437be, 5327f133, 793908b7, db3f004b, 85b7e906, 42adf03c).
- UYARI (esigi gecirmeyi/gecirmemeyi degistirmez ama KABUL'un anlamini sinirlar): metrik yalnizca "eslenmemis pay"; etiketler.csv'de 49 oturum icerigi okunmadan `diger` yazilmis, `diger` toplamin %82,3'u. Yani pay "eslenmis" ama bilgi tasimiyor; arastirma/forge-meta ayrimi yalnizca 76053f18 icinde var. ONKAYIT yalniz eslenmemis payi olcuyor, bu yuzden GECTI; ancak KAYIT'ta "K2 ölçülebilir" demek icin bu `diger` cop kutusu notu dusulmeli.
- Ayrica: yeni olusan her oturum etiketsiz baslar; pay zamanla yukselebilir. Oldurme kosulu (3 hafta ust uste > %30) henuz tetiklenmedi (ilk hafta).

## Oldurme kosullari
- Gorulmemis ajanlarda tek sapma > %2: yok (maks %0,592).
- Etiket katmani 3 hafta ust uste > %30: tetiklenmedi (ilk hafta %1,8).

## Belirsizlikler / kararlar (sessizce yorumlanmadi)
1. "Denetci: kodu yazandan farkli model ailesi": yazar Opus, denetci Sonnet; ayni vendor, farkli model. ONKAYIT'in "aile" ifadesi kati okunursa (Opus ≠ Sonnet ayni aile) karşılanmadi; esas/farkli-dogrulama baglaminda (bagimsiz kod, kimse aracin kodunu kullanmadi) kabul edildi. Karar kullanicinin.
2. Regresyon "19 ajan toplam token sapmasi" hangi anlik goruntu? ONKAYIT belirtmiyor. Anlik goruntu (hakem zamani) olarak okundu; tek mantikli okuma (hakem sayilari sabit, veri buyuyor). Canli veri okumasi icin RED olurdu; bu okuma ONKAYIT'in niyetiyle ("hakemin karsilastirmasi regresyon testi") celisir, uygulanmadi.
3. Ana test kapsami: `af755726` disarida (hakem goruntusunde var). Dahil edilirse n=11, sonuc ayni. n=10 tam sinirda; bir tane daha ajan bulunsaydi daha guvenli olurdu.
4. Resmi sayi = en son task-notification. a8b18801 gibi yeniden uyandirilan ajanlarda ara bildirimler (129-135k) son durumdan farklidir; yalniz sonuncu referans alindi. Ara bildirimlerle kiyaslamak anlamsiz.
5. a1272bcf'deki -%0,59 sapma aciklanamadi (resmi sayi 808 token fazla). Hakem raporundaki 4 ajanin −%0,05..−%0,23 sapmasiyla ayni sinif; esik icinde.
6. Zaman: ONKAYIT "2026-10-25 10:00 UTC sonrasi" -> UTC alindi (git zamanlari +03).

## KARAR: **KABUL**
Gerekce: ONKAYIT'in uc olculebilir kriteri de esigi gecti (ana test 10/10, maks %0,59 <= %2; regresyon %0,000 <= %0,5; etiketsiz pay %1,8 <= %10). Oldurme kosullari tetiklenmedi. Dikkat notlari: n sinirda, `diger` etiketi cop kutusu, denetci "aile" kosulu kati okunursa eksik.
