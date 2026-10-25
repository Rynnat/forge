# Moratoryum ve Pilot Önceliği (ön kayıt, 2026-10-25)

Kaynak: `gelistirme/YARGI.md` ŞİMDİ YAP madde 1. Kullanıcı onayıyla yürürlüğe girdi.

## Kural
- Yeni araç yazılmaz, mevcut araçlara özellik eklenmez.
- Tek istisna: `ONKAYIT-maliyet-sayaci.md`.
- Araç fikirleri yalnız `ISTEK-GUNLUGU.md` dosyasına birer satır olarak yazılır.

## Metrikler ve eşikler
- K5 hükmü (ELE / ARADA / DEVAM): **≤ 2026-10-29**.
- K8 için **≤ 2026-11-08**:
  - pilot hükmü,
  - 1 sayfalık pitch,
  - hocaya görüşme isteğinin gönderilmesi.
- Bu dönemde etiketli harcamada forge-meta payı **≤ %10**.
- Geri anlatma puanı (rubrik aşağıda):
  - K5'ten sonra **≥ 3/5**,
  - pitch'ten önce **≥ 4/5**.
- Öğrenci K8 tahminini pilottan **önce** commit eder.

## Gevşetme ve öldürme
- **Moratoryum gevşer:** bir pilot DEVAM çıkarsa ve 2 hafta içinde aynı elle iş istek günlüğünde ≥3 kez görülürse. Bu durumda yalnız o iş için araç ön kaydı açılır.
- **Araç fikri kalıcı olarak iptal edilir:** 4 hafta içinde 3 tekrara ulaşmazsa.
- **Moratoryum başarısız sayılır:** 11-08 kaçar VE forge-meta payı > %10 olursa. Bu durumda Forge DONDUR kuralı öne çekilir.
- **Geri anlatma kapısı:**
  - Ardışık iki geri anlatma ≤ 2/5 çıkarsa asistan yeni analiz kararı üretmeyi durdurur.
  - Kapı 2 kez atlanırsa Hedef 2 "ölçülmüyor" olarak yazılır.

## Geri anlatma rubriği
20 dakika, kapalı kitap. Her madde 1 puan, toplam 5.

1. Pilotun neyi ölçtüğünü kendi cümleleriyle doğru anlatıyor: metrikler ve gruplar.
2. Eşiklerin neden o değerde olduğunu, ne korumak için konduklarını açıklıyor.
3. Sonucun hangi durumda yanlış olabileceğine dair en az 2 geçerli tehdit sayıyor: örneklem, ölçüm, karıştırıcı.
4. Bir hakem sorusunu doğru cevaplıyor (asistan sorar).
5. İkinci hakem sorusunu doğru cevaplıyor ve en yakın çalışmadan farkı söylüyor.

**Puanlama kuralları:**
- Asistan her maddeye 0 ya da 1 verir ve gerekçesini yazar.
- Kısmi cevap 0'dır.
- Puan, tarih ve geri bildirim `OGRENME-GUNLUGU.md`'ye eklenir.
