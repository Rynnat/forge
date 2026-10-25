# Forge Ölüm Kriteri — v3 (orkestra kapsamı, 2026-10-25)

## Değişiklik kaydı
v2 (aynı gün, commit 74e36a9) dar kapsamla yazılmıştı: "Forge araştırma projesine hizmet etsin". Hoca ve pilot maddeleri kullanıcıyı ölçüyordu, Forge'u değil. Kullanıcı kapsamı düzeltti: Forge bir orkestradır.

v2'nin kendi kuralı "değişirse otomatik DONDUR" diyordu. Bu kural dürüstçe uygulandı:
- **Dar kapsamlı Forge v2 DONDURULDU.**
- Forge v3, aşağıdaki yeni kriterle başlıyor.
- Hoca ve pilot maddeleri `akademik-bosluk/YOL.md`'ye taşındı.

**Bu dosya (v3) bu tarihten sonra değiştirilirse Forge yine otomatik DONDUR'a geçer.**

## 2026-11-22'de ölçülür
- **K1 — Deney:** `ONKAYIT-orkestra-v0.md` deneyi n=30 ile koşulmuş ve KABUL ya da RED almış.
- **K2 — Değer:** deney KABUL aldıysa, orkestra en az 2 farklı projede gerçek işte kullanılmış.
- **K3 — Maliyet disiplini:** forge-meta harcaması (orkestranın inşası ve denetimi), orkestranın gerçek işlerde kullanılmasından kaynaklanan harcamanın 3 katını aşmıyor. Ölçüm maliyet-sayaci etiketleriyle yapılır.

## Hüküm
- K1 tutmazsa → **DONDUR**: deney yapılmadan büyütme yok.
- K1 = RED ise → orkestra v0 ARŞİV olur. Forge, dersleriyle birlikte tek bir v1 denemesi hakkı kazanır. O da RED alırsa Forge ÖLÜR.
- K1 = KABUL olduğu hâlde K2 ya da K3 tutmazsa → **DONDUR** (araç kullanılmıyor ya da pahalı).

## 2026-12-24'te ölçülür
- Orkestra, gerçek işte ≥10 kez çağrılmış ve maliyet-sayaci'ye göre ortalama maliyeti taban çizgisinin ≤ %50'si.
- Tutmazsa → **DONDUR**.
