# Forge

Claude'un (ve ajanlarının) kullanacağı güçlü araçların yapıldığı, kanıtlandığı ve sisteme alındığı merkez. Tüm geliştirmeler burada toplanır.

## Felsefe
- **Pahalı model yalnız yargı yapar.** Tekrarlı işi kod ya da ucuz model yapar.
- **Araç bana özet verir, döküm vermez.** Bağlam pahalıdır.
- **Dürüst durum bilgisi verir.** "Bulunamadı" ile "aranamadı" ayrı şeylerdir. Sessiz veri kaybı yasaktır.
- **Kanıt doğrulanabilir olmalı.** Alıntılar kaynakta kodla kontrol edilir.
- **Kanıtlanmayan araç sisteme girmez.**

## Kabul protokolü (her araç için)
1. **Taban çizgisi:** aynı iş bugünkü yöntemle (ajan veya elle) yapılır; maliyeti ve kalitesi ölçülür.
2. **Eşik önceden yazılır:** kalite ve maliyet için sayısal kabul/ret kriteri. Sonuçtan sonra değiştirilemez.
3. **Bağımsız ölçüm:** aracı yazmayan bir denetçi ajan, altın set ya da bağımsız kontrol ile ölçer.
4. **Karar:**
   - **KABUL:** eşik geçildi → skill/ajan olarak sisteme bağlanır.
   - **ŞARTLI:** belli bir rolde işe yarıyor (ör. ön tarama); rolü açıkça yazılır.
   - **RED:** eşik geçilmedi → nedeni yazılıp arşive kaldırılır.
5. **Regresyon:** kabul edilen aracın kanıt testi kalıcıdır; her değişiklikten sonra yeniden koşulur.

## Yapı
- `KAYIT.md` — araç sicili: durum, kanıt, maliyet.
- `araclar/<ad>/` — her aracın kodu, `SPEC.md`, testleri ve `KANIT.md`'si.
- `kanit/` — ortak altın setler ve ölçüm verisi.
- `sistem/` — kabul edilen araçların skill ve ajan tanımları. Kurulum `~/.claude/` altına yapılır.
