"""Saf prompt vs Forge benchmark tablosu -> forge-benchmark.xlsx (değerler 2026-10-25 ölçümlerinden)."""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

F = Font(name="Arial", size=10)
FB = Font(name="Arial", size=10, bold=True)
FH = Font(name="Arial", size=10, bold=True, color="FFFFFF")
FI = Font(name="Arial", size=10, color="0000FF")  # ölçülmüş girdi
HF = PatternFill("solid", fgColor="2F4858")
BF = PatternFill("solid", fgColor="E3F0EC")
QF = PatternFill("solid", fgColor="FFF4D6")
th = Side(style="thin", color="B8C4C9")
BR = Border(top=th, bottom=th, left=th, right=th)
W = Alignment(wrap_text=True, vertical="top")

wb = Workbook()
ws = wb.active
ws.title = "Benchmark"
ws["A1"] = "Saf prompt vs Forge (B): süreç ölçümleri (2026-10-25)"
ws["A1"].font = Font(name="Arial", size=12, bold=True)
ws["A2"] = ("A0: deneyin 29 sorusu ortalaması · A1: D2 denemesi (1 soru) · B: deneyin ilk 4 sorusu ortalaması. "
            "Mavi = ölçülmüş değer; siyah = formül.")
ws["A2"].font = Font(name="Arial", size=9, italic=True)
for j, h in enumerate(["Ölçüt", "Saf prompt A0 (hafızadan)", "Saf prompt A1 (Opus aramalı)", "Forge B", "Not"], 1):
    c = ws.cell(row=4, column=j, value=h)
    c.font, c.fill, c.alignment, c.border = FH, HF, W, BR
rows = [
    ("Bakılan aday makale (havuz)", 0, None, 5110, "A0: hafızadan (29 koşuda toplam 28 web araması). A1: aday sayısı bilinmiyor. B: 4 sorunun ortalaması."),
    ("Okunan aday (B: Haiku okuyucu)", None, None, 1200, ""),
    ("Web araması (koşu başına)", 0.97, 33, None, "B: web işçileri + 6 akademik kaynak API'si."),
    ("Geçerli görünen kimlik (30'da)", 28, 26, 30, "A0/A1: yalnız biçim kontrolü, doğrulanmadı. B: veritabanında gerçek kayda çözüldü."),
    ("Kaynakta doğrulanmış alıntı (30'da)", 0, 0, 28, ""),
    ("Opus token (pahalı model)", 35230, 1027207, 15563, "B: D2 koşusu (plan + final). A1: D2 denemesi (giriş + önbellek + çıkış)."),
    ("Haiku token (ucuz model)", 0, 0, 1202631, "B: ilk 4 sorunun ortalaması (tüm aşamalar − Opus)."),
    ("Ağırlık (API liste fiyatı, $)", 0.169, 1.173, 0.637, "Abonelikte para çekilmez; limitten düşer."),
    ("Süre (saniye)", 65, 231, 1088, ""),
    ("Claude'a dönen rapor (token, tahmini)", 2763, 3033, 3766, "karakter / 3"),
    ("Sonuç kalitesi (recall@30)", "?", "?", "?", "Deney bitince dolacak (30 soru, ön kayıtlı)."),
]
for i, row in enumerate(rows):
    for j, v in enumerate(row, 1):
        c = ws.cell(row=5 + i, column=j, value=v)
        c.border, c.alignment = BR, W
        num = j in (2, 3, 4) and isinstance(v, (int, float))
        c.font = FB if j == 1 else (FI if num else F)
        if j == 4:
            c.fill = BF
        if num:
            c.number_format = "#,##0.00" if isinstance(v, float) else "#,##0"
rr = 5 + len(rows) + 1
ws.cell(row=rr, column=1, value="Oranlar (formül)").font = FB
for k, (lab, f, fmt) in enumerate([("B / A1 ağırlık", "=D12/C12", "0%"), ("A1 / B Opus token", "=C10/D10", '0.0"x"'),
                                    ("B / A0 süre", "=D13/B13", '0.0"x"'), ("B / A0 ağırlık", "=D12/B12", '0.0"x"')]):
    ws.cell(row=rr + 1 + k, column=1, value=lab).font = F
    c = ws.cell(row=rr + 1 + k, column=2, value=f)
    c.font, c.number_format = F, fmt
for col, wd in zip("ABCDE", (34, 22, 22, 16, 60)):
    ws.column_dimensions[col].width = wd

w2 = wb.create_sheet("Kanıtlanmamış")
w2["A1"] = "Henüz kanıtlanmamış iddialar"
w2["A1"].font = Font(name="Arial", size=12, bold=True)
for j, h in enumerate(["#", "İddia", "Neden henüz kanıt değil", "Nasıl kanıtlanacak", "Durum"], 1):
    c = w2.cell(row=3, column=j, value=h)
    c.font, c.fill, c.alignment, c.border = FH, HF, W, BR
items = [
    ("Forge daha doğru makaleleri buluyor (kalite)", "Hiç ölçülmedi; deney 4/30'da", "Fabrika bitince recall@30, 30 soru, işaret testi", "Fabrikada"),
    ("Forge'un fikirleri daha iyi", "Pilot sürüyor; 3 konu karar için az", "Pilot (yön) → kullanıcının kör hükmü → 30 konuluk deney", "Pilot sürüyor"),
    ("Ağırlıkta yarı yarıya ucuz", "Yalnız 1 soruluk A1 ölçümüne dayanıyor", "A1'in 30 sorusu", "Fabrikada sırada"),
    ("Opus token'ında ~65 kat fark", "B ve A1 Opus sayısı tek koşudan", "30 soruda aşama aşama token dökümü", "Fabrikada sırada"),
    ("A0 ve A1'in kimlikleri gerçek", "KISMEN ÖLÇÜLDÜ (2026-10-26): A0 arXiv kimliklerinin %98,3'ü doğru, 0 uydurma, 10/602 başka makaleye bağlı. DOI'ler kontrol edilmedi", "DOI'ler: Crossref (deney bitince)", "Kısmen"),
    ("Sonuçlar tekrarlanabilir", "Aynı soru hiç tekrar koşulmadı", "10 soru × 3 koşu, sapma", "Planlı"),
    ("Sadakat (gerekçe kaynakla tutarlı)", "Pilotta 10 iddia; bazı gerekçeler tautolojik", "n=30 denetim + tautoloji sayımı", "Planlı"),
    ("Sürdürülebilirlik (her iş öncekinden ucuz)", "Hiç ölçülmedi", "Tekrar kullanımda token düşüşü (yerel arXiv, önbellek)", "v1"),
    ("Gerçek değer ('kendi araçlarımla şunu yaptım')", "Forge'la yapılmış gerçek iş yok", "Bir fikri projeye / makaleye dönüştürmek", "Pilottan sonra"),
]
for i, it in enumerate(items):
    for j, v in enumerate((i + 1,) + it, 1):
        c = w2.cell(row=4 + i, column=j, value=v)
        c.font, c.alignment, c.border = (FB if j == 2 else F), W, BR
        if j == 5:
            c.fill = QF
r = 4 + len(items) + 1
w2.cell(row=r, column=2, value="Ölçülmüş ve sağlam:").font = FB
c = w2.cell(row=r, column=3, value="genişlik (bakılan makale), B kaynaklarının gerçek kayda çözülmesi, süre, şeffaflık (aşama sayımları)")
c.font, c.alignment = F, W
for col, wd in zip("ABCDE", (4, 36, 38, 44, 16)):
    w2.column_dimensions[col].width = wd

wb.save("forge-benchmark.xlsx")
print("ok")
